from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from apps.testsuite.models import TestDesignJob
from apps.testsuite.serializers import TestDesignJobSerializer
from common.response import ApiResponse

class RequirementJobStatusAPI(APIView):
    permission_classes = [AllowAny]
    def get(self, request, job_id):
        job = TestDesignJob.objects.select_related('project','source_document','created_by').filter(id=job_id).first()
        if not job: return ApiResponse.fail(msg='Requirement job not found', code=404, status=404)
        modules = job.modules.count(); suites = job.test_suites.count()
        testcases = sum(suite.test_cases.count() for suite in job.test_suites.all())
        parse_error = job.source_document.parse_error if job.source_document else ''
        return ApiResponse.success(data={
            'job': TestDesignJobSerializer(job).data, 'status': job.status,
            'is_finished': job.status in {TestDesignJob.STATUS_SUCCESS, TestDesignJob.STATUS_FAILED},
            'is_success': job.status == TestDesignJob.STATUS_SUCCESS,
            'document_id': job.source_document_id, 'design_job_id': job.id,
            'module_count': modules, 'suite_count': suites, 'testcase_count': testcases,
            'error_message': parse_error,
        })
