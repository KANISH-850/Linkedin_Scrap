"""Provider-independent LLM client with support for OpenAI/Gemini/Ollama and graceful heuristic fallback."""

import json
from typing import Any
import httpx

from app.ai.heuristic import HeuristicIntelligenceEngine
from app.ai.schemas import (
    AIDraftMessageResult,
    AIEligibilityResult,
    AIExtractionResult,
    AIReplyAnalysisResult,
    AIScoringResult,
    BaseLLMClient,
)
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProviderIndependentLLM(BaseLLMClient):
    """
    Directs tasks to external LLM (OpenAI-compatible / Gemini) if credentials exist.
    If unavailable, rate-limited, or failed, seamlessly falls back to the deterministic Heuristic engine
    without throwing unhandled errors or fabricating data.
    """

    def __init__(self) -> None:
        self.heuristic = HeuristicIntelligenceEngine()

    async def _call_llm_json(self, system_prompt: str, user_prompt: str, timeout: int = 30) -> dict[str, Any] | None:
        settings = get_settings()
        if not settings.llm_api_key or settings.llm_provider == "heuristic":
            return None

        headers = {
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        try:
            url = f"{settings.llm_base_URL.rstrip('/')}/chat/completions"
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, headers=headers, json=body)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
                logger.warning(f"LLM API returned {resp.status_code}: {resp.text[:200]}")
        except Exception as exc:
            logger.warning(f"LLM API call failed: {exc}. Falling back to heuristic engine.")
        return None

    async def extract_and_classify(self, text: str, title: str, context: dict) -> AIExtractionResult:
        sys_prompt = (
            "You are an expert career intelligence AI. Extract structured opportunity details into strict JSON. "
            "Never fabricate salary, deadline, or eligibility. Set deadline to YYYY-MM-DD or null. "
            "Referral classification must be one of: confirmed_referral_offer, explicit_referral_request, "
            "hiring_with_possible_referral, general_job_announcement, unclear_evidence."
        )
        user_prompt = f"Title: {title}\nContext: {json.dumps(context)}\nContent:\n{text[:3500]}"
        raw_json = await self._call_llm_json(sys_prompt, user_prompt)
        if raw_json:
            try:
                return AIExtractionResult.model_validate(raw_json)
            except Exception as exc:
                logger.warning(f"Failed to validate LLM extraction schema: {exc}")
        return await self.heuristic.extract_and_classify(text, title, context)

    async def evaluate_eligibility_and_score(
        self, candidate_profile: dict, opportunity_data: dict, weights: dict
    ) -> tuple[AIEligibilityResult, AIScoringResult]:
        sys_prompt = (
            "Evaluate candidate eligibility and calculate opportunity scores. "
            "Candidate is a 3rd-year CS student graduating in 2028. "
            "Never ignore mandatory requirements like graduation year or experience. "
            "Return JSON with two keys: 'eligibility' and 'scoring'."
        )
        user_prompt = f"Candidate Profile:\n{json.dumps(candidate_profile)}\n\nOpportunity:\n{json.dumps(opportunity_data)}\n\nWeights:\n{json.dumps(weights)}"
        raw_json = await self._call_llm_json(sys_prompt, user_prompt)
        if raw_json and "eligibility" in raw_json and "scoring" in raw_json:
            try:
                elig = AIEligibilityResult.model_validate(raw_json["eligibility"])
                sc = AIScoringResult.model_validate(raw_json["scoring"])
                return elig, sc
            except Exception as exc:
                logger.warning(f"Failed to validate LLM score schema: {exc}")
        return await self.heuristic.evaluate_eligibility_and_score(candidate_profile, opportunity_data, weights)

    async def draft_message(
        self, candidate_profile: dict, opportunity_data: dict, draft_type: str, custom_context: str | None = None
    ) -> AIDraftMessageResult:
        sys_prompt = (
            "You are an executive career coach drafting professional outreach for a student candidate. "
            "Never fabricate candidate achievements or imply referrals that do not exist. "
            "Connection requests must be <= 300 characters. Return JSON with 'draft_type', 'subject', 'body'."
        )
        user_prompt = (
            f"Draft Type: {draft_type}\n"
            f"Candidate: {json.dumps(candidate_profile)}\n"
            f"Opportunity: {json.dumps(opportunity_data)}\n"
            f"Context: {custom_context or ''}"
        )
        raw_json = await self._call_llm_json(sys_prompt, user_prompt)
        if raw_json:
            try:
                return AIDraftMessageResult.model_validate(raw_json)
            except Exception as exc:
                logger.warning(f"Failed to validate draft message schema: {exc}")
        return await self.heuristic.draft_message(candidate_profile, opportunity_data, draft_type, custom_context)

    async def analyze_reply(
        self, reply_text: str, opportunity_data: dict | None, candidate_profile: dict
    ) -> AIReplyAnalysisResult:
        sys_prompt = (
            "Analyze a message reply from a recruiter or employee. "
            "Classify intent, explain situation, recommend next step, and provide a suggested reply. "
            "Return JSON matching AIReplyAnalysisResult."
        )
        user_prompt = f"Reply:\n{reply_text}\n\nOpportunity:\n{json.dumps(opportunity_data or {})}"
        raw_json = await self._call_llm_json(sys_prompt, user_prompt)
        if raw_json:
            try:
                return AIReplyAnalysisResult.model_validate(raw_json)
            except Exception as exc:
                logger.warning(f"Failed to validate reply analysis schema: {exc}")
        return await self.heuristic.analyze_reply(reply_text, opportunity_data, candidate_profile)


ai_service = ProviderIndependentLLM()

