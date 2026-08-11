from django.db import models
from apps.execution.models import Execution

class Report(models.Model):
    id = models.BigAutoField(primary_key=True)
    execution = models.ForeignKey(Execution, on_delete=models.CASCADE, related_name='reports')
    report_url = models.URLField(blank=True, default='')
    summary = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-created_at']
