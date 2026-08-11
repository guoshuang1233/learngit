from rest_framework import serializers
from apps.testsuite.models import BusinessModule, TestDesignJob, TestSuite

class BusinessModuleSerializer(serializers.ModelSerializer):
    class Meta: model=BusinessModule; fields='__all__'

class TestDesignJobSerializer(serializers.ModelSerializer):
    class Meta: model=TestDesignJob; fields='__all__'

class TestSuiteSerializer(serializers.ModelSerializer):
    class Meta: model=TestSuite; fields='__all__'

class RequirementSubmissionSerializer(serializers.Serializer):
    project_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    created_by_id = serializers.IntegerField(required=False, allow_null=True)
    source_document_id = serializers.IntegerField(required=False, allow_null=True)
    title = serializers.CharField(required=False, allow_blank=True)
    source_file = serializers.FileField(required=False, allow_null=True)
    extracted_text = serializers.CharField(required=False, allow_blank=True)
    rule_text = serializers.CharField(required=False, allow_blank=True)
    run_async = serializers.BooleanField(required=False, default=False)
    def validate_project_id(self, value):
        if value in (None, ""):
            return None
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise serializers.ValidationError("Project id must be an integer")
        from apps.project.models import Project
        if not Project.objects.filter(id=value).exists():
            raise serializers.ValidationError("Project not found")
        return value
    def validate_created_by_id(self, value):
        if value:
            from apps.user.models import User
            if not User.objects.filter(id=value).exists(): raise serializers.ValidationError('User not found')
        return value
