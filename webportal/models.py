import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models

from typing import Any


def generate_short_uid(_model_type, _prefix: str) -> str:
    """Generates a short (12-character) UID string. ie: 'mat6af2fd74'."""
    while True:
        _prefix = (_prefix.lower() + "___")[:3]
        uid = _prefix + str(int(uuid.uuid4().time_low))[2:]
        if not _model_type.objects.filter(uid=uid).exists():
            return uid


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
    uid = models.CharField(null=True, blank=True, max_length=12)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255, null=False, blank=False)
    conductivity = models.FloatField(null=False, blank=False, default=1.0)
    emissivity = models.FloatField(null=False, blank=False, default=0.9)
    source = models.CharField(max_length=255, null=True, blank=True)
    comments = models.TextField(max_length=255, null=True, blank=True)
    color_argb = models.CharField(
        max_length=16, null=False, blank=False, default="255,255,255,255"
    )
    category = models.ForeignKey(
        MaterialCategory, null=True, blank=True, on_delete=models.CASCADE
    )

    def save(self, *args, **kwargs):
        # -- Generate the UID if it does not exist
        if not self.uid:
            self.uid = generate_short_uid(Material, "mat")

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
    uid = models.CharField(null=True, blank=True, max_length=12)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
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

    def add_new_layer(self) -> "Layer":
        """Add a new layer to the assembly."""
        layer = Layer.new_layer_with_single_segment(assembly=self)
        # .objects.create(assembly=self, thickness=1.0)
        self.layer_id_order.append(layer.id)
        self.save()
        return layer

    def save(self, *args, **kwargs) -> None:
        # -- Generate the UID if it does not exist
        if not self.uid:
            self.uid = generate_short_uid(Assembly, "asm")
        super().save(*args, **kwargs)

    @property
    def layers(self) -> models.QuerySet["Layer"]:
        return self.layer_set.all()  # type: ignore

    def __str__(self) -> str:
        return self.name


class Layer(models.Model):
    uid = models.CharField(null=True, blank=True, max_length=12)
    assembly = models.ForeignKey(
        Assembly, on_delete=models.CASCADE, related_name="layers"
    )
    thickness = models.FloatField()
    segment_id_order = models.JSONField(default=list)

    def save(self, *args, **kwargs) -> None:
        # -- Generate the UID if it does not exist
        if not self.uid:
            self.uid = generate_short_uid(Assembly, "lyr")
        super().save(*args, **kwargs)

    @property
    def id(self) -> int:
        return self.id

    @property
    def segments(self) -> models.QuerySet["LayerSegment"]:
        return self.segments_set.all()  # type: ignore

    def get_ordered_segments(self):
        """Return segments ordered according to the segment_id_order field."""
        # Sort segments by the order in layer_order
        segments = {segment.id: segment for segment in self.segments.all()}
        return [
            segments[layer_id]
            for layer_id in self.segment_id_order
            if layer_id in segments
        ]

    @classmethod
    def new_layer_with_single_segment(cls, assembly: Assembly) -> "Layer":
        """Create a new layer with a single segment."""
        layer = cls.objects.create(assembly=assembly, thickness=1.0)
        segment = LayerSegment.objects.create(layer=layer)
        layer.segment_id_order.append(segment.id)
        layer.save()
        return layer

    def __str__(self) -> str:
        return f"{self.thickness} mm"


class LayerSegment(models.Model):
    uid = models.CharField(null=True, blank=True, max_length=12)
    layer = models.ForeignKey(
        Layer, on_delete=models.CASCADE, null=True, related_name="segments"
    )
    material = models.ForeignKey(Material, on_delete=models.CASCADE, null=True)

    @property
    def id(self) -> int:
        return self.id

    def save(self, *args, **kwargs) -> None:
        # -- Generate the UID if it does not exist
        if not self.uid:
            self.uid = generate_short_uid(LayerSegment, "seg")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"[layer-{self.layer}]: {self.material}"
