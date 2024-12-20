import logging
import os

import dotenv
from django.core.exceptions import ImproperlyConfigured
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .models import Team, User

# Load environment variables from .env file
dotenv.load_dotenv()
SUPER_USER_PASSWORD = os.getenv("SUPER_USER_PASSWORD")

logger = logging.getLogger(__name__)

if not SUPER_USER_PASSWORD:
    raise ImproperlyConfigured("SUPER_USER_PASSWORD environment variable is not set.")


@receiver(post_migrate)
def create_public_group(sender, **kwargs):
    """Ensure there is always a PUBLIC and an ADMIN team."""
    try:
        public_team, created = Team.objects.get_or_create(
            name="PUBLIC", defaults={"description": "The default Public Team"}
        )
        if created:
            logger.info("Created 'PUBLIC' team.")

        admin_team, created = Team.objects.get_or_create(
            name="ADMIN", defaults={"description": "The default Admin Team"}
        )
        if created:
            logger.info("Created 'ADMIN' team.")
    except Exception as e:
        logger.error(f"Error creating teams: {e}")


@receiver(post_migrate)
def create_super_user(sender, **kwargs):
    """Ensure there is always a superuser with username 'admin'."""
    try:
        if not User.objects.filter(username="admin").exists():
            super_user = User.objects.create_superuser(
                "admin", "info@bldgtyp.com", SUPER_USER_PASSWORD
            )
            logger.info("Created superuser 'admin'.")
            super_user.is_paid_user = True
            super_user.team, created = Team.objects.get_or_create(
                name="ADMIN", defaults={"description": "The default Admin Team"}
            )
            super_user.save()
        else:
            logger.info("Superuser 'admin' already exists.")
    except Exception as e:
        logger.error(f"Error creating superuser: {e}")
