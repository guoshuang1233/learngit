from django.db import models
from apps.project.models import Project
from apps.documents.models import SourceDocument
from apps.user.models import User

class BusinessModule(models.Model):
    id = models.BigAutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='business_modules')
    source_document = models.ForeignKey(SourceDocument, on_delete=models.SET_NULL, null=True, related_name='business_modules')
    design_job = models.ForeignKey('TestDesignJob', on_delete=models.CASCADE, null=True, related_name='modules')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    sort_order = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['sort_order']

class TestDesignJob(models.Model):
    STATUS_PENDING = 'pending'; STATUS_RUNNING = 'running'; STATUS_SUCCESS = 'success'; STATUS_FAILED = 'failed'
    STATUS_CHOICES = [(STATUS_PENDING,'Pending'),(STATUS_RUNNING,'Running'),(STATUS_SUCCESS,'Success'),(STATUS_FAILED,'Failed')]
    id = models.BigAutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='design_jobs')
    source_document = models.ForeignKey(SourceDocument, on_delete=models.SET_NULL, null=True, related_name='design_jobs')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    rule_text = models.TextField(blank=True, default='')
    raw_output = models.TextField(blank=True, default='')
    structured_result = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-created_at']

class TestSuite(models.Model):
    REVIEW_PENDING = 'pending_review'; REVIEW_APPROVED = 'approved'
    REVIEW_CHOICES = [(REVIEW_PENDING,'Pending'),(REVIEW_APPROVED,'Approved')]
    id = models.BigAutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='test_suites')
    module = models.ForeignKey(BusinessModule, on_delete=models.CASCADE, null=True, blank=True, related_name='test_suites')
    source_document = models.ForeignKey(SourceDocument, on_delete=models.SET_NULL, null=True, related_name='test_suites')
    design_job = models.ForeignKey(TestDesignJob, on_delete=models.CASCADE, null=True, related_name='test_suites')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True, default='')
    review_status = models.CharField(max_length=20, choices=REVIEW_CHOICES, default=REVIEW_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-created_at']
