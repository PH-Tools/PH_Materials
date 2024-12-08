from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class MaterialCategory(models.Model):
    MATERIAL_CATEGORIES = (
        ("IN", "Insulation"),
        ("WD", "Wood"),
        ("MN", "Masonry"),
        ("ST", "Stone"),
        ("CR", "Concrete"),
        ("FN", "Finish"),
        ("SS", "Stud Layer [Steel Stud]"),
        ("WS", "Stud Layer [Wood Stud]"),
        ("AH", "Air [Horizontal Heat Flow]"),
        ("AU", "Air [Upward Heat Flow]"),
        ("AD", "Air [Downward Heat Flow]"),
        ("MT", "Metal"),
    )
    category = models.CharField(
        choices=MATERIAL_CATEGORIES, max_length=2, null=False, blank=False, unique=True
    )

    @property
    def display_name(self) -> str:
        return dict(self.MATERIAL_CATEGORIES).get(self.category, self.category)

    @classmethod
    def get_category_display_name(cls, code: str) -> str | None:
        return dict(cls.MATERIAL_CATEGORIES).get(code.upper().strip())

    @classmethod
    def get_category_code(cls, display_name: str) -> str | None:
        label_to_code = {v: k for k, v in cls.MATERIAL_CATEGORIES}
        return label_to_code.get(display_name.strip(), None)

    class Meta:
        verbose_name_plural = "Material Categories"
        ordering = ["category"]

    def __str__(self) -> str:
        return dict(self.MATERIAL_CATEGORIES).get(self.category, self.category)


class Material(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    conductivity = models.FloatField(null=False, blank=False, default=1.0)
    emissivity = models.FloatField(null=False, blank=False, default=0.9)
    source = models.CharField(max_length=255, null=True, blank=True)
    comments = models.TextField(max_length=255, null=True, blank=True)
    color_argb = models.CharField(
        max_length=16, null=False, blank=False, default="255,255,255,255"
    )
    category = models.ForeignKey(
        MaterialCategory, on_delete=models.CASCADE, null=False, blank=False
    )

    def save(self, *args, **kwargs):
        # -- Ensure the Category is one of the allowed ones
        allowed_categories = dict(MaterialCategory.MATERIAL_CATEGORIES)
        if not self.category:
            raise ValueError("Category is required")

        if self.category.category not in allowed_categories.keys():
            raise ValueError(f"Invalid category: {self.category}")

        if self.category.display_name not in allowed_categories.values():
            raise ValueError(f"Invalid category: {self.category}")

        # -- Check if the category exists in the database, if not, create it
        category, created = MaterialCategory.objects.get_or_create(
            category=self.category.category
        )
        self.category = category

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        # Order by Category Name (lookup), then by Material Name
        ordering = ["category", "name"]
