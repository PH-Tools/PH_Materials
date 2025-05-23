import pytest

from webportal.factories import MaterialFactory, UserFactory


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def materials():
    return MaterialFactory.create_batch(20)


@pytest.fixture
def user_materials():
    user = UserFactory()
    return MaterialFactory.create_batch(20, user=user)


@pytest.fixture
def material_dict_params(user):
    material = MaterialFactory.create(user=user)
    return {
        "name": material.name,
        "conductivity": material.conductivity,
        "emissivity": material.emissivity,
        "source": material.source,
        "comments": material.comments,
        "color_argb": material.color_argb,
        "category": material.category_id,
    }
