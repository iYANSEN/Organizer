"""
Orchestrator — the brain of My Organizer.
Decides whether to use Baby AI or Free API for each task.
Logs decisions with confidence scores for training.
"""

import json
import os
import time
from typing import Optional


class Orchestrator:
    def __init__(self, config: dict, db):
        self.config = config
        self.db = db
        self.baby_ai_enabled = config.get("ai", {}).get("baby_ai_enabled", False)
        self.threshold_auto = config.get("ai", {}).get("confidence_threshold_auto", 80)
        self.threshold_suggest = config.get("ai", {}).get("confidence_threshold_suggest", 50)
        
        # Lazy-load APIs
        self._free_api = None
        self._baby_ai = None

    @property
    def free_api(self):
        if self._free_api is None:
            from ai.free_api import FreeAPI
            self._free_api = FreeAPI(self.config)
        return self._free_api

    @property
    def baby_ai(self):
        if self._baby_ai is None and self.baby_ai_enabled:
            from ai.baby_ai.inference import BabyAI
            self._baby_ai = BabyAI(self.config)
        return self._baby_ai

    async def decide_email(self, email: dict) -> dict:
        """
        Given an email dict, return a decision:
        {
          "category": "Finances",
          "action": "move",           # move | archive | delete | label
          "confidence": 87.5,
          "used_model": "baby_ai",    # baby_ai | free_api
          "reasoning": "...",
          "suggested_label": "Finances"
        }
        """
        start = time.time()
        
        # Phase 1: Baby AI not enabled → always use Free API
        if not self.baby_ai_enabled or self.baby_ai is None:
            result = await self.free_api.classify_email(email)
            result["used_model"] = "free_api"
            result["latency_ms"] = int((time.time() - start) * 1000)
            return result
        
        # Phase 2+: Try Baby AI first
        baby_result = self.baby_ai.classify_email(email)
        
        if baby_result["confidence"] >= self.threshold_auto:
            # Baby AI is confident → execute automatically
            baby_result["used_model"] = "baby_ai"
            baby_result["latency_ms"] = int((time.time() - start) * 1000)
            return baby_result
        
        elif baby_result["confidence"] >= self.threshold_suggest:
            # Medium confidence → suggest to user (UI handles this)
            baby_result["used_model"] = "baby_ai"
            baby_result["needs_confirmation"] = True
            baby_result["latency_ms"] = int((time.time() - start) * 1000)
            return baby_result
        
        else:
            # Low confidence → fall back to Free API
            result = await self.free_api.classify_email(email)
            result["used_model"] = "free_api"
            result["baby_ai_confidence"] = baby_result["confidence"]
            result["latency_ms"] = int((time.time() - start) * 1000)
            return result

    async def decide_file(self, file: dict) -> dict:
        """
        Given a file dict, return a decision:
        {
          "category": "Receipts",
          "action": "move",
          "new_name": "2024-01_Amazon_Receipt.pdf",
          "confidence": 91.0,
          "used_model": "free_api",
          "reasoning": "..."
        }
        """
        start = time.time()
        
        if not self.baby_ai_enabled or self.baby_ai is None:
            result = await self.free_api.classify_file(file)
            result["used_model"] = "free_api"
            result["latency_ms"] = int((time.time() - start) * 1000)
            return result
        
        baby_result = self.baby_ai.classify_file(file)
        
        if baby_result["confidence"] >= self.threshold_auto:
            baby_result["used_model"] = "baby_ai"
            baby_result["latency_ms"] = int((time.time() - start) * 1000)
            return baby_result
        elif baby_result["confidence"] >= self.threshold_suggest:
            baby_result["used_model"] = "baby_ai"
            baby_result["needs_confirmation"] = True
            baby_result["latency_ms"] = int((time.time() - start) * 1000)
            return baby_result
        else:
            result = await self.free_api.classify_file(file)
            result["used_model"] = "free_api"
            result["baby_ai_confidence"] = baby_result["confidence"]
            result["latency_ms"] = int((time.time() - start) * 1000)
            return result

    def explain_decision(self, action: dict) -> str:
        """Generate a human-readable explanation for a past decision."""
        model = action.get("used_model", "free_api")
        confidence = action.get("confidence", 0)
        category = action.get("category", "Unknown")
        reasoning = action.get("reasoning", "")
        
        if model == "baby_ai":
            similar_count = self.db.count_similar_past_actions(
                category=category,
                sender=action.get("sender", "")
            )
            return (
                f"🤖 Baby AI — {confidence:.0f}% confident.\n"
                f"Reason: {reasoning}\n"
                f"Based on {similar_count} similar items you've organized the same way."
            )
        else:
            return (
                f"🌐 Free API (Gemini) — used as fallback.\n"
                f"Reason: {reasoning}\n"
                f"Baby AI wasn't confident enough (< {self.threshold_suggest}%)."
            )

    def add_training_example(self, action: dict, correct_category: str, correct_action: str):
        """Write a training example to training_data.jsonl for Baby AI fine-tuning."""
        training_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "storage", "training_data.jsonl"
        )
        
        example = {
            "input": {
                "item_type": action.get("item_type"),
                "subject": action.get("subject", ""),
                "sender": action.get("sender", ""),
                "snippet": action.get("snippet", ""),
                "filename": action.get("filename", ""),
                "extension": action.get("extension", ""),
            },
            "output": {
                "category": correct_category,
                "action": correct_action
            },
            "original_prediction": action.get("category"),
            "original_confidence": action.get("confidence", 0),
            "timestamp": time.time()
        }
        
        os.makedirs(os.path.dirname(training_path), exist_ok=True)
        with open(training_path, "a") as f:
            f.write(json.dumps(example) + "\n")
