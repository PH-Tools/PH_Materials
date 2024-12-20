from django.core.management.base import BaseCommand

from webportal.models import Assembly


class Command(BaseCommand):
    help = """
        Delete all the assemblies from the database.
        To run: 'python manage.py delete_assemblies'
    """

    def handle(self, *args, **kwargs):
        num_assemblies = Assembly.objects.count()
        Assembly.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(f"{num_assemblies} assemblies deleted successfully.")
        )
