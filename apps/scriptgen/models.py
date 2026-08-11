from django.db import models
from apps.project.models import Project
from apps.testsuite.models import TestSuite
from apps.documents.models import SourceDocument
from apps.user.models import User

class ScriptFile(models.Model):
    STATUS_DRAFT='draft';STATUS_PENDING_REVIEW='pending_review';STATUS_APPROVED='approved';STATUS_REJECTED='rejected'
    STATUS_CHOICES=[(STATUS_DRAFT,'Draft'),(STATUS_PENDING_REVIEW,'Pending Review'),(STATUS_APPROVED,'Approved'),(STATUS_REJECTED,'Rejected')]
    id = models.BigAutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    suite = models.ForeignKey(TestSuite, on_delete=models.CASCADE)
    generation_job = models.ForeignKey('ScriptGenerationJob', on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    current_version = models.ForeignKey('ScriptVersion', on_delete=models.SET_NULL, null=True, related_name='+')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ScriptGenerationJob(models.Model):
    STATUS_PENDING='pending';STATUS_RUNNING='running';STATUS_SUCCESS='success';STATUS_FAILED='failed'
    STATUS_CHOICES=[(STATUS_PENDING,'Pending'),(STATUS_RUNNING,'Running'),(STATUS_SUCCESS,'Success'),(STATUS_FAILED,'Failed')]
    id = models.BigAutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    suite = models.ForeignKey(TestSuite, on_delete=models.CASCADE, null=True)
    suite_document = models.ForeignKey(SourceDocument, on_delete=models.SET_NULL, null=True, related_name='script_jobs_suite')
    api_document = models.ForeignKey(SourceDocument, on_delete=models.SET_NULL, null=True, related_name='script_jobs_api')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    rule_text = models.TextField(blank=True, default='')
    raw_output = models.TextField(blank=True, default='')
    structured_result = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

class ScriptVersion(models.Model):
    SOURCE_AI='ai';SOURCE_MANUAL='manual'
    SOURCE_CHOICES=[(SOURCE_AI,'AI Generated'),(SOURCE_MANUAL,'Manual')]
    REVIEW_DRAFT='draft';REVIEW_PENDING='pending';REVIEW_APPROVED='approved';REVIEW_REJECTED='rejected'
    REVIEW_CHOICES=[(REVIEW_DRAFT,'Draft'),(REVIEW_PENDING,'Pending'),(REVIEW_APPROVED,'Approved'),(REVIEW_REJECTED,'Rejected')]
    id = models.BigAutoField(primary_key=True)
    script_file = models.ForeignKey(ScriptFile, on_delete=models.CASCADE, related_name='versions')
    version = models.IntegerField(default=1)
    content = models.TextField(blank=True, default='')
    rendered_path = models.CharField(max_length=500, blank=True, default='')
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_AI)
    review_status = models.CharField(max_length=20, choices=REVIEW_CHOICES, default=REVIEW_DRAFT)
    generation_rule = models.TextField(blank=True, default='')
    change_summary = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
