import pytest
from webportal.models import User, Material, MaterialCategory


@pytest.mark.django_db
def test_material_categories_queryset_get_all(materials):
    qs = MaterialCategory.objects.all()
    category_codes = [code for code, _ in MaterialCategory.MATERIAL_CATEGORIES]
    for category_code in qs.values_list("category", flat=True):
        assert category_code in category_codes


@pytest.mark.django_db
def test_queryset_get_all(materials):
    qs = Material.objects.all()
    assert len(qs) == 20
