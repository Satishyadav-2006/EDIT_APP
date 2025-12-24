import argparse
import sys
import os

# Ensure src is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), "VideoEditorAI"))

from VideoEditorAI.pipeline import VideoAnalysisPipeline
from VideoEditorAI.chat.llm import EditingAssistant

def main():
    parser = argparse.ArgumentParser(description="AI Video Editing Assistant")
    parser.add_argument("--video", type=str, required=True, help="Path to the input video file")
    parser.add_argument("--chat", action="store_true", help="Enable chat mode after analysis")
    
    args = parser.parse_args()
    
    video_path = args.video
    if not os.path.exists(video_path):
        print(f"Error: File {video_path} does not exist.")
        return

    # 1. Run Analysis
    print(f"\n=== Processing {video_path} ===\n")
    pipeline = VideoAnalysisPipeline()
    try:
        result = pipeline.analyze_video(video_path)
    except Exception as e:
        print(f"\nCRITICAL ERROR during analysis: {e}")
        return

    # 2. Display Result (Matching Screenshot)
    print("\n==================================")
    print("ANALYSIS RESULT")
    print("==================================")
    import json
    print(json.dumps(result.to_json(), indent=4))

    # 3. Chat Mode
    if args.chat:
        print("\n=== Chat Mode (Local LLM) ===")
        print("Type 'exit' to quit. Ask about the editing suggestions or general questions.")
        
        assistant = EditingAssistant()
        
        # Create a natural language summary for the TinyLlama model
        # (It struggles with raw JSON, so we feed it sentences)
        context = f"Video Language: {result.language}\n"
        context += f"Total Duration: {result.duration} seconds.\n"
        context += "Analysis Findings:\n"
        if result.suggestions:
            for s in result.suggestions:
                context += f"- A {s.suggestion_type.value} is suggested from {s.start_time}s to {s.end_time}s. Reason: {s.reason}\n"
        else:
            context += "- No specific edits suggested.\n"
        
        while True:
            try:
                user_input = input("\nYou: ")
                if user_input.lower() in ["exit", "quit", "q"]:
                    break
                
                print("Assistant: [Thinking...]")
                response = assistant.chat(user_input, context)
                print(f"Assistant: {response}")
                
                # Context is passed only once or strictly managed? 
                # For simplicity, we keep passing the same analysis context + session history if we wanted 
                # (but here we just pass static context)
                
            except KeyboardInterrupt:
                break
        print("\nExiting chat.")

if __name__ == "__main__":
    main()
