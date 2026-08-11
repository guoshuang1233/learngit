import json
import re
from pathlib import Path

from django.conf import settings
from django.db import transaction

from apps.ai_core.service.ai_client import AIClient
from apps.documents.models import SourceDocument
from apps.documents.repo.source_document_repo import SourceDocumentRepo
from apps.documents.service.source_document_service import SourceDocumentService
from apps.project.service.default_project import resolve_project_or_default
from apps.scriptgen.models import ScriptFile, ScriptGenerationJob, ScriptVersion
from apps.testcase.models import TestCase
from apps.testsuite.models import TestSuite
from common.base_service import BaseService


class ScriptGenerationService(BaseService):
    @classmethod
    def submit_generation_request(
        cls,
        *,
        project_id=None,
        suite_id=None,
        suite_document_id=None,
        api_document_id=None,
        created_by_id=None,
        suite_title="",
        api_title="",
        suite_file=None,
        api_file=None,
        suite_text="",
        api_text="",
        rule_text="",
    ):
        job = cls._create_generation_job(
            project_id=project_id,
            suite_id=suite_id,
            suite_document_id=suite_document_id,
            api_document_id=api_document_id,
            created_by_id=created_by_id,
            suite_title=suite_title,
            api_title=api_title,
            suite_file=suite_file,
            api_file=api_file,
            suite_text=suite_text,
            api_text=api_text,
            rule_text=rule_text,
        )
        return cls.process_generation_job(job.id)

    @classmethod
    def enqueue_generation_request(
        cls,
        *,
        project_id=None,
        suite_id=None,
        suite_document_id=None,
        api_document_id=None,
        created_by_id=None,
        suite_title="",
        api_title="",
        suite_file=None,
        api_file=None,
        suite_text="",
        api_text="",
        rule_text="",
    ):
        job = cls._create_generation_job(
            project_id=project_id,
            suite_id=suite_id,
            suite_document_id=suite_document_id,
            api_document_id=api_document_id,
            created_by_id=created_by_id,
            suite_title=suite_title,
            api_title=api_title,
            suite_file=suite_file,
            api_file=api_file,
            suite_text=suite_text,
            api_text=api_text,
            rule_text=rule_text,
        )
        from apps.scriptgen.tasks import process_script_generation_job_task

        async_result = process_script_generation_job_task.delay(job.id)
        return {"task_id": async_result.id, "job_id": job.id, "status": job.status}

    @classmethod
    def process_generation_job(cls, job_id):
        job = (
            ScriptGenerationJob.objects.select_related("project", "suite", "suite_document", "api_document", "created_by")
            .filter(id=job_id)
            .first()
        )
        if not job:
            raise ValueError("script generation job does not exist")

        project = resolve_project_or_default(job.project)
        suite_record = cls._ensure_suite_record(
            project=project,
            suite=job.suite,
            suite_document=job.suite_document,
            created_by=job.created_by,
        )

        ScriptGenerationJob.objects.filter(id=job.id).update(status=ScriptGenerationJob.STATUS_RUNNING)

        generation = cls._generate_script_payload(
            suite_record=suite_record,
            suite_document=job.suite_document,
            api_document=job.api_document,
            rule_text=job.rule_text or "",
        )

        with transaction.atomic():
            script_file = ScriptFile.objects.create(
                project=project,
                suite=suite_record,
                generation_job=job,
                name=generation["script_file_name"],
                description=generation["description"],
                status=ScriptFile.STATUS_PENDING_REVIEW,
                created_by=job.created_by or project.creator,
            )
            rendered_path = cls._write_rendered_script(script_file.name, generation["script_content"])
            version = ScriptVersion.objects.create(
                script_file=script_file,
                version=1,
                content=generation["script_content"],
                rendered_path=rendered_path,
                source_type=ScriptVersion.SOURCE_AI if generation["ai_used"] else ScriptVersion.SOURCE_MANUAL,
                review_status=ScriptVersion.REVIEW_PENDING,
                generation_rule=job.rule_text or "",
                change_summary="Initial generation",
                created_by=job.created_by or project.creator,
            )
            script_file.current_version = version
            script_file.save(update_fields=["current_version"])
            job.raw_output = generation["raw_output"]
            job.structured_result = generation["structured_result"]
            job.status = ScriptGenerationJob.STATUS_SUCCESS
            job.save(update_fields=["raw_output", "structured_result", "status"])

        return {
            "job_id": job.id,
            "script_file_id": script_file.id,
            "script_version_id": version.id,
            "suite_id": suite_record.id if suite_record else None,
            "status": job.status,
            "summary": {
                "script_file_id": script_file.id,
                "script_version_id": version.id,
                "suite_id": suite_record.id if suite_record else None,
            },
        }

    @classmethod
    def review_script_version(
        cls,
        *,
        script_version=None,
        version_id=None,
        review_status,
        content="",
        change_summary="",
    ):
        if script_version is None:
            script_version = ScriptVersion.objects.select_related("script_file").filter(id=version_id).first()
        if not script_version:
            raise ValueError("script version does not exist")

        if content:
            script_version.content = content
        if change_summary:
            script_version.change_summary = change_summary
        script_version.review_status = review_status
        script_version.save(update_fields=["content", "change_summary", "review_status"] if content or change_summary else ["review_status"])

        script_file = script_version.script_file
        if review_status == ScriptVersion.REVIEW_APPROVED:
            script_file.status = ScriptFile.STATUS_APPROVED
        elif review_status == ScriptVersion.REVIEW_REJECTED:
            script_file.status = ScriptFile.STATUS_REJECTED
        else:
            script_file.status = ScriptFile.STATUS_PENDING_REVIEW
        script_file.save(update_fields=["status"])
        return script_version

    @classmethod
    def _create_generation_job(
        cls,
        *,
        project_id=None,
        suite_id=None,
        suite_document_id=None,
        api_document_id=None,
        created_by_id=None,
        suite_title="",
        api_title="",
        suite_file=None,
        api_file=None,
        suite_text="",
        api_text="",
        rule_text="",
    ):
        project = resolve_project_or_default(project_id)
        created_by = cls._resolve_user(created_by_id)
        suite_document, suite_payload = cls._prepare_document(
            project=project,
            existing_document=cls._resolve_document(suite_document_id),
            title=suite_title,
            source_file=suite_file,
            inline_text=suite_text,
            doc_type=SourceDocument.DOC_TYPE_SUITE,
            created_by=created_by,
        )
        api_document, api_payload = cls._prepare_document(
            project=project,
            existing_document=cls._resolve_document(api_document_id),
            title=api_title,
            source_file=api_file,
            inline_text=api_text,
            doc_type=SourceDocument.DOC_TYPE_API,
            created_by=created_by,
        )
        suite_record = cls._ensure_suite_record(
            project=project,
            suite_id=suite_id,
            suite_document=suite_document,
            created_by=created_by,
        )

        job = ScriptGenerationJob.objects.create(
            project=project,
            suite=suite_record,
            suite_document=suite_document,
            api_document=api_document,
            created_by=created_by or project.creator,
            rule_text=rule_text or "",
            status=ScriptGenerationJob.STATUS_PENDING,
        )
        job._prepared_suite_payload = suite_payload
        job._prepared_api_payload = api_payload
        return job

    @classmethod
    def _prepare_document(
        cls,
        *,
        project,
        existing_document=None,
        title="",
        source_file=None,
        inline_text="",
        doc_type=SourceDocument.DOC_TYPE_SUITE,
        created_by=None,
    ):
        metadata = {}
        uploaded_text = SourceDocumentService.extract_text_from_upload(source_file)
        if inline_text and inline_text.strip():
            final_text = inline_text.strip()
            metadata["text_source"] = "request_body"
        elif uploaded_text:
            final_text = uploaded_text
            metadata["text_source"] = "uploaded_file"
        elif existing_document and existing_document.extracted_text.strip():
            final_text = existing_document.extracted_text.strip()
            metadata["text_source"] = "existing_document"
        else:
            final_text = title.strip() or getattr(source_file, "name", "") or "Document placeholder"
            metadata["text_source"] = "placeholder"

        if existing_document:
            if existing_document.project_id != project.id:
                raise ValueError("source_document does not belong to the selected project")
            if existing_document.doc_type != doc_type:
                raise ValueError("source_document type mismatch")
            merged_metadata = dict(existing_document.metadata or {})
            merged_metadata.update(metadata)
            update_fields = {
                "parse_status": SourceDocument.STATUS_PARSING,
                "parse_error": "",
                "metadata": merged_metadata,
                "extracted_text": final_text,
            }
            if title.strip():
                update_fields["title"] = title.strip()
            if source_file is not None:
                update_fields["source_file"] = source_file
            document = SourceDocumentRepo.update_record(existing_document, **update_fields)
            return document, final_text

        if doc_type == SourceDocument.DOC_TYPE_SUITE:
            document = SourceDocumentService.create_suite_document(
                project=project,
                title=title,
                source_file=source_file,
                extracted_text=final_text,
                uploaded_by=created_by or project.creator,
                metadata=metadata,
            )
        else:
            document = SourceDocumentService.create_api_document(
                project=project,
                title=title,
                source_file=source_file,
                extracted_text=final_text,
                uploaded_by=created_by or project.creator,
                metadata=metadata,
            )
        document = SourceDocumentRepo.update_record(
            document,
            parse_status=SourceDocument.STATUS_PARSING,
            parse_error="",
        )
        return document, final_text

    @classmethod
    def _ensure_suite_record(cls, *, project, suite_id=None, suite_document=None, created_by=None):
        if suite_id:
            suite = TestSuite.objects.filter(id=suite_id, project=project).first()
            if suite:
                return suite
        if suite_document:
            suite = TestSuite.objects.filter(project=project, source_document=suite_document).first()
            if suite:
                return suite
            return TestSuite.objects.create(
                project=project,
                module=None,
                source_document=suite_document,
                created_by=created_by or project.creator,
                name=suite_document.title or "Generated Test Suite",
                description=suite_document.extracted_text[:1000],
            )
        return TestSuite.objects.create(
            project=project,
            module=None,
            source_document=None,
            created_by=created_by or project.creator,
            name=f"{project.name} Test Suite",
            description="Generated by AI Test Platform",
        )

    @classmethod
    def _generate_script_payload(cls, *, suite_record, suite_document, api_document, rule_text=""):
        testcases = list(suite_record.test_cases.order_by("id"))
        testcase_payload = [cls._serialize_testcase(tc) for tc in testcases]
        if not testcase_payload:
            testcase_payload = [cls._fallback_testcase(suite_record)]

        user_prompt = "\n".join(
            [
                "Generate a pytest script for the following test suite.",
                "Return JSON only with fields: suite_name, script_content, testcases.",
                f"Suite name: {suite_record.name}",
                f"Rule text: {rule_text or 'None'}",
                f"Suite document:\n{suite_document.extracted_text if suite_document else ''}",
                f"API document:\n{api_document.extracted_text if api_document else ''}",
                json.dumps({"suite_name": suite_record.name, "script_content": "# pytest", "testcases": testcase_payload}, ensure_ascii=False, indent=2),
            ]
        )

        try:
            client = AIClient()
            raw_output = client.generate_text(
                user_prompt,
                system_prompt="You are a senior test automation engineer. Output JSON only.",
                temperature=0.1,
            )
            parsed = cls._extract_json_object(raw_output)
            payload = json.loads(parsed)
            script_content = payload.get("script_content") or ""
            if script_content.strip():
                return {
                    "ai_used": True,
                    "raw_output": raw_output,
                    "structured_result": {
                        "suite_name": payload.get("suite_name") or suite_record.name,
                        "rule_text": rule_text,
                        "script_content": script_content,
                        "testcases": payload.get("testcases") or testcase_payload,
                    },
                    "script_content": script_content,
                    "script_file_name": cls._script_file_name(suite_record.name),
                    "description": f"Generated for {suite_record.name}",
                }
        except Exception as exc:
            raw_output = str(exc)
        script_content = cls._build_local_script(suite_record=suite_record, testcases=testcase_payload, rule_text=rule_text)
        structured_result = {
            "suite_name": suite_record.name,
            "rule_text": rule_text,
            "script_content": script_content,
            "testcases": testcase_payload,
        }
        return {
            "ai_used": False,
            "raw_output": json.dumps(structured_result, ensure_ascii=False, indent=2),
            "structured_result": structured_result,
            "script_content": script_content,
            "script_file_name": cls._script_file_name(suite_record.name),
            "description": f"Generated for {suite_record.name}",
        }

    @staticmethod
    def _serialize_testcase(testcase):
        return {
            "case_no": getattr(testcase, "case_path", "") or f"TC-{testcase.id:03d}",
            "module_name": testcase.suite.module.name if testcase.suite and testcase.suite.module else "",
            "suite_name": testcase.suite.name if testcase.suite else "",
            "scenario": testcase.name,
            "description": testcase.description or testcase.name,
            "related_tables": testcase.related_tables or "",
            "related_fields": testcase.related_fields or "",
            "preconditions": testcase.preconditions or "",
            "steps": testcase.steps or "",
            "expected_result": testcase.expected_result or "",
            "priority": "P1",
            "case_type": "Functional Test",
        }

    @staticmethod
    def _fallback_testcase(suite_record):
        return {
            "case_no": "TC-FUNC-001",
            "module_name": "",
            "suite_name": suite_record.name,
            "scenario": f"Smoke check for {suite_record.name}",
            "description": "",
            "related_tables": "",
            "related_fields": "",
            "preconditions": "Document and environment are ready",
            "steps": "1. Open the target page\n2. Execute the main flow",
            "expected_result": "The main flow completes successfully",
            "priority": "P1",
            "case_type": "Functional Test",
        }

    @staticmethod
    def _build_local_script(*, suite_record, testcases, rule_text=""):
        lines = [
            "import pytest",
            "",
            f'\"\"\"Auto generated script for {suite_record.name}.\"\"\"',
            "",
        ]
        if rule_text:
            lines.append(f"# Rule: {rule_text}")
            lines.append("")
        for index, testcase in enumerate(testcases, start=1):
            function_name = re.sub(r"[^0-9a-zA-Z_]+", "_", testcase["scenario"].lower()).strip("_")
            if not function_name:
                function_name = f"case_{index}"
            lines.extend(
                [
                    f"def test_{function_name}():",
                    f'    """{testcase["scenario"]}"""',
                    f'    # case_no: {testcase["case_no"]}',
                    f'    # preconditions: {testcase["preconditions"]}',
                    f'    # steps: {testcase["steps"]}',
                    f'    # expected_result: {testcase["expected_result"]}',
                    "    assert True",
                    "",
                ]
            )
        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def _write_rendered_script(file_name, script_content):
        generated_root = Path(getattr(settings, "GENERATED_ROOT"))
        output_dir = generated_root / "pytest_scripts"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / file_name
        output_path.write_text(script_content, encoding="utf-8")
        return str(output_path)

    @staticmethod
    def _script_file_name(suite_name):
        safe = re.sub(r'[\\/:*?"<>|]+', "_", suite_name or "generated_suite").strip()
        safe = safe or "generated_suite"
        return f"{safe}.py"

    @staticmethod
    def _resolve_user(user_id):
        if not user_id:
            return None
        from apps.user.models import User

        if isinstance(user_id, User):
            return user_id
        return User.objects.filter(id=user_id).first()

    @staticmethod
    def _resolve_document(document_id):
        if not document_id:
            return None
        return SourceDocument.objects.filter(id=document_id).first()

    @staticmethod
    def _extract_json_object(raw_text):
        raw_text = (raw_text or "").strip()
        if raw_text.startswith("{") and raw_text.endswith("}"):
            return raw_text
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
        if fenced:
            return fenced.group(1)
        first = raw_text.find("{")
        last = raw_text.rfind("}")
        if first != -1 and last != -1 and first < last:
            return raw_text[first:last + 1]
        return raw_text

