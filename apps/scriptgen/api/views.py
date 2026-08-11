from rest_framework.viewsets import ModelViewSet
from apps.scriptgen.models import ScriptFile, ScriptGenerationJob, ScriptVersion
from rest_framework.permissions import AllowAny
class ScriptFileViewSet(ModelViewSet): queryset=ScriptFile.objects.all(); permission_classes=[AllowAny]
class ScriptGenerationJobViewSet(ModelViewSet): queryset=ScriptGenerationJob.objects.all(); permission_classes=[AllowAny]
class ScriptVersionViewSet(ModelViewSet): queryset=ScriptVersion.objects.all(); permission_classes=[AllowAny]
