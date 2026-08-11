from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.documents.models import SourceDocument
from apps.execution.models import Execution
from apps.execution.service.run import RunService
from apps.project.models import Project
from apps.project.service.design_job_xlsx_exporter import DesignJobXlsxExporter
from apps.report.models import Report
from apps.scriptgen.models import ScriptVersion
from apps.scriptgen.serializers import ScriptGenerationSubmissionSerializer, ScriptVersionReviewSerializer
from apps.scriptgen.service.script_generation_service import ScriptGenerationService
from apps.testcase.models import TestCase
from apps.testsuite.models import TestDesignJob, TestSuite
from apps.testsuite.serializers import RequirementSubmissionSerializer
from apps.testsuite.service.test_design_service import TestDesignService
from apps.user.models import User


def _build_request_payload(request):
    payload = {}
    for key, value in request.POST.items():
        if key == "csrfmiddlewaretoken":
            continue
        if value != "":
            payload[key] = value
    for key, uploaded_file in request.FILES.items():
        if uploaded_file:
            payload[key] = uploaded_file
    return payload


def _flatten_errors(serializer):
    messages_list = []
    for field, errors in serializer.errors.items():
        label = "non_field_errors" if field == "non_field_errors" else field
        for error in errors:
            messages_list.append(f"{label}: {error}")
    return "; ".join(messages_list)


def _build_workbench_url(active="", **params):
    base = reverse("project-workbench")
    qs = {}
    if active:
        qs["active"] = active
    qs.update(params)
    if qs:
        return f"{base}?{urlencode(qs)}"
    return base


def _resolve_selected_design_job(request, design_jobs):
    job_id = request.GET.get("design_job_id")
    if job_id:
        try:
            return TestDesignJob.objects.select_related("project", "source_document").get(id=job_id)
        except TestDesignJob.DoesNotExist:
            pass
    return design_jobs[0] if design_jobs else None


def _resolve_selected_design_testcases(selected_design_job):
    if not selected_design_job:
        return []
    return list(
        TestCase.objects.select_related("suite", "suite__module")
        .filter(suite__design_job=selected_design_job)
        .order_by("id")
    )


def _resolve_selected_script_version(request, script_versions):
    version_id = request.GET.get("script_version_id")
    if version_id:
        try:
            return ScriptVersion.objects.select_related("script_file__suite", "script_file__project").get(id=version_id)
        except ScriptVersion.DoesNotExist:
            pass
    return script_versions[0] if script_versions else None


def _resolve_selected_execution(request, executions):
    execution_id = request.GET.get("execution_id")
    if execution_id:
        try:
            return Execution.objects.select_related("suite", "script_version__script_file").get(id=execution_id)
        except Execution.DoesNotExist:
            pass
    return executions[0] if executions else None


def _build_workbench_context(request, extra_context=None):
    extra_context = extra_context or {}
    projects = list(Project.objects.order_by("id"))
    users = list(User.objects.order_by("id"))
    design_jobs = list(TestDesignJob.objects.select_related("project", "source_document", "created_by").order_by("-id")[:8])
    suites = list(TestSuite.objects.select_related("project", "module", "source_document").order_by("-id")[:12])
    script_versions = list(ScriptVersion.objects.select_related("script_file__suite", "script_file__project", "created_by").order_by("-id")[:10])
    executions = list(Execution.objects.select_related("suite", "script_version__script_file").order_by("-id")[:10])
    reports = list(Report.objects.select_related("execution").order_by("-id")[:10])

    selected_design_job = _resolve_selected_design_job(request, design_jobs)
    selected_design_testcases = _resolve_selected_design_testcases(selected_design_job)
    selected_script_version = _resolve_selected_script_version(request, script_versions)
    selected_execution = _resolve_selected_execution(request, executions)
    selected_report = None

    if selected_execution:
        selected_report = Report.objects.select_related("execution").filter(execution=selected_execution).first()

    context = {
        "projects": projects,
        "users": users,
        "design_jobs": design_jobs,
        "suites": suites,
        "script_versions": script_versions,
        "executions": executions,
        "reports": reports,
        "selected_design_job": selected_design_job,
        "selected_design_testcases": selected_design_testcases,
        "selected_script_version": selected_script_version,
        "selected_execution": selected_execution,
        "selected_report": selected_report,
        "review_choices": ScriptVersion.REVIEW_CHOICES,
    }
    context.update(extra_context)
    return context


def workbench(request):
    return render(request, "workbench.html", _build_workbench_context(request))


