import json
from collections import OrderedDict
from django.db import transaction
from apps.ai_core.service.design_ai_service import DesignAIService
from apps.documents.models import SourceDocument
from apps.documents.repo.source_document_repo import SourceDocumentRepo
from apps.documents.serializers import SourceDocumentSerializer
from apps.documents.service.source_document_service import SourceDocumentService
from apps.testcase.models import TestCase
from apps.testcase.serializers import TestCaseSerializer
from apps.testsuite.models import BusinessModule, TestDesignJob, TestSuite
from apps.testsuite.repo.test_design_repo import BusinessModuleRepo, TestCaseAssetRepo, TestDesignJobRepo, TestSuiteRepo
from apps.testsuite.serializers import BusinessModuleSerializer, TestDesignJobSerializer, TestSuiteSerializer
from common.base_service import BaseService


class TestDesignService(BaseService):

    @classmethod
    def submit_requirement_document(cls, *, project, source_document=None, title="",
                                    source_file=None, extracted_text="", rule_text="", created_by=None):
        job = cls._create_requirement_job(project=project, source_document=source_document,
            title=title, source_file=source_file, extracted_text=extracted_text,
            rule_text=rule_text, created_by=created_by)
        return cls.process_requirement_job(job.id)

    @classmethod
    def enqueue_requirement_document(cls, *, project, source_document=None, title="",
                                     source_file=None, extracted_text="", rule_text="", created_by=None):
        job = cls._create_requirement_job(project=project, source_document=source_document,
            title=title, source_file=source_file, extracted_text=extracted_text,
            rule_text=rule_text, created_by=created_by)
        from apps.testsuite.tasks import process_requirement_job_task
        async_result = process_requirement_job_task.delay(job.id)
        return {"task_id": async_result.id, "job_id": job.id,
                "document_id": job.source_document_id, "status": job.status}

    @classmethod
    def _create_requirement_job(cls, *, project, source_document=None, title="",
                                source_file=None, extracted_text="", rule_text="", created_by=None):
        document, _ = cls._prepare_requirement_document(project=project, source_document=source_document,
            title=title, source_file=source_file, extracted_text=extracted_text, created_by=created_by)
        SourceDocumentRepo.update_record(document, parse_status=SourceDocument.STATUS_UPLOADED, parse_error="")
        return TestDesignJobRepo.create(project=project, source_document=document,
            created_by=created_by or project.creator, rule_text=rule_text, status=TestDesignJob.STATUS_PENDING)

    @classmethod
    def process_requirement_job(cls, job_id):
        job = TestDesignJob.objects.select_related("project", "source_document", "created_by").filter(id=job_id).first()
        if not job:
            raise ValueError("test design job does not exist")
        if not job.source_document:
            raise ValueError("test design job has no source document")
        document = job.source_document
        TestDesignJobRepo.update_record(job, status=TestDesignJob.STATUS_RUNNING)
        SourceDocumentRepo.update_record(document, parse_status=SourceDocument.STATUS_PARSING, parse_error="")
        try:
            design_result = DesignAIService.generate_test_design(
                title=document.title, requirement_text=document.extracted_text, rule_text=job.rule_text)
            structured_result = design_result["structured_result"]
            with transaction.atomic():
                created_assets = cls._persist_design_assets(
                    project=job.project, document=document, job=job,
                    created_by=job.created_by or job.project.creator,
                    structured_result=structured_result)
            job = TestDesignJobRepo.update_record(job, raw_output=design_result["raw_output"],
                structured_result=structured_result, status=TestDesignJob.STATUS_SUCCESS)
            SourceDocumentRepo.update_record(document, parse_status=SourceDocument.STATUS_PARSED, parse_error="")
        except Exception as exc:
            TestDesignJobRepo.update_record(job, status=TestDesignJob.STATUS_FAILED)
            SourceDocumentRepo.update_record(document, parse_status=SourceDocument.STATUS_FAILED, parse_error=str(exc))
            raise
        return {
            "document": SourceDocumentSerializer(document).data,
            "job": TestDesignJobSerializer(job).data,
            "modules": BusinessModuleSerializer(created_assets["modules"], many=True).data,
            "suites": TestSuiteSerializer(created_assets["suites"], many=True).data,
            "testcases": TestCaseSerializer(created_assets["testcases"], many=True).data,
            "summary": {"module_count": len(created_assets["modules"]),
                        "suite_count": len(created_assets["suites"]),
                        "testcase_count": len(created_assets["testcases"])},
        }

    @classmethod
    def _prepare_requirement_document(cls, *, project, source_document=None, title="",
                                      source_file=None, extracted_text="", created_by=None):
        metadata = {}
        uploaded_text = SourceDocumentService.extract_text_from_upload(source_file)
        if extracted_text.strip():
            final_text = extracted_text.strip()
            metadata["text_source"] = "request_body"
        elif uploaded_text:
            final_text = uploaded_text
            metadata["text_source"] = "uploaded_file"
        elif source_document and source_document.extracted_text.strip():
            final_text = source_document.extracted_text.strip()
            metadata["text_source"] = "existing_document"
        else:
            final_text = title.strip() or getattr(source_file, "name", "") or "Requirement placeholder"
            metadata["text_source"] = "placeholder"
        if source_document:
            if source_document.project_id != project.id:
                raise ValueError("source_document does not belong to the selected project")
            if source_document.doc_type != SourceDocument.DOC_TYPE_REQUIREMENT:
                raise ValueError("source_document must be a requirement document")
            merged_metadata = dict(source_document.metadata or {})
            merged_metadata.update(metadata)
            update_fields = {"parse_status": SourceDocument.STATUS_PARSING, "parse_error": "",
                           "metadata": merged_metadata, "extracted_text": final_text}
            if title.strip():
                update_fields["title"] = title.strip()
            if source_file is not None:
                update_fields["source_file"] = source_file
            document = SourceDocumentRepo.update_record(source_document, **update_fields)
            return document, final_text
        document = SourceDocumentService.create_requirement_document(
            project=project, title=title, source_file=source_file,
            extracted_text=final_text, uploaded_by=created_by or project.creator, metadata=metadata)
        document = SourceDocumentRepo.update_record(document, parse_status=SourceDocument.STATUS_PARSING, parse_error="")
        return document, final_text

    @classmethod
    def _persist_design_assets(cls, *, project, document, job, created_by, structured_result):
        rows = structured_result.get("rows") or []
        if not rows:
            raise ValueError("AI未生成有效测试用例,请检查AI服务配置")
        created_modules, created_suites, created_testcases = [], [], []
        module_map = OrderedDict()
        for row in rows:
            mn = row.get("module_name") or "未命名模块"
            sn = row.get("suite_name") or f"{mn} Test Suite"
            key = (mn, sn)
            if key not in module_map:
                mr = BusinessModuleRepo.create(project=project, source_document=document, design_job=job,
                    name=mn, description="", sort_order=len(module_map) + 1)
                sr = TestSuiteRepo.create(project=project, module=mr, source_document=document,
                    design_job=job, created_by=created_by, name=sn, description="",
                    review_status=TestSuite.REVIEW_PENDING)
                module_map[key] = {"module": mr, "suite": sr}
                created_modules.append(mr)
                created_suites.append(sr)
            suite_record = module_map[key]["suite"]
            tc_name = row.get("scenario") or row.get("description") or row.get("case_no") or "Generated Case"
            tr = TestCaseAssetRepo.create(
                suite=suite_record, source_document=document, name=tc_name,
                description=row.get("description") or row.get("scenario") or "",
                creator=created_by, preconditions=row.get("preconditions", ""),
                steps=row.get("steps", ""), expected_result=row.get("expected_result", ""),
                related_tables=row.get("related_tables", ""),
                related_fields=row.get("related_fields", ""),
                review_status=TestCase.REVIEW_PENDING, case_path=row.get("case_no", ""))
            created_testcases.append(tr)
        return {"modules": created_modules, "suites": created_suites, "testcases": created_testcases}
