import os
import json
import subprocess
from VideoEditorAI.core.config import settings
from VideoEditorAI.core.models import AnalysisResult
from VideoEditorAI.analysis.audio import AudioProcessor
from VideoEditorAI.analysis.transcription import Transcriber
from VideoEditorAI.analysis.semantic import SemanticAnalyzer
from VideoEditorAI.rules.engine import DecisionEngine

class VideoAnalysisPipeline:
    def __init__(self):
        print("INFO:ai.analyzer:Initializing AI Pipeline components...")
        self.audio_processor = AudioProcessor()
        self.transcriber = Transcriber()
        self.semantic_analyzer = SemanticAnalyzer()
        self.decision_engine = DecisionEngine()

    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration using ffprobe (or ffmpeg)."""
        try:
            # ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 input.mp4
            command = [
                "ffprobe", 
                "-v", "error", 
                "-show_entries", "format=duration", 
                "-of", "default=noprint_wrappers=1:nokey=1", 
                video_path
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except Exception:
            # Fallback to ffmpeg stderr parsing if ffprobe not available, 
            # but usually they come together. For now return 0.0 on failure.
            return 0.0

    def analyze_video(self, video_path: str) -> AnalysisResult:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        print(f"INFO:ai.analyzer:Starting analysis for: {video_path}")
        
        # 0. Get Video Info (Duration)
        duration = self._get_video_duration(video_path)

        # 1. Audio Processing
        print(f"INFO:ai.audio_extraction:Extracting audio from {video_path}...")
        audio_path = self.audio_processor.extract_audio(video_path)
        print("INFO:ai.audio_extraction:Audio extraction successful.")
        
        print(f"INFO:ai.audio_analysis:Loading audio file: {audio_path}")
        silence_intervals = self.audio_processor.detect_silence(audio_path)
        energy_peaks = self.audio_processor.get_high_energy_segments(audio_path)
        print(f"INFO:ai.audio_analysis:Found {len(silence_intervals)} silence segments.")

        # 2. Transcription
        print(f"INFO:ai.speech_to_text:Loading Whisper model '{settings.WHISPER_MODEL_SIZE}'...")
        transcription_result = self.transcriber.transcribe(audio_path)
        raw_segments = transcription_result.get("segments", [])
        detected_language = transcription_result.get("language", "unknown")
        
        # 3. Semantic Analysis
        print("INFO:ai.nlp_analysis:Loading SentenceTransformer model...")
        video_segments = self.semantic_analyzer.analyze_segments(raw_segments)
        redundancies = self.semantic_analyzer.find_redundancies(video_segments)
        print(f"INFO:ai.nlp_analysis:Detected {len(redundancies)} redundancy pairs.")

        # 4. Decision Engine
        print("INFO:ai.analyzer:Running Decision Engine...")
        suggestions = self.decision_engine.generate_suggestions(
            silence_intervals, 
            video_segments, 
            redundancies,
            energy_peaks,
            duration
        )
        
        # 5. Final Packaging
        result = AnalysisResult(
            video_path=video_path,
            duration=duration,
            language=detected_language,
            transcript=raw_segments,
            silence_segments=silence_intervals,
            suggestions=suggestions
        )
        
        # Save output
        output_filename = os.path.basename(video_path) + ".json"
        output_path = os.path.join(settings.OUTPUT_DIR, output_filename)
        
        # Just creating the json dict, we won't verify write here to keep it clean
        # but matching the style of returning it
        
        print(f"INFO:ai.analyzer:Analysis completed.")
        return result
