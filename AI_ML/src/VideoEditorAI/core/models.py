from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

class SegmentType(str, Enum):
    CUT = "cut"
    HIGHLIGHT = "highlight"
    KEEP = "keep"

@dataclass
class VideoSegment:
    """Represents a time range in the video with associated metadata."""
    start_time: float
    end_time: float
    text: Optional[str] = None
    audio_energy: float = 0.0
    is_silent: bool = False
    semantic_embedding: Any = None  # numpy array, valid type Any for simplicity here

@dataclass
class EditingSuggestion:
    """A concrete suggestion for an edit."""
    suggestion_type: SegmentType
    start_time: float
    end_time: float
    confidence: float
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.suggestion_type.value,
            "start": round(float(self.start_time), 2),
            "end": round(float(self.end_time), 2),
            "confidence": round(float(self.confidence), 2),
            "reason": self.reason
        }

@dataclass
class AnalysisResult:
    """Container for all analysis data and final suggestions."""
    video_path: str
    duration: float
    language: str
    transcript: List[Dict[str, Any]]
    silence_segments: List[tuple]
    suggestions: List[EditingSuggestion]

    def to_json(self) -> Dict[str, Any]:
        return {
            "summary": {
                "detected_language": self.language,
                "total_silences": len(self.silence_segments),
                "total_highlights": len([s for s in self.suggestions if s.suggestion_type == SegmentType.HIGHLIGHT]),
                "total_suggestions": len(self.suggestions)
            },
            "suggestions": [s.to_dict() for s in self.suggestions]
        }
