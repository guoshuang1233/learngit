from html import escape
from pathlib import Path

from django.conf import settings

from apps.report.models import Report


class ReportService:
    @classmethod
    def generate_report(cls, execution):
        """
        Build a lightweight HTML report artifact for the execution record.
        This keeps the chain usable before real Allure integration is wired in.
        """
        report_dir = Path(settings.MEDIA_ROOT) / "reports" / f"execution_{execution.id}"
        report_dir.mkdir(parents=True, exist_ok=True)

        html_content = cls._build_html(execution)
        report_path = report_dir / "index.html"
        report_path.write_text(html_content, encoding="utf-8")

        report_url = f"{settings.MEDIA_URL.rstrip('/')}/reports/execution_{execution.id}/index.html"
        summary = f"Execution {execution.id} finished with status {execution.status}"

        Report.objects.create(
            execution=execution,
            report_url=report_url,
            summary=summary,
        )

        return {
            "report_url": report_url,
            "summary": summary,
            "result_dir": str(report_dir),
            "stdout": f"Generated report for execution {execution.id}",
            "stderr": "",
        }

    @staticmethod
    def _build_html(execution):
        suite_name = escape(execution.suite.name if execution.suite else "")
        script_version = escape(str(execution.script_version.version) if execution.script_version else "")
        stdout = escape(execution.stdout or "")
        stderr = escape(execution.stderr or "")
        return f"""<!doctype html>
<html lang="zh-Hans">
<head>
  <meta charset="utf-8">
  <title>Execution {execution.id} Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; padding: 24px; color: #1f2937; }}
    .card {{ max-width: 960px; margin: 0 auto; background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 24px; }}
    pre {{ white-space: pre-wrap; background: #f8fafc; padding: 16px; border-radius: 8px; }}
    h1 {{ margin-top: 0; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Execution Report</h1>
    <p><strong>Execution ID:</strong> {execution.id}</p>
    <p><strong>Status:</strong> {escape(execution.status)}</p>
    <p><strong>Suite:</strong> {suite_name}</p>
    <p><strong>Script Version:</strong> {script_version}</p>
    <h2>Stdout</h2>
    <pre>{stdout}</pre>
    <h2>Stderr</h2>
    <pre>{stderr}</pre>
  </div>
</body>
</html>"""

