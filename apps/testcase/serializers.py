from rest_framework import serializers
from apps.testcase.models import TestCase

class TestCaseSerializer(serializers.ModelSerializer):
    class Meta: model=TestCase; fields='__all__'
