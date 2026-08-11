from django.db import models
from apps.project.models import Project
from apps.user.models import User

class SourceDocument(models.Model):
    DOC_TYPE_REQUIREMENT = 'requirement'
    DOC_TYPE_SUITE = 'suite'
    DOC_TYPE_API = 'api'
    DOC_TYPE_CHOICES = [(DOC_TYPE_REQUIREMENT,'Requirement'),(DOC_TYPE_SUITE,'Suite'),(DOC_TYPE_API,'API')]
    STATUS_UPLOADED = 'uploaded'; STATUS_PARSING = 'parsing'; STATUS_PARSED = 'parsed'; STATUS_FAILED = 'failed'
    STATUS_CHOICES = [(STATUS_UPLOADED,'Uploaded'),(STATUS_PARSING,'Parsing'),(STATUS_PARSED,'Parsed'),(STATUS_FAILED,'Failed')]

    id = models.BigAutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=300)
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES, default=DOC_TYPE_REQUIREMENT)
    source_file = models.FileField(upload_to='uploads/requirement_docs/', null=True, blank=True)
    extracted_text = models.TextField(blank=True, default='')
    parse_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_UPLOADED)
    parse_error = models.TextField(blank=True, default='')
    metadata = models.JSONField(null=True, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-created_at']
    def __str__(self): return self.title
