from django.urls import path
from rest_framework.routers import DefaultRouter
from .api.script_generation_job_status_api import ScriptGenerationJobStatusAPI
from .api.script_generation_submit_api import ScriptGenerationSubmitAPI
from .api.script_version_review_api import ScriptVersionReviewAPI
from .api.views import ScriptFileViewSet, ScriptGenerationJobViewSet, ScriptVersionViewSet
router = DefaultRouter()
router.register('script-generation-jobs', ScriptGenerationJobViewSet)
router.register('script-files', ScriptFileViewSet)
router.register('script-versions', ScriptVersionViewSet)
urlpatterns = router.urls + [
    path('script-generation/submit/', ScriptGenerationSubmitAPI.as_view(), name='api-script-generation-submit'),
    path('script-generation/jobs/<int:job_id>/status/', ScriptGenerationJobStatusAPI.as_view(), name='api-script-generation-job-status'),
    path('script-versions/<int:version_id>/review/', ScriptVersionReviewAPI.as_view()),
]
