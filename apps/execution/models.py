from django.db import models
from apps.testsuite.models import TestSuite
from apps.scriptgen.models import ScriptVersion

class Execution(models.Model):
    STATUS_PENDING='pending';STATUS_RUNNING='running';STATUS_SUCCESS='success';STATUS_FAILED='failed'
    STATUS_CHOICES=[(STATUS_PENDING,'Pending'),(STATUS_RUNNING,'Running'),(STATUS_SUCCESS,'Success'),(STATUS_FAILED,'Failed')]
    id = models.BigAutoField(primary_key=True)
    suite = models.ForeignKey(TestSuite, on_delete=models.CASCADE, null=True)
    script_version = models.ForeignKey(ScriptVersion, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    result_dir = models.CharField(max_length=500, blank=True, default='')
    stdout = models.TextField(blank=True, default='')
    stderr = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-created_at']
