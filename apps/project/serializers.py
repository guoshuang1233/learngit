from rest_framework import serializers
from apps.project.models import Project
class ProjectSerializer(serializers.ModelSerializer):
    class Meta: model=Project; fields='__all__'
