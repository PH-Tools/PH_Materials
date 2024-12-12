from django.core.management.base import BaseCommand

from webportal.models import Cell


class Command(BaseCommand):
    help = """
        Delete all the Assembly cells from the database.
        To run: 'python manage.py delete_assembly_cells'
    """

    def handle(self, *args, **kwargs):
        num_assemblies = Cell.objects.count()
        Cell.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(f"{num_assemblies} assembly-cells deleted successfully.")
        )