@require_POST
def submit_requirement_workbench(request):
    payload = _build_request_payload(request)
    serializer = RequirementSubmissionSerializer(data=payload)
    if not serializer.is_valid():
        messages.error(request, _flatten_errors(serializer))
        return render(
            request,
            "workbench.html",
            _build_workbench_context(request, {"requirement_form_data": request.POST, "active_section": "requirement"}),
            status=400,
        )

    payload = dict(serializer.validated_data)
    run_async = payload.pop("run_async", False)
    # ID 转为 ORM 对象
    payload["project"] = get_object_or_404(Project, id=payload.pop("project_id"))
    if payload.get("created_by_id"):
        payload["created_by"] = get_object_or_404(User, id=payload.pop("created_by_id"))
    else:
        payload.pop("created_by_id", None)
    if payload.get("source_document_id"):
        payload["source_document"] = get_object_or_404(SourceDocument, id=payload.pop("source_document_id"))
    else:
        payload.pop("source_document_id", None)

    try:
        if run_async or not settings.CELERY_TASK_ALWAYS_EAGER:
            result = TestDesignService.enqueue_requirement_document(**payload)
            messages.success(request, f"需求链路已提交，任务编号为 {result['job_id']}。")
            return redirect(_build_workbench_url(design_job_id=result["job_id"], active="requirement"))
        result = TestDesignService.submit_requirement_document(**payload)
    except Exception as exc:
        messages.error(request, f"需求文档提交失败: {exc}")
        return render(
            request,
            "workbench.html",
            _build_workbench_context(request, {"requirement_form_data": request.POST, "active_section": "requirement"}),
            status=500,
        )

    summary = result["summary"]
    messages.success(
        request,
        f"需求链路完成：生成 {summary['module_count']} 个模块，{summary['suite_count']} 个测试集，{summary['testcase_count']} 条测试用例。",
    )
    return redirect(_build_workbench_url(design_job_id=result["job"]["id"], active="requirement"))


@require_POST
def submit_script_generation_workbench(request):
    payload = _build_request_payload(request)
    serializer = ScriptGenerationSubmissionSerializer(data=payload)
    if not serializer.is_valid():
        messages.error(request, _flatten_errors(serializer))
        return render(
            request,
            "workbench.html",
            _build_workbench_context(request, {"script_form_data": request.POST, "active_section": "scriptgen"}),
            status=400,
        )

    payload = dict(serializer.validated_data)
    run_async = payload.pop("run_async", False)

    try:
        if run_async or not settings.CELERY_TASK_ALWAYS_EAGER:
            result = ScriptGenerationService.enqueue_generation_request(**payload)
            messages.success(request, f"脚本生成任务已提交，任务编号为 {result['job_id']}。")
            return redirect(_build_workbench_url(active="scriptgen", script_generation_job_id=result["job_id"]))
        result = ScriptGenerationService.submit_generation_request(**payload)
    except Exception as exc:
        messages.error(request, f"脚本生成失败: {exc}")
        return render(
            request,
            "workbench.html",
            _build_workbench_context(request, {"script_form_data": request.POST, "active_section": "scriptgen"}),
            status=500,
        )

    messages.success(request, "脚本生成完成。")
    return redirect(_build_workbench_url(script_version_id=result.get("summary", {}).get("script_version_id") or "", active="scriptgen"))


@require_POST
def review_script_version_workbench(request):
    payload = _build_request_payload(request)
    serializer = ScriptVersionReviewSerializer(data=payload)
    if not serializer.is_valid():
        messages.error(request, _flatten_errors(serializer))
        return redirect(_build_workbench_url(active="scriptgen"))

    try:
        version = ScriptVersion.objects.get(id=serializer.validated_data["version_id"])
        ScriptGenerationService.review_script_version(
            script_version=version,
            review_status=serializer.validated_data["review_status"],
            content=serializer.validated_data.get("content", ""),
            change_summary=serializer.validated_data.get("change_summary", ""),
        )
        messages.success(request, "审核结果已保存。")
    except ScriptVersion.DoesNotExist:
        messages.error(request, "脚本版本不存在。")
    except Exception as exc:
        messages.error(request, f"审核失败: {exc}")
    return redirect(_build_workbench_url(active="scriptgen"))


@require_POST
def execute_script_version_workbench(request):
    version_id = request.POST.get("version_id")
    if not version_id:
        messages.error(request, "缺少 version_id 参数。")
        return redirect(_build_workbench_url(active="scriptgen"))

    try:
        version = ScriptVersion.objects.get(id=version_id)
        result = {}
        result = RunService.execute_script(script_version=version, suite=version.script_file.suite)
        messages.success(request, f"脚本执行已提交，执行ID: {result.get('execution_id', '')}。")
    except ScriptVersion.DoesNotExist:
        messages.error(request, "脚本版本不存在。")
    except Exception as exc:
        messages.error(request, f"执行失败: {exc}")
    return redirect(_build_workbench_url(active="scriptgen", execution_id=result.get("execution_id", "")))


def download_design_job_workbench(request, design_job_id):
    job = get_object_or_404(TestDesignJob, id=design_job_id)
    xlsx_bytes = DesignJobXlsxExporter.build_workbook(job)
    response = HttpResponse(xlsx_bytes, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    title = job.source_document.title if job.source_document and job.source_document.title else f"design_job_{design_job_id}"
    safe_title = "".join(ch if ch not in '\\/:*?"<>|' else "_" for ch in title).strip() or f"design_job_{design_job_id}"
    response["Content-Disposition"] = f'attachment; filename="{safe_title}_testcases.xlsx"'
    return response


def download_report_workbench(request, execution_id):
    execution = get_object_or_404(Execution, id=execution_id)
    zip_bytes = b""
    response = HttpResponse(zip_bytes, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="report_{execution_id}.zip"'
    return response
