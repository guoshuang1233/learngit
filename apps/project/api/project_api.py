from rest_framework.viewsets import ModelViewSet
from apps.project.models import Project
from rest_framework.permissions import AllowAny
class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.all(); permission_classes = [AllowAny]
