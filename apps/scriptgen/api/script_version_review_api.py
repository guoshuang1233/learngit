from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from apps.scriptgen.serializers import ScriptVersionReviewSerializer
from apps.scriptgen.service.script_generation_service import ScriptGenerationService
from common.response import ApiResponse

class ScriptVersionReviewAPI(APIView):
    permission_classes = [AllowAny]
    def post(self, request, version_id):
        payload = request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
        payload["version_id"] = version_id
        serializer = ScriptVersionReviewSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        version = ScriptGenerationService.review_script_version(
            version_id=serializer.validated_data["version_id"],
            review_status=serializer.validated_data["review_status"],
            content=serializer.validated_data.get("content", ""),
            change_summary=serializer.validated_data.get("change_summary", ""),
        )
        return ApiResponse.success(
            data={
                "version_id": version.id,
                "review_status": version.review_status,
                "script_file_id": version.script_file_id,
            },
            msg="OK",
        )
