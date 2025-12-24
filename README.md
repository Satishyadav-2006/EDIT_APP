# AI Video Editing Assistant - Backend

This backend connects the React (Vite) frontend with the AI analysis pipeline and Gemini chat assistant.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Gemini API Key**:
   Ensure you have your Gemini API key set in your environment variables:
   ```bash
   # Windows
   $env:GEMINI_API_KEY = "your-api-key"
   ```

## Running the Backend

Run the server using `uvicorn`:
```bash
uvicorn main:app --reload
```
The server will start at `http://localhost:8000`.

## API Endpoints

### 1. POST `/analyze`
- **Purpose**: Upload a video for AI analysis.
- **Request**: `multipart/form-data` with a `video` file.
- **Example**:
  ```bash
  curl -X POST "http://localhost:8000/analyze" -F "video=@my_video.mp4"
  ```

### 2. POST `/chat`
- **Purpose**: Chat with the AI assistant about the video or editing.
- **Request**: JSON with `message` and optional `analysis_summary`.
- **Example**:
  ```bash
  curl -X POST "http://localhost:8000/chat" -H "Content-Type: application/json" -d "{\"message\": \"hi\"}"
  ```

## Integration Details
- **Frontend**: Connects to `http://localhost:8000`.
- **AI Pipeline**: Uses the `VideoAnalysisPipeline` class from `AI_ML/src`.
- **Chat**: Uses the `EditingAssistant` class from `AI_ML/src`.
