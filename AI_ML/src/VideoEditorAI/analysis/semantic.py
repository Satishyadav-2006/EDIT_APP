from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Dict, Any
from VideoEditorAI.core.config import settings
from VideoEditorAI.core.models import VideoSegment

class SemanticAnalyzer:
    def __init__(self):
        print(f"Loading Sentence Transformer ({settings.EMBEDDING_MODEL})...")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)

    def analyze_segments(self, segments: List[Dict[str, Any]]) -> List[VideoSegment]:
        """
        Enriches transcript segments with embeddings and detects redundancies.
        Returns a list of VideoSegment objects.
        """
        if not segments:
            return []

        texts = [s["text"].strip() for s in segments]
        embeddings = self.model.encode(texts)
        
        video_segments = []
        for i, s in enumerate(segments):
            seg = VideoSegment(
                start_time=s["start"],
                end_time=s["end"],
                text=s["text"],
                semantic_embedding=embeddings[i]
            )
            video_segments.append(seg)
            
        return video_segments

    def find_redundancies(self, video_segments: List[VideoSegment]) -> List[tuple]:
        """
        Finds pairs of segments that are semantically similar.
        Returns list of (index1, index2) where index2 is redundant to index1.
        """
        redundancies = []
        n = len(video_segments)
        if n < 2:
            return redundancies

        embeddings = np.array([s.semantic_embedding for s in video_segments])
        sim_matrix = cosine_similarity(embeddings)
        
        # Check upper triangle
        for i in range(n):
            for j in range(i + 1, n):
                if sim_matrix[i][j] > settings.SIMILARITY_THRESHOLD:
                    # Mark the shorter or later one as potential redundancy
                    redundancies.append((i, j))
                    
        return redundancies
