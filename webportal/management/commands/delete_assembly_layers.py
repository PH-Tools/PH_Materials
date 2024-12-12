from django.core.management.base import BaseCommand

from webportal.models import Layer


class Command(BaseCommand):
    help = """
        Delete all the Assembly cells from the database.
        To run: 'python manage.py delete_assembly_layers'
    """

    def handle(self, *args, **kwargs):
        num_assemblies = Layer.objects.count()
        Layer.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"{num_assemblies} assembly-layers deleted successfully."
            )
        )
