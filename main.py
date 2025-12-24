import os
import sys
import shutil
import tempfile
import uuid
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add AI_ML/src to path so we can import VideoEditorAI
AI_SRC_PATH = os.path.join(os.getcwd(), "AI_ML", "src")
sys.path.append(AI_SRC_PATH)

# Import existing AI components
try:
    from VideoEditorAI.pipeline import VideoAnalysisPipeline
    from VideoEditorAI.chat.llm import EditingAssistant
    
    print("Initializing Global AI Pipeline (this may take a moment)...")
    global_pipeline = VideoAnalysisPipeline()
    global_assistant = EditingAssistant()
    print("Global AI Pipeline ready.")
except ImportError as e:
    print(f"Error importing AI components: {e}")
    print(f"Check if {AI_SRC_PATH} exists and contains VideoEditorAI")
    global_pipeline = None
    global_assistant = None

app = FastAPI(title="AI Video Editing Assistant Backend")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"], # Common Vite/React ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models for Requests ---

class ChatRequest(BaseModel):
    message: str
    analysis_summary: Optional[dict] = None
    selected_app: Optional[str] = None
    is_sharing: bool = False

# --- Helper for Language Mapping ---
LANGUAGE_MAP = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "hi": "Hindi",
    "ar": "Arabic",
    # Add more as needed
}

def get_language_name(code: str) -> str:
    return LANGUAGE_MAP.get(code.lower(), code.capitalize())

# --- Endpoints ---

@app.get("/")
async def root():
    return {"message": "AI Video Editing Assistant Backend is running!"}

@app.post("/analyze")
async def analyze_video(video: UploadFile = File(...)):
    """
    Receive a video file, save it temporarily, run AI analysis, and return results.
    """
    # Create a unique temp file path
    temp_dir = tempfile.gettempdir()
    file_extension = os.path.splitext(video.filename)[1]
    temp_video_path = os.path.join(temp_dir, f"{uuid.uuid4()}{file_extension}")

    try:
        # Save the uploaded file
        total_size = 0
        with open(temp_video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
            total_size = os.path.getsize(temp_video_path)
            
        print(f"\n[DEBUG] --- NEW ANALYSIS REQUEST ---")
        print(f"[DEBUG] Original File: {video.filename}")
        print(f"[DEBUG] Temp File: {temp_video_path} (Size: {total_size} bytes)")

        # Run Analysis using Global Pipeline
        if global_pipeline is None:
            raise HTTPException(status_code=500, detail="AI Pipeline failed to initialize. Check server logs.")
            
        result = global_pipeline.analyze_video(temp_video_path)

        print(f"[DEBUG] Analysis complete. Detected Language: {result.language}")
        print(f"[DEBUG] Suggestions: {len(result.suggestions)}")

        # Build response with a unique ID and Timestamp to verify freshness
        import time
        analysis_id = str(uuid.uuid4())[:8]
        timestamp = time.strftime("%H:%M:%S")

        response = {
            "analysis_id": analysis_id,
            "timestamp": timestamp,
            "summary": {
                "detected_language": get_language_name(result.language),
                "duration": result.duration,
                "total_silences": len(result.silence_segments),
                "total_highlights": sum(1 for s in result.suggestions if s.suggestion_type.value == "highlight"),
                "total_suggestions": len(result.suggestions)
            },
            "suggestions": [s.to_dict() for s in result.suggestions]
        }
        
        print(f"[DEBUG] Returning Analysis ID: {analysis_id} at {timestamp}")
        return response

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Receive user message and optional analysis summary, return Gemini assistant response.
    """
    try:
        if global_assistant is None:
            raise HTTPException(status_code=500, detail="Gemini Assistant failed to initialize. Check API key.")
            
        # Convert analysis_summary to string context if provided
        context = ""
        if request.analysis_summary:
            import json
            context = json.dumps(request.analysis_summary)

        reply = global_assistant.chat(
            request.message, 
            context, 
            selected_app=request.selected_app, 
            is_sharing=request.is_sharing
        )
        return {"reply": reply}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
