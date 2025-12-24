import os
import subprocess
from typing import List
import numpy as np
import librosa
from VideoEditorAI.core.config import settings

class AudioProcessor:
    def __init__(self):
        self.sample_rate = 22050

    def extract_audio(self, video_path: str) -> str:
        """Extracts audio from video functionality using ffmpeg."""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        base_name = os.path.basename(video_path)
        audio_filename = f"{os.path.splitext(base_name)[0]}.wav"
        output_path = os.path.join(settings.TEMP_DIR, audio_filename)
        
        # Overwrite if exists
        if os.path.exists(output_path):
            os.remove(output_path)

        # Conceptual command: ffmpeg -i input.mp4 -vn -acodec pcm_s16le -ar 44100 -ac 2 output.wav
        # Using subprocess to call ffmpeg (assuming ffmpeg is in PATH)
        command = [
            "ffmpeg", "-i", video_path,
            "-vn", # No video
            "-acodec", "pcm_s16le", # WAV codec
            "-ar", "22050", # Sample rate
            "-ac", "1", # Mono for analysis is usually fine
            "-y", # Overwrite
            "-loglevel", "error",
            output_path
        ]
        
        print(f"Extracting audio to {output_path}...")
        subprocess.run(command, check=True)
        return output_path

    def detect_silence(self, audio_path: str):
        """
        Detects silent segments in the audio file.
        Returns a list of (start_time, end_time) tuples.
        """
        print("Loading audio for silence detection...")
        y, sr = librosa.load(audio_path, sr=self.sample_rate)
        
        # Compute RMS energy
        rms = librosa.feature.rms(y=y)[0]
        
        # Convert dB threshold to linear amplitude
        # db = 20 * log10(amp) -> amp = 10^(db/20)
        # Note: librosa.feature.rms results are linear, but often normalized.
        # Let's compute dB relative to max
        db = librosa.amplitude_to_db(rms, ref=np.max)
        
        # Identify silent frames
        is_silent = db < settings.SILENCE_THRESHOLD_DB
        
        # Convert frames to time
        silent_intervals = []
        current_start = None
        
        frames_to_time = librosa.frames_to_time(np.arange(len(db)), sr=sr)
        
        for i, silent in enumerate(is_silent):
            t = frames_to_time[i]
            if silent:
                if current_start is None:
                    current_start = t
            else:
                if current_start is not None:
                    duration = t - current_start
                    if duration >= settings.MIN_SILENCE_DURATION:
                        silent_intervals.append((current_start, t))
                    current_start = None
        
        # Handle case where file ends in silence
        if current_start is not None:
            t_end = frames_to_time[-1]
            if (t_end - current_start) >= settings.MIN_SILENCE_DURATION:
                silent_intervals.append((current_start, t_end))
        
        return silent_intervals

    def get_high_energy_segments(self, audio_path: str, top_n: int = 2) -> List[tuple]:
        """
        Identify top N high-energy segments (approx 5s long).
        Returns list of (start, end) tuples.
        """
        y, sr = librosa.load(audio_path, sr=self.sample_rate)
        rms = librosa.feature.rms(y=y)[0]
        frames_to_time = librosa.frames_to_time(np.arange(len(rms)), sr=sr)
        
        # Smooth the signal to find sustained peaks, not just transient clicks
        # Simple moving average
        window_size = int(sr * 1.0 / 512) # ~1 sec window if hop_length is 512 (default for rms)
        # Actually librosa rms hop is 512 by default
        
        # Just find the frame with max energy, take +/- 2.5 seconds
        # To get multiple, we can zero out the region and search again
        
        peaks = []
        rms_cp = rms.copy()
        duration = librosa.get_duration(y=y, sr=sr)
        
        for _ in range(top_n):
            max_idx = np.argmax(rms_cp)
            max_time = frames_to_time[max_idx]
            
            # Define window around peak
            start = max(0, max_time - 2.5)
            end = min(duration, max_time + 2.5)
            
            peaks.append((start, end))
            
            # Zero out this region in rms_copy to find next distinct peak
            # Convert time back to frames
            start_frame = librosa.time_to_frames(start, sr=sr)
            end_frame = librosa.time_to_frames(end, sr=sr)
            rms_cp[start_frame:end_frame] = 0
            
        peaks.sort()
        return peaks
