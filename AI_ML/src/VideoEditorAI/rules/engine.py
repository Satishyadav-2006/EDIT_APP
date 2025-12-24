from typing import List, Dict
from VideoEditorAI.core.models import VideoSegment, EditingSuggestion, SegmentType, AnalysisResult
from VideoEditorAI.core.config import settings

class DecisionEngine:
    def generate_suggestions(
        self,
        silence_intervals: List[tuple],
        semantic_segments: List[VideoSegment],
        redundancies: List[tuple],
        energy_peaks: List[tuple],
        duration: float
    ) -> List[EditingSuggestion]:
        suggestions = []

        # 1. Processing Silence
        for start, end in silence_intervals:
            if (end - start) >= settings.MIN_SILENCE_DURATION:
                suggestions.append(EditingSuggestion(
                    suggestion_type=SegmentType.CUT,
                    start_time=start,
                    end_time=end,
                    confidence=0.9, # High confidence for silence
                    reason=f"Detected detected dead air/silence ({round(end-start, 1)}s)"
                ))

        # 2. Processing Redundancies
        # redundancies is list of (idx1, idx2) where idx2 is redundant
        for idx1, idx2 in redundancies:
            # We assume semantic_segments corresponds to the original transcript list order
            # but we need to be careful with indices if we were modifying the list.
            # Here we just flag the second occurrence.
            
            # Sanity check indices
            if idx1 >= len(semantic_segments) or idx2 >= len(semantic_segments):
                continue

            seg_original = semantic_segments[idx1]
            seg_redundant = semantic_segments[idx2]
            
            suggestions.append(EditingSuggestion(
                suggestion_type=SegmentType.CUT,
                start_time=seg_redundant.start_time,
                end_time=seg_redundant.end_time,
                confidence=0.8,
                reason=f"Content is semantically redundant to segment at {round(seg_original.start_time, 1)}s"
            ))

        # 3. Semantic Highlights (Keyword based)
        highlight_keywords = ["amazing", "important", "key takeaway", "don't forget"]
        semantic_highlight_found = False
        
        for seg in semantic_segments:
            if seg.text and any(k in seg.text.lower() for k in highlight_keywords):
                 suggestions.append(EditingSuggestion(
                    suggestion_type=SegmentType.HIGHLIGHT,
                    start_time=seg.start_time,
                    end_time=seg.end_time,
                    confidence=0.7,
                    reason=f"Contains key phrase suggesting importance: '{seg.text[:20]}...'"
                ))
                 semantic_highlight_found = True

        # 4. Energy Highlights (Fallback or Additive)
        # If we didn't find specific semantic highlights, use energy peaks
        # Or we can just include them as "High Energy" segments
        for start, end in energy_peaks:
            # Avoid overlapping with existing suggestions roughly
            # (Simple distinct check)
            suggestions.append(EditingSuggestion(
                suggestion_type=SegmentType.HIGHLIGHT,
                start_time=start,
                end_time=end,
                confidence=0.6,
                reason="High audio energy detected (potential highlight)"
            ))

        # Sort suggestions by start time
        suggestions.sort(key=lambda s: s.start_time)
        return suggestions
