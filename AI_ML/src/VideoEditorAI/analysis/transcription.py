import whisper
from typing import List, Dict, Any
from VideoEditorAI.core.config import settings

class Transcriber:
    def __init__(self):
        print(f"Loading Whisper model ({settings.WHISPER_MODEL_SIZE})...")
        self.model = whisper.load_model(settings.WHISPER_MODEL_SIZE)

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribes audio to text with timestamps.
        Returns the full result dictionary including 'segments' and 'language'.
        """
        print(f"INFO:ai.speech_to_text:Transcribing {audio_path}...")
        
        # verbose=False to suppress default whisper printing
        # fp16=False to supress CPU warning
        result = self.model.transcribe(audio_path, verbose=False, fp16=False)
        
        # Access language if available (Whisper usually determines this early)
        language = result.get("language", "unknown")
        print(f"Detected language: {language}")
        
        print("INFO:ai.speech_to_text:Transcription complete.")
        return result
