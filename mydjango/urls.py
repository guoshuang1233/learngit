"""
URL configuration for mydjango project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include("apps.user.urls")),
    path('api/', include("apps.project.urls")),
    path("api/", include("apps.testcase.urls")),
    path("api/", include("apps.testsuite.urls")),
    path("api/", include("apps.scriptgen.urls")),
    path("api/", include("apps.execution.urls")),
    path("api/", include("apps.report.urls")),
    path("api/", include("apps.documents.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
