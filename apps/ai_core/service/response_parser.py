import json
import re
from collections import defaultdict
from .exceptions import AIResponseParseError, AIResponseSchemaError
from .schema import build_default_design_result, build_default_module, build_default_testcase


class ResponseParser:
    JSON_BLOCK_PATTERN = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)

    @classmethod
    def parse_json_block(cls, raw_text):
        if not raw_text or not raw_text.strip():
            raise AIResponseParseError("AI returned empty text")
        raw_text = raw_text.strip()
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            pass
        fenced_match = cls.JSON_BLOCK_PATTERN.search(raw_text)
        if fenced_match:
            try:
                return json.loads(fenced_match.group(1))
            except json.JSONDecodeError as exc:
                raise AIResponseParseError(f"Failed to decode fenced JSON: {exc}") from exc
        first_brace = raw_text.find("{")
        last_brace = raw_text.rfind("}")
        if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
            try:
                return json.loads(raw_text[first_brace:last_brace + 1])
            except json.JSONDecodeError as exc:
                raise AIResponseParseError(f"Failed to decode extracted JSON: {exc}") from exc
        raise AIResponseParseError("No valid JSON object found in AI response")

    @classmethod
    def parse_design_result(cls, raw_text, *, fallback_title="", fallback_rule_text=""):
        payload = cls.parse_json_block(raw_text)
        result = build_default_design_result()
        result["title"] = cls._clean_text(payload.get("title") or fallback_title)
        result["rule_text"] = cls._clean_text(payload.get("rule_text") or fallback_rule_text)
        result["summary"] = cls._clean_text(payload.get("summary"))

        rows_payload = payload.get("rows")
        if isinstance(rows_payload, list) and rows_payload:
            result["rows"] = cls._normalize_rows(rows_payload)
        else:
            modules_payload = payload.get("modules")
            if isinstance(modules_payload, list) and modules_payload:
                rows = []
                for mi, m in enumerate(modules_payload, 1):
                    mn = cls._clean_text(m.get("name") or f"Module {mi}")
                    sn = cls._clean_text(m.get("suite_name") or f"{mn} Test Suite")
                    for ci, tc in enumerate(m.get("testcases") or [], 1):
                        row = cls._normalize_row(tc, index=ci, module_name=mn, suite_name=sn)
                        row["module_name"] = row["module_name"] or mn
                        row["suite_name"] = row["suite_name"] or sn
                        rows.append(row)
                result["rows"] = cls._normalize_rows(rows) if rows else []
            else:
                result["rows"] = []

        result["modules"] = cls._group_rows_by_module(result["rows"])
        return result

    @classmethod
    def parse_review_result(cls, raw_text):
        payload = cls.parse_json_block(raw_text)
        return {
            "review_summary": cls._clean_text(payload.get("review_summary", "")),
            "passed": bool(payload.get("passed", False)),
            "issues": payload.get("issues") or [],
            "fixed_rows": cls._normalize_rows(payload.get("fixed_rows") or []),
        }

    @classmethod
    def _normalize_rows(cls, rows_payload):
        normalized = []
        case_counters = defaultdict(int)
        for index, row_item in enumerate(rows_payload, start=1):
            row = cls._normalize_row(row_item, index=index)
            if not row["case_no"]:
                case_type = row["case_type"] or "功能测试"
                case_counters[case_type] += 1
                row["case_no"] = cls._build_case_no(case_type, case_counters[case_type])
            normalized.append(row)
        return normalized

    @classmethod
    def _normalize_row(cls, row_item, *, index, module_name="", suite_name=""):
        if not isinstance(row_item, dict):
            raise AIResponseSchemaError(f"Row #{index} must be an object")
        n = build_default_testcase()
        n["case_no"] = cls._clean_text(row_item.get("case_no") or row_item.get("id") or "")
        n["module_name"] = cls._clean_text(row_item.get("module_name") or module_name)
        n["suite_name"] = cls._clean_text(row_item.get("suite_name") or suite_name)
        n["scenario"] = cls._clean_text(row_item.get("scenario") or row_item.get("name") or row_item.get("description"))
        n["description"] = cls._clean_text(row_item.get("description") or n["scenario"])
        n["preconditions"] = cls._normalize_multiline(row_item.get("preconditions"))
        n["steps"] = cls._normalize_multiline(row_item.get("steps"), numbered=True)
        n["expected_result"] = cls._normalize_multiline(row_item.get("expected_result"), numbered=True)
        n["related_tables"] = cls._clean_text(row_item.get("related_tables") or row_item.get("tables") or "")
        n["related_fields"] = cls._clean_text(row_item.get("related_fields") or row_item.get("fields") or "")
        n["priority"] = cls._clean_text(row_item.get("priority") or "P1")
        n["case_type"] = cls._clean_text(row_item.get("case_type") or "功能测试")
        return n

    @classmethod
    def _group_rows_by_module(cls, rows):
        grouped, by_key = [], {}
        for row in rows:
            mn = row["module_name"] or "Generated Module"
            sn = row["suite_name"] or f"{mn} Test Suite"
            key = (mn, sn)
            if key not in by_key:
                m = build_default_module()
                m["name"] = mn
                m["suite_name"] = sn
                m["testcases"] = []
                by_key[key] = m
                grouped.append(m)
            by_key[key]["testcases"].append(row)
        return grouped

    @staticmethod
    def _normalize_multiline(value, numbered=False):
        if value is None:
            return ""
        if isinstance(value, list):
            items = [ResponseParser._clean_text(item) for item in value]
            items = [i for i in items if i]
            if not items:
                return ""
            if numbered:
                return "\n".join(f"{idx}. {item}" for idx, item in enumerate(items, start=1))
            return "\n".join(items)
        return ResponseParser._clean_text(value)

    @classmethod
    def _build_case_no(cls, case_type, sequence):
        prefix_map = {"功能测试": "FUNC", "字段校验": "F"}
        return f"TC-{prefix_map.get(case_type, 'FUNC')}-{sequence:03d}"

    @staticmethod
    def _clean_text(value):
        if value is None:
            return ""
        if isinstance(value, (int, float, bool)):
            return str(value)
        text = str(value).strip()
        text = re.sub(r"^(?:[>|#\-\*]+\s*)+", "", text).strip()
        text = re.sub(r"\s*\|\s*", " ", text).strip()
        text = re.sub(r"\s{2,}", " ", text).strip()
        return text
