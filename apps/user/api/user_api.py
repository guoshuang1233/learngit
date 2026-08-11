from rest_framework.viewsets import ModelViewSet
from apps.user.models import User
from rest_framework.permissions import AllowAny
class UserViewSet(ModelViewSet):
    queryset = User.objects.all(); permission_classes = [AllowAny]
