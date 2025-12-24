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
                    reason=f"Found a quiet part/silence ({round(end-start, 1)}s)"
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
                reason=f"You're repeating yourself (similar to what you said at {round(seg_original.start_time, 1)}s)"
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
                    reason=f"Important word mentioned: '{seg.text[:20]}...'"
                ))
                 semantic_highlight_found = True

        # 4. Energy Highlights (Fallback or Additive)
        # If we didn't find specific semantic highlights, use energy peaks
        # Or we can just include them as "High Energy" segments
        for start, end in energy_peaks:
            # Check for overlaps with existing suggestions
            is_redundant = False
            for existing in suggestions:
                # If they overlap more than 50%, or if the start/end is within another
                ov_start = max(start, existing.start_time)
                ov_end = min(end, existing.end_time)
                if ov_start < ov_end:
                    overlap_duration = ov_end - ov_start
                    if overlap_duration > 1.0: # If they overlap by more than 1 second
                        is_redundant = True
                        break
            
            if not is_redundant:
                # NEW: Try to find semantic context for this energy peak
                context_text = ""
                for seg in semantic_segments:
                    # Check for overlap
                    ov_start = max(start, seg.start_time)
                    ov_end = min(end, seg.end_time)
                    if ov_start < ov_end:
                        context_text = seg.text
                        break
                
                reason = "You talked louder here (potential highlight)"
                if context_text:
                    reason = f"Captured an important moment: \"{context_text[:50]}...\""

                suggestions.append(EditingSuggestion(
                    suggestion_type=SegmentType.HIGHLIGHT,
                    start_time=start,
                    end_time=end,
                    confidence=0.6,
                    reason=reason
                ))

        # Sort suggestions by start time
        suggestions.sort(key=lambda s: s.start_time)
        
        # Final pass: Ensure no two suggestions start at the exact same time
        unique_suggestions = []
        seen_starts = set()
        for s in suggestions:
            # Use rounded start time for identification
            rounded_start = round(s.start_time, 1)
            if rounded_start not in seen_starts:
                unique_suggestions.append(s)
                seen_starts.add(rounded_start)
        
        # Add transition suggestions between far highlights
        final_suggestions = list(unique_suggestions)
        for i in range(len(unique_suggestions) - 1):
            curr = unique_suggestions[i]
            nxt = unique_suggestions[i+1]
            gap = nxt.start_time - curr.end_time
            if gap > 2.0: # If there's more than 2s gap between suggestions
                final_suggestions.append(EditingSuggestion(
                    suggestion_type=SegmentType.TRANSITION,
                    start_time=curr.end_time - 0.5,
                    end_time=curr.end_time + 0.5,
                    confidence=0.5,
                    reason="Add a smooth transition (like a fade) between these parts"
                ))
            elif curr.suggestion_type == SegmentType.CUT:
                 final_suggestions.append(EditingSuggestion(
                    suggestion_type=SegmentType.TRANSITION,
                    start_time=curr.start_time,
                    end_time=curr.start_time + 0.1,
                    confidence=0.4,
                    reason="Try a quick 'Jump Cut' here"
                ))

        final_suggestions.sort(key=lambda s: s.start_time)
        return final_suggestions
