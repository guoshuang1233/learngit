from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .api.project_api import ProjectViewSet
from .views import (workbench, submit_requirement_workbench, submit_script_generation_workbench,
    review_script_version_workbench, execute_script_version_workbench,
    download_design_job_workbench, download_report_workbench)
router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
urlpatterns = [
    path('', include(router.urls)),
    path('ui/workbench/', workbench, name='project-workbench'),
    path('ui/workbench/requirements/submit/', submit_requirement_workbench, name='workbench-requirement-submit'),
    path('ui/workbench/scripts/submit/', submit_script_generation_workbench, name='workbench-script-submit'),
    path('ui/workbench/scripts/review/', review_script_version_workbench, name='workbench-script-review'),
    path('ui/workbench/scripts/execute/', execute_script_version_workbench, name='workbench-script-execute'),
    path('ui/workbench/requirements/<int:design_job_id>/download/', download_design_job_workbench, name='workbench-design-job-download'),
    path('ui/workbench/reports/<int:execution_id>/download/', download_report_workbench, name='workbench-report-download'),
]
