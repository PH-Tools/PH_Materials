import pytest
from pytest_django.asserts import assertTemplateUsed
from django.urls import reverse
from webportal.models import MaterialCategory, Material, User


@pytest.mark.django_db
def test_material_category_filter(user, materials, client):
    client.force_login(user)

    # -- Get the first two Primary Keys of MaterialCategory
    category_primary_keys = MaterialCategory.objects.all()[:2].values_list(
        "pk", flat=True
    )

    # # -- Filter the Materials
    GET_params = {"category": category_primary_keys}
    response = client.get(reverse("materials-list"), GET_params)
    assert response.status_code == 200

    # -- All response items should be have a category in the allowed GET_params types
    qs = response.context["filter"].qs
    assert len(qs) > 0
    for material in qs:
        assert material.category.pk in category_primary_keys


@pytest.mark.django_db
def test_add_material_request(user, material_dict_params, client):
    client.force_login(user)
    response = client.post(reverse("create-material"), material_dict_params)
    assert response.status_code == 200

    material_count = Material.objects.all().count()

    header = {"http_hx-request": "true"}
    response = client.post(reverse("create-material"), material_dict_params, **header)

    assert Material.objects.all().count() == material_count + 1
    assertTemplateUsed(response, "webportal/partials/material-success.html")


@pytest.mark.django_db
def test_cannot_add_material_with_bad_name(user, material_dict_params, client):
    client.force_login(user)
    response = client.post(reverse("create-material"), material_dict_params)
    assert response.status_code == 200
    user_material_count = Material.objects.all().count()

    # -- No Name
    material_dict_params["name"] = ""
    header = {"http_hx-request": "true"}
    response = client.post(reverse("create-material"), material_dict_params, **header)

    assert Material.objects.all().count() == user_material_count
    assertTemplateUsed(response, "webportal/partials/create-material.html")
    assert "HX-Retarget" in response.headers


@pytest.mark.django_db
def test_cannot_add_material_with_bad_conductivity(user, material_dict_params, client):
    client.force_login(user)
    response = client.post(reverse("create-material"), material_dict_params)
    assert response.status_code == 200
    user_material_count = Material.objects.all().count()

    # -- Less than 0.0
    material_dict_params["conductivity"] = -44.0
    header = {"http_hx-request": "true"}
    response = client.post(reverse("create-material"), material_dict_params, **header)

    assert Material.objects.all().count() == user_material_count
    assertTemplateUsed(response, "webportal/partials/create-material.html")
    assert "HX-Retarget" in response.headers


@pytest.mark.django_db
def test_cannot_add_material_with_bad_emissivity(user, material_dict_params, client):
    client.force_login(user)
    response = client.post(reverse("create-material"), material_dict_params)
    assert response.status_code == 200
    user_material_count = Material.objects.all().count()

    material_dict_params["emissivity"] = -44.0
    header = {"http_hx-request": "true"}
    response = client.post(reverse("create-material"), material_dict_params, **header)

    # -- Less than 0.0
    assert Material.objects.all().count() == user_material_count
    assertTemplateUsed(response, "webportal/partials/create-material.html")
    assert "HX-Retarget" in response.headers

    # -- Over 1.0
    material_dict_params["emissivity"] = 1.01
    header = {"http_hx-request": "true"}
    response = client.post(reverse("create-material"), material_dict_params, **header)

    assert Material.objects.all().count() == user_material_count
    assertTemplateUsed(response, "webportal/partials/create-material.html")
    assert "HX-Retarget" in response.headers


@pytest.mark.django_db
def test_update_material_request(user, material_dict_params, client):
    client.force_login(user)
    assert Material.objects.all().count() == 1

    material = Material.objects.first()
    assert material is not None

    material_dict_params["conductivity"] = 1.23
    material_dict_params["emissivity"] = 0.5

    header = {"http_hx-request": "true"}
    post_request_url = reverse("update-material", kwargs={"pk": material.pk})
    response = client.post(post_request_url, material_dict_params, **header)

    assert response.status_code == 200
    assert Material.objects.all().count() == 1
    material = Material.objects.first()
    assert material is not None
    assert material.conductivity == 1.23
    assert material.emissivity == 0.5


@pytest.mark.django_db
def test_delete_material_request(user, material_dict_params, client):
    client.force_login(user)
    assert Material.objects.all().count() == 1

    material = Material.objects.first()
    assert material is not None
    client.delete(reverse("delete-material", kwargs={"pk": material.pk}))

    assert Material.objects.all().count() == 0
