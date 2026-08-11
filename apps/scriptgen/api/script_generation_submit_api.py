from django.conf import settings
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.scriptgen.serializers import ScriptGenerationSubmissionSerializer
from apps.scriptgen.service.script_generation_service import ScriptGenerationService
from common.response import ApiResponse


class ScriptGenerationSubmitAPI(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ScriptGenerationSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = dict(serializer.validated_data)
        run_async = payload.pop("run_async", False)

        try:
            if run_async or not settings.CELERY_TASK_ALWAYS_EAGER:
                result = ScriptGenerationService.enqueue_generation_request(**payload)
                return ApiResponse.success(data=result, msg="任务已提交", status=202)

            result = ScriptGenerationService.submit_generation_request(**payload)
            return ApiResponse.success(data=result, msg="OK", status=201)
        except ValueError as exc:
            return ApiResponse.fail(str(exc))
        except Exception as exc:
            return ApiResponse.fail(str(exc), code=500, status=500)
