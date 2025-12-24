import sys
import os
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from VideoEditorAI.pipeline import VideoAnalysisPipeline
from VideoEditorAI.core.models import VideoSegment
from VideoEditorAI.core.config import settings

def run_mock_verification():
    print("=== MOCK VERIFICATION MODE ===")
    
    # Mocking external heavy libraries to test logic flow
    pipeline = VideoAnalysisPipeline()
    
    print("1. Mocking Audio Extraction...")
    pipeline.audio_processor.extract_audio = MagicMock(return_value="dummy_audio.wav")
    
    print("2. Mocking Silence Detection...")
    # Simulate a silence from 10s to 15s
    pipeline.audio_processor.detect_silence = MagicMock(return_value=[(10.0, 15.0)])
    
    print("3. Mocking Transcription...")
    # Simulate some segments
    pipeline.transcriber.transcribe = MagicMock(return_value=[
        {"start": 0.0, "end": 5.0, "text": "Hello welcome to the video."},
        {"start": 5.0, "end": 10.0, "text": "This is a test segment."},
        {"start": 15.0, "end": 20.0, "text": "This is a test segment."}, # Redundant
        {"start": 20.0, "end": 25.0, "text": "Don't forget to subscribe! Key takeaway here."}
    ])
    
    print("4. Mocking duration...")
    # We can't easily mock mp.VideoFileClip inside the method without patching the module,
    # but we can assume the pipeline handles the exception or we pass a dummy file that exists?
    # Let's just create a dummy file so os.path.exists passes
    with open("dummy_video.mp4", "w") as f:
        f.write("test")
        
    # We rely on the pipeline to handle the clip loading failure or we mock it if possible.
    # For now, let's see if the logic flow (Rule Engine) works.
    
    print("5. Running Analysis...")
    try:
        result = pipeline.analyze_video("dummy_video.mp4")
        
        print("\n--- Result Validation ---")
        cuts = [s for s in result.suggestions if s.suggestion_type == "cut"]
        highlights = [s for s in result.suggestions if s.suggestion_type == "highlight"]
        
        print(f"Reflected Suggestions: {len(result.suggestions)}")
        print(f"Cuts: {len(cuts)}")
        print(f"Highlights: {len(highlights)}")
        
        # Expectation:
        # 1 Cut for silence (10-15s)
        # 1 Cut for redundancy (15-20s is same as 5-10s)
        # 1 Highlight for 'Key takeaway' (20-25s)
        
        # Note: Redundancy detection uses the real SemanticAnalyzer unless we mock that too.
        # But SemanticAnalyzer needs real model weights which takes time.
        # Ideally we permit it to run if installed, but for pure logic test we might default to 
        # mocking the embedding generation to return identical vectors for identical text.
        
    except Exception as e:
        print(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if os.path.exists("dummy_video.mp4"):
            os.remove("dummy_video.mp4")

if __name__ == "__main__":
    run_mock_verification()
