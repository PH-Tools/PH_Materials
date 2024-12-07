import pytest
from webportal.models import User, Material


@pytest.mark.django_db
def test_queryset_get_all(materials):
    qs = Material.objects.all()
    assert len(qs) == 20
