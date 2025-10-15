from django.core.management.base import BaseCommand
from resources.models import Project, ProjectAccess, Role
from django.contrib.auth.models import User


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("user", type=str)
        parser.add_argument("project", type=str)
        parser.add_argument("role", type=str)

    def handle(self, *args, **options):
        user = User.objects.get(username=options["user"])
        project = Project.objects.get(label=options["project"])
        role = Role.objects.get(project=project, label=options["role"])
        ProjectAccess.objects.get_or_create(role=role, project=project, user=user)
