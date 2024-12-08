import factory
from webportal.models import User, Material, MaterialCategory


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    username = factory.Sequence(lambda n: f"user{n}")


class MaterialCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MaterialCategory

    category = factory.Faker(
        "random_element", elements=[x[0] for x in MaterialCategory.MATERIAL_CATEGORIES]
    )

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # Use get_or_create to avoid creating duplicate categories
        category, created = model_class.objects.get_or_create(**kwargs)
        return category


class MaterialFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Material

    name = factory.Faker("word")
    conductivity = factory.Faker("pyfloat", positive=True)
    emissivity = factory.Faker("pyfloat", positive=True, max_value=1.0)
    source = factory.Faker("word")
    comments = factory.Faker("word")
    color_argb = factory.Faker("word")
    category = factory.SubFactory(MaterialCategoryFactory)
