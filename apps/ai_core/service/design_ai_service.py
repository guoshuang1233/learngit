import json
import re

from apps.ai_core.service.ai_client import AIClient
from apps.ai_core.service.exceptions import (
    AIRequestError,
    AIResponseParseError,
    AIResponseSchemaError,
    AIServiceError,
)
from apps.ai_core.service.response_parser import ResponseParser


class DesignAIService:
    SYSTEM_PROMPT = (
        "You are a senior test architect. Read the full requirement document and output a complete, "
        "review-ready test case table. Do not split the document line by line. Do not copy document "
        "chapter titles as test modules. Derive test scenarios from real business flows, pages, dialogs, "
        "APIs, data validation, permissions, exceptions, and boundary conditions. "
        "Every row must include case_no, module_name, suite_name, scenario, description, related_tables, "
        "related_fields, preconditions, steps, expected_result, priority, and case_type. "
        "steps and expected_result must be concrete, logical, and executable. "
        "Return JSON only. The top-level field must be rows. Use the same human language as the requirement document."
    )

    @classmethod
    def generate_test_design(cls, *, title, requirement_text, rule_text="", client=None):
        clean_text = cls._clean_requirement_text(requirement_text)
        prompt = cls._build_prompt(title=title, requirement_text=clean_text, rule_text=rule_text)

        try:
            raw_output = cls._call_ai(prompt=prompt, client=client)
        except AIRequestError as exc:
            raise AIServiceError(str(exc)) from exc

        try:
            result = ResponseParser.parse_design_result(
                raw_text=raw_output,
                fallback_title=title,
                fallback_rule_text=rule_text,
            )
        except (AIResponseParseError, AIResponseSchemaError) as exc:
            excerpt = cls._compact_text(raw_output, limit=600)
            raise AIServiceError(f"AI returned invalid JSON: {exc}. Response excerpt: {excerpt}") from exc

        if not result.get("rows"):
            excerpt = cls._compact_text(raw_output, limit=600)
            raise AIServiceError(f"AI returned no rows. Response excerpt: {excerpt}")

        return {"raw_output": raw_output, "structured_result": result}

    @classmethod
    def _call_ai(cls, *, prompt, client=None):
        ai_client = client or AIClient()
        return ai_client.generate_text(
            prompt,
            system_prompt=cls.SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=12000,
            response_format={"type": "json_object"},
        )

    @classmethod
    def _build_prompt(cls, *, title, requirement_text, rule_text):
        row_schema = {
            "case_no": "TC-FUNC-001",
            "module_name": "Login and Authorization",
            "suite_name": "User Asset Management Test Suite",
            "scenario": "Verify a concrete end-to-end business scenario",
            "description": "Cover main flow, validation, exceptions, and permissions",
            "related_tables": "user_assets",
            "related_fields": "user_assets.status",
            "preconditions": "Test environment is ready and required accounts exist",
            "steps": "1. Open the target page\n2. Perform the main operation\n3. Verify the result",
            "expected_result": "The system returns the expected and verifiable result",
            "priority": "P1",
            "case_type": "Functional Test",
        }
        return "\n".join(
            [
                "Read the full requirement document and generate the complete test case table.",
                "Requirements:",
                "1. Do not split the document line by line.",
                "2. Do not use chapter titles as test modules.",
                "3. Derive test scenarios from the real business flow.",
                "4. Steps must be specific, logical, and executable.",
                "5. Expected results must be concrete and verifiable.",
                "6. Return JSON only, and the top-level field must be rows.",
                json.dumps({"title": title, "summary": "", "rows": [row_schema]}, ensure_ascii=False, indent=2),
                f"Title: {title}",
                f"Rule: {rule_text or 'None'}",
                f"Requirement:\n{requirement_text}",
            ]
        )

    @classmethod
    def _clean_requirement_text(cls, text):
        text = text or ""
        text = re.sub(r"\|[-\s:|=|]+\|", "", text)
        text = re.sub(r"\n\s*\|", "\n", text)
        text = re.sub(r"\|\s*\n", "\n", text)
        text = re.sub(r"\|", " ", text)
        text = re.sub(r"\n-{3,}\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()[:12000]

    @staticmethod
    def _compact_text(text, *, limit=200):
        text = (text or "").strip()
        text = re.sub(r"\s+", " ", text)
        return text[:limit]
