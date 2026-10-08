import json
import re
import httpx
from typing import Dict, Any, List, Optional
from app.config import settings


class GeminiValidationService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL or "gemini-1.5-flash"
        self.client = None
        self.decision_provider = settings.DECISION_PROVIDER  # "gemini" or "clef"

        # ── Gemini client ──────────────────────────────────────────────────
        if self.api_key and self.api_key not in ("", "your-gemini-api-key"):
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model_name)
                print(f"[GeminiService] ✅ Gemini client initialised (model: {self.model_name})")
            except Exception as e:
                print(f"[GeminiService] ⚠ Gemini init error: {e}. Fallback will be used.")

        # ── Cloudflare CLEF client ─────────────────────────────────────────
        self.cf_account_id = settings.CLOUDFLARE_ACCOUNT_ID
        self.cf_api_token = settings.CLOUDFLARE_API_TOKEN
        self.cf_gateway_id = settings.CLOUDFLARE_AI_GATEWAY_ID
        self.cf_model = settings.CLEF_MODEL

        if settings.has_cloudflare_ai():
            print(f"[GeminiService] ✅ Cloudflare AI available (model: {self.cf_model})")

    async def validate_evidence(
        self,
        control_code: str,
        control_name: str,
        control_description: str,
        requirements: List[Dict[str, Any]],
        period_start: str,
        period_end: str,
        extracted_text: str,
    ) -> Dict[str, Any]:
        """
        Validates extracted evidence against control requirements using Gemini API.
        Returns structured dictionary matching the AIValidationResult schema.
        """
        req_list_str = "\n".join([
            f"- {r.get('name', '')}: {r.get('description', '')} (Mandatory: {r.get('mandatory', True)})"
            for r in requirements
        ])

        system_prompt = f"""You are an expert LOD2 (Second Line of Defense) IT & Internal Controls Testing Auditor.
Your task is to objectively evaluate whether the submitted evidence satisfies the control requirements for the specified review period.

CONTROL DETAILS:
Code: {control_code}
Name: {control_name}
Description: {control_description}
Review Period: {period_start} to {period_end}

EVIDENCE REQUIREMENTS:
{req_list_str}

SUBMITTED EVIDENCE EXTRACTED CONTENT:
\"\"\"
{extracted_text[:35000]}
\"\"\"

CRITICAL AUDIT RULES:
1. Do not hallucinate or assume evidence exists outside what is explicitly provided.
2. Only use the supplied evidence text.
3. If all mandatory requirements are satisfied with evidence covering the review period, status must be "COMPLETE".
4. If some mandatory requirements or necessary approvals/dates are missing from the evidence, status must be "INCOMPLETE", and list the specific missing requirements in "missingInformation".
5. If the uploaded document is completely unrelated to this control, status must be "IRRELEVANT", relevance "LOW", and list all requirements in "missingInformation".
6. Be strict and deterministic.
7. Return ONLY a single raw JSON object with NO markdown code block wrappers (do not write ```json).

JSON Output Schema:
{{
  "status": "COMPLETE" | "INCOMPLETE" | "IRRELEVANT",
  "relevance": "HIGH" | "MEDIUM" | "LOW",
  "confidence": 0.0 to 1.0,
  "missingInformation": ["List of missing requirements or items"],
  "findings": ["Specific factual findings observed in the evidence"],
  "reason": "Detailed summary explanation of audit determination"
}}"""

        # ── Route to chosen AI provider ───────────────────────────────────────
        # 1. Cloudflare CLEF (when DECISION_PROVIDER=clef)
        if self.decision_provider == "clef" and settings.has_cloudflare_ai():
            try:
                result = await self._call_cloudflare_clef(system_prompt)
                if result:
                    return result
            except Exception as e:
                print(f"[GeminiService] CLEF call failed: {e}. Trying Gemini.")

        # 2. Gemini
        if self.client:
            try:
                response = self.client.generate_content(
                    system_prompt,
                    generation_config={"temperature": 0.1, "response_mime_type": "application/json"}
                )
                raw_text = response.text.strip()
                parsed = self._parse_json_response(raw_text)
                if parsed:
                    parsed["model"] = self.model_name
                    parsed["raw_response"] = raw_text
                    return parsed
            except Exception as e:
                print(f"[GeminiService] Gemini call failed: {e}. Using deterministic fallback.")

        # 3. Deterministic / Rule-Based Fallback
        return self._deterministic_fallback_validation(
            control_code=control_code,
            requirements=requirements,
            extracted_text=extracted_text
        )

    async def _call_cloudflare_clef(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Calls the Cloudflare AI Workers API (CLEF model) with the given prompt.
        Uses the AI Gateway endpoint when CLOUDFLARE_AI_GATEWAY_ID is set.
        """
        # Cloudflare AI Gateway URL pattern:
        # https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}/workers-ai/{model}
        if self.cf_gateway_id and self.cf_gateway_id != "":
            url = (
                f"https://gateway.ai.cloudflare.com/v1/"
                f"{self.cf_account_id}/{self.cf_gateway_id}/workers-ai/{self.cf_model}"
            )
        else:
            url = (
                f"https://api.cloudflare.com/client/v4/accounts/"
                f"{self.cf_account_id}/ai/run/{self.cf_model}"
            )

        headers = {
            "Authorization": f"Bearer {self.cf_api_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messages": [
                {"role": "system", "content": "You are an expert LOD2 auditor that responds ONLY with valid JSON."},
                {"role": "user", "content": prompt},
            ]
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        # Cloudflare response: {"result": {"response": "<text>"}, ...}
        raw_text = (
            data.get("result", {}).get("response", "")
            or data.get("choices", [{}])[0].get("message", {}).get("content", "")
        )
        parsed = self._parse_json_response(raw_text)
        if parsed:
            parsed["model"] = self.cf_model
            parsed["raw_response"] = raw_text
        return parsed

    def _parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:

        try:
            # Direct parse
            return json.loads(text)
        except Exception:
            pass

        # Clean code fences
        cleaned = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
        try:
            return json.loads(cleaned)
        except Exception:
            pass

        # Regex search for JSON object
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass

        return None

    def _deterministic_fallback_validation(
        self,
        control_code: str,
        requirements: List[Dict[str, Any]],
        extracted_text: str
    ) -> Dict[str, Any]:
        """
        Deterministic, offline evaluation logic that inspects the extracted text
        against requirements when Gemini API key is not configured or network is unavailable.
        """
        lower_text = extracted_text.lower()
        missing = []
        findings = []

        # Check for empty or error content
        if not extracted_text or "[Extraction Error" in extracted_text or len(extracted_text.strip()) < 30:
            return {
                "status": "IRRELEVANT",
                "relevance": "LOW",
                "confidence": 0.85,
                "missingInformation": [r.get("name", "Evidence") for r in requirements],
                "findings": ["The uploaded document appears to be empty or unreadable."],
                "reason": "Uploaded file contains insufficient or unreadable content.",
                "model": "deterministic-fallback",
                "raw_response": "{\"status\": \"IRRELEVANT\"}"
            }

        # Check relevance to general LOD2 / control terms
        control_keywords = ["access", "review", "approval", "report", "user", "audit", "authorization", "period", "log", "security", "control"]
        relevance_score = sum(1 for kw in control_keywords if kw in lower_text)

        if relevance_score < 1 and len(lower_text) < 200:
            return {
                "status": "IRRELEVANT",
                "relevance": "LOW",
                "confidence": 0.90,
                "missingInformation": [r.get("name", "") for r in requirements],
                "findings": ["Uploaded document does not contain terms related to control testing or evidence."],
                "reason": "Submitted evidence does not pertain to the specified control requirements.",
                "model": "deterministic-fallback",
                "raw_response": "{\"status\": \"IRRELEVANT\"}"
            }

        # Check each requirement against text
        generic_words = {"report", "evidence", "document", "test", "summary", "data", "file", "list"}
        for req in requirements:
            req_name = req.get("name", "")
            req_name_lower = req_name.lower()
            if "exception" in req_name_lower:
                matched = "exception" in lower_text
            elif "approval" in req_name_lower or "sign-off" in req_name_lower or "signoff" in req_name_lower:
                matched = any(w in lower_text for w in ["approval", "approved", "signoff", "signed off", "sign-off"])
            elif "confirmation" in req_name_lower or "attestation" in req_name_lower:
                matched = any(w in lower_text for w in ["confirmation", "attest", "confirmed", "attestation"])
            else:
                distinctive = [w.lower() for w in req_name.split() if len(w) > 3 and w.lower() not in generic_words]
                if distinctive:
                    matched = all(w in lower_text for w in distinctive)
                else:
                    matched = req_name_lower in lower_text

            if matched:
                findings.append(f"Found evidence corresponding to requirement: '{req_name}'")
            else:
                if req.get("mandatory", True):
                    missing.append(req_name)

        if not missing:
            return {
                "status": "COMPLETE",
                "relevance": "HIGH",
                "confidence": 0.92,
                "missingInformation": [],
                "findings": findings or ["All mandatory evidence items and approvals identified."],
                "reason": "The submitted evidence satisfies all mandatory control requirements and period criteria.",
                "model": "deterministic-fallback",
                "raw_response": "{\"status\": \"COMPLETE\"}"
            }
        else:
            return {
                "status": "INCOMPLETE",
                "relevance": "HIGH" if findings else "MEDIUM",
                "confidence": 0.88,
                "missingInformation": missing,
                "findings": findings if findings else ["Partial access information found."],
                "reason": f"Evidence submitted meets partial requirements, but the following mandatory items are missing: {', '.join(missing)}.",
                "model": "deterministic-fallback",
                "raw_response": "{\"status\": \"INCOMPLETE\"}"
            }

gemini_service = GeminiValidationService()
