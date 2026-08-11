from celery import shared_task
@shared_task
def process_requirement_job_task(job_id):
    from apps.testsuite.service.test_design_service import TestDesignService
    return TestDesignService.process_requirement_job(job_id)
