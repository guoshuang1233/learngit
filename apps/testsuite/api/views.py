from rest_framework.viewsets import ModelViewSet
from apps.testsuite.models import BusinessModule, TestDesignJob, TestSuite
from rest_framework.permissions import AllowAny
class BusinessModuleViewSet(ModelViewSet): queryset=BusinessModule.objects.all(); permission_classes=[AllowAny]
class TestDesignJobViewSet(ModelViewSet): queryset=TestDesignJob.objects.all(); permission_classes=[AllowAny]
class TestSuiteViewSet(ModelViewSet): queryset=TestSuite.objects.all(); permission_classes=[AllowAny]
