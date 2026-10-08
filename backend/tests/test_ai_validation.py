import pytest
from app.services.ai.gemini import gemini_service

def test_ai_response_parsing():
    raw_markdown = """```json
    {
      "status": "COMPLETE",
      "relevance": "HIGH",
      "confidence": 0.95,
      "missingInformation": [],
      "findings": ["Access review verified."],
      "reason": "All requirements satisfied."
    }
    ```"""
    parsed = gemini_service._parse_json_response(raw_markdown)
    assert parsed is not None
    assert parsed["status"] == "COMPLETE"
    assert parsed["confidence"] == 0.95

def test_ai_response_parsing_invalid():
    raw_broken = "I am an AI and I think this document is valid but here is no json."
    parsed = gemini_service._parse_json_response(raw_broken)
    assert parsed is None

@pytest.mark.asyncio
async def test_deterministic_validation_complete():
    reqs = [
        {"name": "Access Review Report", "mandatory": True},
        {"name": "Approval Evidence", "mandatory": True}
    ]
    extracted = "The quarterly Access Review Report was approved on 2026-10-01. Approval Evidence is verified."
    result = await gemini_service.validate_evidence(
        control_code="C001",
        control_name="Periodic User Access Review",
        control_description="Review user accounts",
        requirements=reqs,
        period_start="2026-07-01",
        period_end="2026-09-30",
        extracted_text=extracted
    )
    assert result["status"] == "COMPLETE"
    assert len(result["missingInformation"]) == 0

@pytest.mark.asyncio
async def test_deterministic_validation_incomplete():
    reqs = [
        {"name": "Access Review Report", "mandatory": True},
        {"name": "Exception Report", "mandatory": True}
    ]
    extracted = "Here is the raw access listing with accounts. Review report details."
    result = await gemini_service.validate_evidence(
        control_code="C001",
        control_name="Periodic User Access Review",
        control_description="Review user accounts",
        requirements=reqs,
        period_start="2026-07-01",
        period_end="2026-09-30",
        extracted_text=extracted
    )
    assert result["status"] == "INCOMPLETE"
    assert "Exception Report" in result["missingInformation"]
