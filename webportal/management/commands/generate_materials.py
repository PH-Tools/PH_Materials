import random
from faker import Faker
from django.core.management.base import BaseCommand
from webportal.models import Material, MaterialCategory


class Command(BaseCommand):
    help = """
        Generates 20 random Material objects in the database for testing. 
        To run: 'python manage.py generate_materials'
    """

    def handle(self, *args, **kwargs):
        fake = Faker()

        # -- Ensure all the Categories are present in the database
        for category in MaterialCategory.MATERIAL_CATEGORIES:
            MaterialCategory.objects.get_or_create(category=category[0])

        # -- Build 20 random Material objects in the database
        categories = MaterialCategory.objects.all()
        for _ in range(20):
            Material.objects.create(
                name=fake.word(),
                conductivity=random.uniform(0.1, 10.0),
                emissivity=random.uniform(0.1, 1.0),
                source=fake.text(max_nb_chars=100),
                comments=fake.text(max_nb_chars=100),
                color_argb=f"{random.randint(0, 255)},{random.randint(0, 255)},{random.randint(0, 255)},{random.randint(0, 255)}",
                category=random.choice(categories),
            )
