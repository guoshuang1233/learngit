from django.urls import path
from .api.user_api import UserViewSet
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
urlpatterns = router.urls
