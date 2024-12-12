import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from typing import Any


# ---------------------------------------------------------------------------------------
# -- Users


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


# ---------------------------------------------------------------------------------------
# -- Materials


class Material(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    unique_id = models.CharField(
        max_length=6, unique=True, null=False, blank=False, default=uuid.uuid4().hex[:6]
    )
    name = models.CharField(max_length=255, null=False, blank=False)
    conductivity = models.FloatField(null=False, blank=False, default=1.0)
    emissivity = models.FloatField(null=False, blank=False, default=0.9)
    source = models.CharField(max_length=255, null=True, blank=True)
    comments = models.TextField(max_length=255, null=True, blank=True)
    color_argb = models.CharField(
        max_length=16, null=False, blank=False, default="255,255,255,255"
    )
    category = models.ForeignKey(MaterialCategory, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        # -- Make sure that the Material has a hex-id and that it is unique
        if not self.unique_id:
            self.unique_id = uuid.uuid4().hex[:6]

        while Material.objects.filter(unique_id=self.unique_id).exists():
            self.unique_id = uuid.uuid4().hex[:6]

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


# ---------------------------------------------------------------------------------------
# -- Assemblies


class Assembly(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    name = models.CharField(max_length=100, default="assembly")
    created_at = models.DateTimeField(auto_now_add=True)
    layer_id_order = models.JSONField(default=list)

    def get_ordered_layers(self) -> list["Layer"]:
        """Return layers ordered according to the layer_id_order field."""
        # Sort layers by the order in layer_order
        layers = {layer.id: layer for layer in self.layers.all()}
        return [
            layers[layer_id] for layer_id in self.layer_id_order if layer_id in layers
        ]

    def delete_layer(self, layer_pk: int) -> None:
        """Delete a layer from the assembly."""
        if layer_pk in self.layer_id_order:
            self.layer_id_order.remove(layer_pk)
            self.save()

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        layers = Layer.objects.filter(assembly=self)
        if not layers.exists():
            new_layer = Layer.objects.create(assembly=self, thickness=1.0)
            self.layer_id_order.append(new_layer.id)

    @property
    def layers(self) -> models.QuerySet["Layer"]:
        return self.layer_set.all()  # type: ignore

    def __str__(self) -> str:
        return self.name


class Layer(models.Model):
    assembly = models.ForeignKey(
        Assembly, on_delete=models.CASCADE, related_name="layers"
    )
    thickness = models.FloatField()

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        cells = Cell.objects.filter(layer=self)
        if not cells.exists():
            Cell.objects.create(layer=self)

    @property
    def id(self) -> int:
        return self.id

    def __str__(self) -> str:
        return f"{self.thickness} mm"


class Cell(models.Model):
    layer = models.ForeignKey(
        Layer, on_delete=models.CASCADE, null=True, related_name="cells"
    )
    value = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"[layer-{self.layer}]: {self.value}"
