from django.core.management.base import BaseCommand

from webportal.models import LayerSegment


class Command(BaseCommand):
    help = """
        Delete all the Assembly cells from the database.
        To run: 'python manage.py delete_assembly_segments'
    """

    def handle(self, *args, **kwargs):
        num_assemblies = LayerSegment.objects.count()
        LayerSegment.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"{num_assemblies} assembly-segments deleted successfully."
            )
        )
