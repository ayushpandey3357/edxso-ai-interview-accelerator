import json
import re
from typing import Dict, Any, Optional
from app.config import Config

class LLMClient:
    def __init__(self, gemini_key: str = Config.GEMINI_API_KEY, openai_key: str = Config.OPENAI_API_KEY, provider: str = Config.LLM_PROVIDER):
        self.gemini_key = gemini_key
        self.openai_key = openai_key
        self.provider = provider.lower()

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        """
        Executes LLM call using OpenAI or Gemini depending on configured API keys.
        Returns parsed JSON object.
        """
        # Try OpenAI if requested or if OpenAI key is present
        if (self.provider == "openai" or not self.gemini_key) and self.openai_key:
            try:
                return self._call_openai(prompt)
            except Exception as e:
                print(f"[LLMClient] OpenAI call failed: {e}")
                if self.gemini_key:
                    return self._call_gemini(prompt)
                raise e

        # Default to Gemini if key is present
        if self.gemini_key:
            try:
                return self._call_gemini(prompt)
            except Exception as e:
                print(f"[LLMClient] Gemini call failed: {e}")
                if self.openai_key:
                    return self._call_openai(prompt)
                raise e

        raise ValueError("No valid LLM API Key provided.")

    def _call_openai(self, prompt: str) -> Dict[str, Any]:
        from openai import OpenAI
        client = OpenAI(api_key=self.openai_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional HR, technical recruiter, and AI assessment engine. Always respond with raw valid JSON without markdown tags."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content.strip()
        return json.loads(content)

    def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        import google.generativeai as genai
        genai.configure(api_key=self.gemini_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        resp_text = response.text.strip()
        resp_text = re.sub(r"^```json\s*", "", resp_text)
        resp_text = re.sub(r"\s*```$", "", resp_text)
        return json.loads(resp_text)
