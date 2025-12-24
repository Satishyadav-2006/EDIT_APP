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
except ImportError as e:
    print(f"Error importing AI components: {e}")
    print(f"Check if {AI_SRC_PATH} exists and contains VideoEditorAI")
    # We'll handle this in the endpoints if imports failed

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
        with open(temp_video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        # Run Analysis
        pipeline = VideoAnalysisPipeline()
        result = pipeline.analyze_video(temp_video_path)

        # The result is an AnalysisResult object, we need to convert to JSON-serializable dict
        # Based on pipeline.py, it likely has a to_json() method or can be converted
        # In main.py:37, we saw: print(json.dumps(result.to_json(), indent=4))
        
        analysis_data = result.to_json()

        # Simplify for the requested frontend format
        # {
        #   "summary": { "detected_language": "string", "total_silences": number, ... },
        #   "suggestions": [ ... ]
        # }
        
        response = {
            "summary": {
                "detected_language": analysis_data.get("language", "unknown"),
                "total_silences": len(analysis_data.get("silence_segments", [])),
                "total_highlights": sum(1 for s in analysis_data.get("suggestions", []) if s.get("type", "").lower() == "highlight"),
                "total_suggestions": len(analysis_data.get("suggestions", []))
            },
            "suggestions": analysis_data.get("suggestions", [])
        }

        return response

    except Exception as e:
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
        assistant = EditingAssistant()
        
        # Convert analysis_summary to string context if provided
        context = ""
        if request.analysis_summary:
            import json
            context = json.dumps(request.analysis_summary)

        reply = assistant.chat(request.message, context)
        return {"reply": reply}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
