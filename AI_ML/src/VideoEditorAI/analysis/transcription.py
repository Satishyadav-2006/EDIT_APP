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
        print(f"[DEBUG] Transcribing audio from: {audio_path}")
        
        # verbose=False to suppress default whisper printing
        # fp16=False to supress CPU warning
        # beam_size=1 for maximum speed (greedy decoding)
        result = self.model.transcribe(audio_path, verbose=False, fp16=False, beam_size=1)
        
        # Access language if available (Whisper usually determines this early)
        language = result.get("language", "unknown")
        
        # --- Heuristic to prevent false 'Japanese' (ja) detection ---
        # Whisper often hallucinations 'ja' on short noise or silence.
        # If 'ja' is detected, verify if there are actually CJK characters.
        if language == "ja":
            text_content = result.get("text", "").strip()
            # Simple check for CJK characters: 
            # Japanese range includes Hiragana, Katakana, and Kanji.
            # If none found, default to 'en' as it's likely a placeholder.
            has_japanese = any('\u3040' <= char <= '\u30ff' or '\u4e00' <= char <= '\u9fff' for char in text_content)
            # If 'ja' but NO japanese characters, or very short text that usually signifies noise/hallucination
            if not has_japanese:
                print(f"[DEBUG] False Japanese detection suspected (language 'ja' but no CJK chars). Reverting to 'en'.")
                language = "en"
                result["language"] = "en"

        print(f"Detected language: {language}")
        
        print("INFO:ai.speech_to_text:Transcription complete.")
        return result
