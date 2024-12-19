import uuid

from django.contrib.auth.models import AbstractUser, Group
from django.db import models


def generate_short_uid(_model_type, _prefix: str) -> str:
    """Generates a short (12-character) UID string. ie: 'mat6af2fd74'."""
    while True:
        _prefix = (_prefix.lower() + "___")[:3]
        uid = _prefix + str(int(uuid.uuid4().time_low))[2:]
        if not _model_type.objects.filter(uid=uid).exists():
            return uid


# ---------------------------------------------------------------------------------------
# -- Users


class Team(Group):
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "User",
        related_name="created_teams",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    @property
    def members(self) -> models.QuerySet["User"]:
        return self.members.all()

    def update_name(self, new_name: str):
        """Update the name of the Team."""
        self.name = new_name
        self.save()

    def __str__(self):
        return f"{self.name} - {self.description}"


class User(AbstractUser):
    team = models.ForeignKey(
        Team,
        related_name="members",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    is_paid_user = models.BooleanField(default=False)
    team_invite = models.ForeignKey(
        Team,
        related_name="invited_users",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    @property
    def team_members(self) -> models.QuerySet["User"]:
        if self.team:
            return self.team.members.all()
        else:
            return User.objects.none()

    def is_team_manager(self) -> bool:
        """Return True if this User is the Manager of their Team."""
        if not self.team or not self.team.created_by:
            return False
        return self.pk == self.team.created_by.pk

    def is_project_manager(self, project: "Project") -> bool:
        """Return True if this User is the Manager of the given Project."""
        if not project.create_by:
            return False
        return self.pk == project.create_by.pk

    def change_user_status(self, is_paid_user: bool):
        """Change the status of User (paid or free). When status is changed, this also changes their team."""
        if is_paid_user:
            if self.team is None or self.team.name == "PUBLIC":
                # -- Paid users get a default Team with their username
                self.team, created = Team.objects.get_or_create(
                    name=self.username, created_by=self
                )
        else:
            # -- Assign all free users to the 'PUBLIC' team by default
            self.team, created = Team.objects.get_or_create(name="PUBLIC")
        self.is_paid_user = is_paid_user
        self.save()

    def invite_to_team(self, sender: "User"):
        """Register an invitation to join Team."""
        if sender.team:
            self.team_invite = sender.team
            self.save()

    def accept_team_invite(self):
        """Accept the invitation to join Team."""
        if self.team_invite:
            self.team = self.team_invite
            self.team_invite = None
            self.save()

    def reject_team_invite(self):
        """Reject the invitation to join Team."""
        self.team_invite = None
        self.save()

    def save(self, *args, **kwargs):
        if self.is_paid_user:
            if self.team is None:
                # -- Paid users get a default Team with their username
                self.team, created = Team.objects.get_or_create(
                    name=self.username, created_by=self
                )
        else:
            # -- Assign all free users to the 'PUBLIC' team by default
            self.team, created = Team.objects.get_or_create(name="PUBLIC")
        super().save(*args, **kwargs)


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
# -- Projects


class ProjectQuerySet(models.QuerySet):
    def filter_by_team(self, team):
        return self.filter(create_by__team=team)


class Project(models.Model):
    uid = models.CharField(null=True, blank=True, max_length=12)
    name = models.CharField(max_length=100, default="new project")
    created_at = models.DateTimeField(auto_now_add=True)
    create_by = models.ForeignKey(
        User,
        related_name="created_projects",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    assembly_id_order = models.JSONField(default=list)
    objects = ProjectQuerySet.as_manager()

    @property
    def team(self) -> Team | None:
        """Return the Team of the User who created the Project."""
        if not self.create_by:
            return None
        return self.create_by.team

    def get_ordered_assemblies(self) -> list["Assembly"]:
        """Return assemblies ordered according to the assembly_id_order field."""
        # Sort assemblies by the order in assembly_order
        assemblies = {assembly.pk: assembly for assembly in self.assemblies.all()}
        return [
            assemblies[assembly_id]
            for assembly_id in self.assembly_id_order
            if assembly_id in assemblies
        ]

    def delete_assembly(self, assembly_pk: int) -> None:
        """Delete an assembly from the project."""
        if assembly_pk in self.assembly_id_order:
            self.assembly_id_order.remove(assembly_pk)
            self.save()

    def add_new_assembly(self) -> "Assembly | None":
        """Add a new assembly to the project."""
        if not self.team or self.team.name == "PUBLIC":
            return None

        assembly = Assembly.objects.create(user=self.team.created_by)
        self.assembly_id_order.append(assembly.pk)
        self.save()
        return assembly

    def save(self, *args, **kwargs) -> None:
        # -- Generate the UID if it does not exist
        if not self.uid:
            self.uid = generate_short_uid(Project, "prj")
        super().save(*args, **kwargs)

    @property
    def assemblies(self) -> models.QuerySet["Assembly"]:
        return self.assembly_set.all()  # type: ignore

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------------------
# -- Assemblies


class Assembly(models.Model):
    uid = models.CharField(null=True, blank=True, max_length=12)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="assemblies",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100, default="assembly")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        related_name="created_assemblies",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    layer_id_order = models.JSONField(default=list)

    @classmethod
    def create_new_assembly(
        cls, user: "User", name: str, project: Project
    ) -> "Assembly":
        """Create a new Assembly object."""
        new_assembly = cls.objects.create(created_by=user, name=name, project=project)
        new_assembly.save()
        return new_assembly

    def get_ordered_layers(self) -> list["Layer"]:
        """Return layers ordered according to the layer_id_order field."""
        # Sort layers by the order in layer_order
        layers = {layer.pk: layer for layer in self.layers.all()}
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
        self.layer_id_order.append(layer.pk)
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
    def segments(self) -> models.QuerySet["LayerSegment"]:
        return self.segments_set.all()  # type: ignore

    def get_ordered_segments(self):
        """Return segments ordered according to the segment_id_order field."""
        # Sort segments by the order in layer_order
        segments = {segment.pk: segment for segment in self.segments.all()}
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
        layer.segment_id_order.append(segment.pk)
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

    def save(self, *args, **kwargs) -> None:
        # -- Generate the UID if it does not exist
        if not self.uid:
            self.uid = generate_short_uid(LayerSegment, "seg")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"[layer-{self.layer}]: {self.material}"
