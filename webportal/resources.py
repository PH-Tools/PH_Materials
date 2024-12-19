from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget

from webportal.models import Material, MaterialCategory


class MaterialResource(resources.ModelResource):
    category = fields.Field(
        column_name="category",
        attribute="category",
        widget=ForeignKeyWidget(MaterialCategory, field="category"),
    )

    def dehydrate_category(self, obj: Material) -> str | None:
        # Get the display-name for the 'category' from its code
        return MaterialCategory.get_category_display_name(obj.category.category)  # type: ignore

    def before_import_row(self, row, **kwargs) -> None:
        # Convert the category display-name back to the category-code
        if "category" in row:
            code = MaterialCategory.get_category_code(row["category"])

            # Ensure that the category exists in the database
            MaterialCategory.objects.get_or_create(category=code)
            row["category"] = code

        # Set the user field for each Material instance
        user = kwargs.get("user")
        if user:
            row["user"] = user.pk

    def after_init_instance(self, instance, new, row, **kwargs):
        instance.user = kwargs.get("user")

    class Meta:
        model = Material
        fields = (
            "uid",
            "category",
            "name",
            "conductivity",
            "emissivity",
            "source",
            "comments",
            "color_argb",
        )
        import_id_fields = (
            "category",
            "name",
            "conductivity",
            "emissivity",
            "source",
            "comments",
            "color_argb",
        )
