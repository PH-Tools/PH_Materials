from django.core.management.base import BaseCommand

from webportal.models import User


class Command(BaseCommand):
    help = """
        Delete all the assemblies from the database.
        To run: 'python manage.py delete_teams_and_users'
    """

    def handle(self, *args, **kwargs):
        num_users = User.objects.filter(is_superuser=False)
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(
            self.style.SUCCESS(f"{num_users} users deleted successfully.")
        )
