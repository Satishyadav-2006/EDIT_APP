from google import genai
from google.genai import types
from VideoEditorAI.core.config import settings


class EditingAssistant:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing in configuration. Please set the environment variable.")
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_MODEL

    def _generate(self, prompt: str, system_instruction: str = None) -> str:
        """Safe, bounded generation call to Gemini."""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                    max_output_tokens=1024,
                    safety_settings=[
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE,
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE,
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE,
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE,
                        ),
                    ]
                )
            )
            
            if response and response.text:
                return response.text.strip()
            
            return "The assistant was unable to generate a detailed response. Please try rephrasing your editing question."

        except Exception as e:
            # Handle specific SDK errors gracefully
            error_msg = str(e)
            if "strip" in error_msg:
                return "The assistant produced an empty response due to context limits or safety filtering. Try a shorter question."
            return f"Error communicating with Gemini: {error_msg}"

    def chat(self, user_query: str, analysis_summary: str = None, selected_app: str = None, is_sharing: bool = False) -> str:
        """Main chat interface for explaining video analysis results."""
        if user_query.strip().lower() in ["hi", "hello", "hii"]:
            return "Hello! I'm your AI video editing assistant. I've analyzed your video—ask me about cuts, highlights, or how to implement the suggested edits!"

        app_context = f"The user is using {selected_app}." if selected_app else "The user has not selected a specific editing app."
        sharing_context = "The user is currently sharing their screen." if is_sharing else "The user is NOT sharing their screen."

        system_instruction = (
            "You are a simple video editing helper.\n"
            "\n"
            "Your rules:\n"
            "- Use very simple English.\n"
            "- Keep answers short and clear.\n"
            "- Do NOT start every message with 'Hello' or 'Hi'.\n"
            "- Do NOT explain theory.\n"
            "- Do NOT repeat information.\n"
            "- Do NOT use advanced words.\n"
            "- If the user asks 'how to do it', reply with step-by-step actions.\n"
            "- Steps must be like: Click this → Do that → Done.\n"
            f"- {app_context}\n"
            f"- {sharing_context}\n"
            "- If the user asks if you can see their screen, explain that while they are sharing, you can only provide guidance based on their questions.\n"
            "- Do NOT act like an expert analyst.\n"
            "- Be direct and helpful.\n"
            "\n"
            "Answer format rules:\n"
            "- Maximum 5 steps.\n"
            "- Each step must be one short sentence.\n"
            "- No long paragraphs.\n"
            "- No repetitive greetings.\n"
        )

        context = ""
        if analysis_summary:
            context = f"Video Analysis Context:\n{analysis_summary}\n\n"

        prompt = f"{context}User Request: {user_query}"
        return self._generate(prompt, system_instruction=system_instruction)

    def explain_suggestion(self, suggestion_reason: str, platform: str = "general") -> str:
        """Explain a specific AI suggestion with step-by-step instructions."""
        system_instruction = "You are a professional video editing assistant providing step-by-step instructions."
        prompt = (
            f"The AI suggested an edit because: '{suggestion_reason}'.\n"
            f"Explain how to perform this specific edit in {platform}.\n"
            "Provide exactly 3 clear, actionable steps."
        )
        return self._generate(prompt, system_instruction=system_instruction)
