import threading
from django.shortcuts import get_object_or_404
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from apps.documents.models import SourceDocument
from apps.project.models import Project
from apps.testsuite.serializers import RequirementSubmissionSerializer
from apps.testsuite.service.test_design_service import TestDesignService
from apps.user.models import User
from common.response import ApiResponse


class RequirementSubmitAPI(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RequirementSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = dict(serializer.validated_data)
        payload.pop("run_async", None)

        # ID → ORM
        payload["project"] = get_object_or_404(Project, id=payload.pop("project_id"))
        if payload.get("created_by_id"):
            payload["created_by"] = get_object_or_404(User, id=payload.pop("created_by_id"))
        else:
            payload.pop("created_by_id", None)
            payload["created_by"] = payload["project"].creator
        if payload.get("source_document_id"):
            payload["source_document"] = get_object_or_404(SourceDocument, id=payload.pop("source_document_id"))
        else:
            payload.pop("source_document_id", None)

        # 创建 job, 立即返回
        job = TestDesignService._create_requirement_job(**payload)

        # 后台线程处理 AI
        def run():
            try:
                TestDesignService.process_requirement_job(job.id)
            except Exception:
                pass
        threading.Thread(target=run, daemon=True).start()

        return ApiResponse.success(
            data={"job_id": job.id, "status": job.status},
            msg="任务已提交", status=202,
        )
