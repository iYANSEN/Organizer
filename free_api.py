"""
Free API wrapper — Gemini (primary) with GPT-4o-mini fallback.
Handles email classification and file organization.
"""

import json
import re
from typing import Optional
import httpx


SYSTEM_PROMPT = """You are a personal file and email organizer AI.
Your job is to categorize emails and files accurately and suggest what to do with them.
Always respond with valid JSON only — no explanation, no markdown.

Categories: Finances, Work, Personal, Receipts, Travel, Health, Legal, Newsletters, Other

For emails:
- "action" options: "move", "archive", "delete", "label"
- "action" = "delete" only for obvious spam
- "action" = "archive" for newsletters or low-priority

For files:
- "action" options: "move", "rename_and_move", "skip"  
- Suggest a clean filename using format: YYYY-MM_Description.ext
- "action" = "skip" if the file doesn't seem worth organizing (e.g., .tmp, .log)
"""

EMAIL_PROMPT_TEMPLATE = """Categorize this email:

Subject: {subject}
From: {sender}
Date: {date}
Snippet: {snippet}

Respond ONLY with this JSON:
{{
  "category": "<Category>",
  "action": "<action>",
  "suggested_label": "<label>",
  "confidence": <0-100>,
  "reasoning": "<one sentence>"
}}"""

FILE_PROMPT_TEMPLATE = """Categorize this file:

Filename: {name}
Extension: {extension}
Size: {size_bytes} bytes
Path: {path}

Respond ONLY with this JSON:
{{
  "category": "<Category>",
  "action": "<action>",
  "new_name": "<suggested_filename_or_null>",
  "confidence": <0-100>,
  "reasoning": "<one sentence>"
}}"""


class FreeAPI:
    def __init__(self, config: dict):
        self.config = config
        self.api_key = config.get("gemini_api_key", "")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def _call_gemini(self, prompt: str) -> str:
        """Make a Gemini API call and return the text response."""
        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 256,
            }
        }
        
        response = await self.client.post(
            f"{self.base_url}?key={self.api_key}",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def _parse_json_response(self, text: str) -> dict:
        """Safely parse JSON from LLM response, stripping markdown fences."""
        text = text.strip()
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return json.loads(text)

    async def classify_email(self, email: dict) -> dict:
        """Classify an email and return a decision dict."""
        prompt = EMAIL_PROMPT_TEMPLATE.format(
            subject=email.get("subject", ""),
            sender=email.get("sender", ""),
            date=email.get("date", ""),
            snippet=email.get("snippet", "")[:500]  # Truncate for token limits
        )
        
        try:
            raw = await self._call_gemini(prompt)
            result = self._parse_json_response(raw)
            # Ensure required fields
            result.setdefault("confidence", 70.0)
            result.setdefault("reasoning", "Classified by Gemini")
            result.setdefault("action", "archive")
            result.setdefault("category", "Other")
            return result
        except Exception as e:
            return {
                "category": "Other",
                "action": "archive",
                "suggested_label": "Other",
                "confidence": 0.0,
                "reasoning": f"API error: {str(e)}",
                "error": True
            }

    async def classify_file(self, file: dict) -> dict:
        """Classify a file and return a decision dict."""
        prompt = FILE_PROMPT_TEMPLATE.format(
            name=file.get("name", ""),
            extension=file.get("extension", ""),
            size_bytes=file.get("size_bytes", 0),
            path=file.get("path", "")
        )
        
        try:
            raw = await self._call_gemini(prompt)
            result = self._parse_json_response(raw)
            result.setdefault("confidence", 70.0)
            result.setdefault("reasoning", "Classified by Gemini")
            result.setdefault("action", "move")
            result.setdefault("category", "Other")
            result.setdefault("new_name", None)
            return result
        except Exception as e:
            return {
                "category": "Other",
                "action": "skip",
                "new_name": None,
                "confidence": 0.0,
                "reasoning": f"API error: {str(e)}",
                "error": True
            }
