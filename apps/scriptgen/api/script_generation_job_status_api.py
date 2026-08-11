from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from apps.scriptgen.models import ScriptGenerationJob
from common.response import ApiResponse

class ScriptGenerationJobStatusAPI(APIView):
    permission_classes = [AllowAny]
    def get(self, request, job_id):
        job = ScriptGenerationJob.objects.filter(id=job_id).first()
        if not job: return ApiResponse.fail(msg='Job not found', code=404, status=404)
        script_file = job.scriptfile_set.order_by('-created_at').first()
        return ApiResponse.success(data={
            'job_id': job.id, 'status': job.status,
            'is_finished': job.status in {ScriptGenerationJob.STATUS_SUCCESS, ScriptGenerationJob.STATUS_FAILED},
            'is_success': job.status == ScriptGenerationJob.STATUS_SUCCESS,
            'script_file_id': getattr(script_file, 'id', None),
            'script_version_id': getattr(script_file, 'current_version_id', None),
        })
