from django.urls import path
from rest_framework.routers import DefaultRouter
from .api.requirement_job_status_api import RequirementJobStatusAPI
from .api.requirement_submit_api import RequirementSubmitAPI
from .api.views import BusinessModuleViewSet, TestDesignJobViewSet, TestSuiteViewSet
router = DefaultRouter()
router.register('test-design-jobs', TestDesignJobViewSet)
router.register('business-modules', BusinessModuleViewSet)
router.register('testsuites', TestSuiteViewSet)
urlpatterns = router.urls + [
    path('requirements/submit/', RequirementSubmitAPI.as_view(), name='api-requirement-submit'),
    path('requirements/jobs/<int:job_id>/status/', RequirementJobStatusAPI.as_view(), name='api-requirement-job-status'),
]
