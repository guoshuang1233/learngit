from rest_framework import serializers
from apps.scriptgen.models import ScriptFile, ScriptGenerationJob, ScriptVersion

class ScriptFileSerializer(serializers.ModelSerializer):
    class Meta: model=ScriptFile; fields='__all__'

class ScriptGenerationJobSerializer(serializers.ModelSerializer):
    class Meta: model=ScriptGenerationJob; fields='__all__'

class ScriptVersionSerializer(serializers.ModelSerializer):
    class Meta: model=ScriptVersion; fields='__all__'

class ScriptGenerationSubmissionSerializer(serializers.Serializer):
    project_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    suite_id = serializers.IntegerField(required=False, allow_null=True)
    suite_document_id = serializers.IntegerField(required=False, allow_null=True)
    api_document_id = serializers.IntegerField(required=False, allow_null=True)
    created_by_id = serializers.IntegerField(required=False, allow_null=True)
    suite_title = serializers.CharField(required=False, allow_blank=True)
    api_title = serializers.CharField(required=False, allow_blank=True)
    suite_file = serializers.FileField(required=False, allow_null=True)
    api_file = serializers.FileField(required=False, allow_null=True)
    suite_text = serializers.CharField(required=False, allow_blank=True)
    api_text = serializers.CharField(required=False, allow_blank=True)
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
        if not Project.objects.filter(id=value).exists(): raise serializers.ValidationError('Project not found')
        return value

class ScriptVersionReviewSerializer(serializers.Serializer):
    version_id = serializers.IntegerField()
    review_status = serializers.CharField()
    content = serializers.CharField(required=False, allow_blank=True)
    change_summary = serializers.CharField(required=False, allow_blank=True)
