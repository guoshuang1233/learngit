from django.conf import settings
from django.db import transaction

from apps.project.models import Project


DEFAULT_PROJECT_NAME = getattr(settings, "DEFAULT_PROJECT_NAME", "AI Test Platform")


def get_or_create_default_project():
    """
    Return an existing project if one exists, otherwise create a default workspace.
    This keeps the two main submission flows usable even when the UI does not
    explicitly provide a project.
    """
    project = Project.objects.order_by("id").first()
    if project:
        return project

    with transaction.atomic():
        project = Project.objects.order_by("id").first()
        if project:
            return project
        return Project.objects.create(
            name=DEFAULT_PROJECT_NAME,
            description="Auto-created default project for AI test generation flows",
            creator=None,
        )


def resolve_project_or_default(project_ref=None):
    """
    Resolve a project reference from an id/object; fall back to the default workspace.
    """
    if isinstance(project_ref, Project):
        return project_ref

    if project_ref in (None, "", "null"):
        return get_or_create_default_project()

    try:
        project_id = int(project_ref)
    except (TypeError, ValueError):
        return get_or_create_default_project()

    project = Project.objects.filter(id=project_id).first()
    return project or get_or_create_default_project()

