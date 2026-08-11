from apps.execution.models import Execution
from apps.report.service.report_service import ReportService


class RunService:
    @classmethod
    def execute_script(cls, *, script_version, suite=None):
        """
        Create an execution record and generate a lightweight report artifact.
        This is the minimal runnable path until real pytest + Allure wiring is added.
        """
        if suite is None and script_version and getattr(script_version, "script_file", None):
            suite = script_version.script_file.suite

        execution = Execution.objects.create(
            suite=suite,
            script_version=script_version,
            status=Execution.STATUS_RUNNING,
        )

        report_info = ReportService.generate_report(execution)
        execution.status = Execution.STATUS_SUCCESS
        execution.result_dir = report_info.get("result_dir", "")
        execution.stdout = report_info.get("stdout", "Execution completed")
        execution.stderr = report_info.get("stderr", "")
        execution.save(update_fields=["status", "result_dir", "stdout", "stderr"])

        return {
            "execution_id": execution.id,
            "report_url": report_info.get("report_url", ""),
            "status": execution.status,
        }

