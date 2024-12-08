import random
from faker import Faker
from django.core.management.base import BaseCommand
from webportal.models import Material, MaterialCategory


class Command(BaseCommand):
    help = """
        Delete all the materials from the database.
        To run: 'python manage.py delete_materials'
    """

    def handle(self, *args, **kwargs):
        num_materials = Material.objects.count()
        Material.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(f"{num_materials} materials deleted successfully.")
        )
