from celery import shared_task
@shared_task
def process_script_generation_job_task(job_id):
    from apps.scriptgen.service.script_generation_service import ScriptGenerationService
    return ScriptGenerationService.process_generation_job(job_id)
