from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Team


@receiver(post_migrate)
def create_public_group(sender, **kwargs):
    # Ensure the 'PUBLIC' and 'ADMIN' teams are created if they don't exist
    Team.objects.get_or_create(
        name="PUBLIC", defaults={"description": "The default Public Team"}
    )
    Team.objects.get_or_create(
        name="ADMIN", defaults={"description": "The default Admin Team"}
    )
