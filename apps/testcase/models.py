from django.db import models
from apps.documents.models import SourceDocument
from apps.testsuite.models import TestSuite
from apps.user.models import User

class TestCase(models.Model):
    REVIEW_DRAFT='draft';REVIEW_PENDING='pending_review';REVIEW_APPROVED='approved';REVIEW_REJECTED='rejected'
    REVIEW_CHOICES=[(REVIEW_DRAFT,'Draft'),(REVIEW_PENDING,'Pending Review'),(REVIEW_APPROVED,'Approved'),(REVIEW_REJECTED,'Rejected')]

    id = models.BigAutoField(primary_key=True)
    suite = models.ForeignKey(TestSuite, on_delete=models.CASCADE, related_name='test_cases', null=True, blank=True)
    source_document = models.ForeignKey(SourceDocument, on_delete=models.SET_NULL, related_name='test_cases', null=True, blank=True)
    name = models.CharField(max_length=100, verbose_name='Test case name')
    description = models.TextField(blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_test_cases')
    preconditions = models.TextField(blank=True, default='')
    steps = models.TextField(blank=True, default='')
    expected_result = models.TextField(blank=True, default='')
    related_tables = models.CharField(max_length=500, blank=True, null=True, default='', verbose_name='关联数据表')
    related_fields = models.CharField(max_length=500, blank=True, null=True, default='', verbose_name='关联字段')
    review_status = models.CharField(max_length=20, choices=REVIEW_CHOICES, default=REVIEW_DRAFT)
    case_path = models.CharField(max_length=500, default='', blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    class Meta: verbose_name='Test case'; verbose_name_plural='Test cases'; ordering=['-create_time']
    def __str__(self): return self.name
