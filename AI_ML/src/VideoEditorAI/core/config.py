import os
from dataclasses import dataclass

@dataclass
class Config:
    # Audio Analysis
    SILENCE_THRESHOLD_DB: int = -40
    MIN_SILENCE_DURATION: float = 0.5  # seconds
    
    # NLP / Semantic
    WHISPER_MODEL_SIZE: str = "base"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    SIMILARITY_THRESHOLD: float = 0.85  # For detecting redundancy
    
    # Heuristics
    MIN_SEGMENT_DURATION: float = 1.0
    CONFIDENCE_THRESHOLD: float = 0.6
    
    # LLM
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-flash-latest"
    
    # System
    TEMP_DIR: str = os.path.join(os.getcwd(), "temp")
    OUTPUT_DIR: str = os.path.join(os.getcwd(), "output")

    def __post_init__(self):
        os.makedirs(self.TEMP_DIR, exist_ok=True)
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)

# Global config instance
settings = Config()
