from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from webportal.models import Material, MaterialCategory


class MaterialResource(resources.ModelResource):
    category = fields.Field(
        column_name="category",
        attribute="category",
        widget=ForeignKeyWidget(MaterialCategory, field="category"),
    )

    def dehydrate_category(self, obj):
        # Get the display-name for the 'category' from it's code
        return MaterialCategory.get_category_display_name(obj.category.category)

    def before_import_row(self, row, **kwargs):
        # convert the category-display-name back to the category-code
        if "category" in row:
            row["category"] = MaterialCategory.get_category_code(row["category"])

    class Meta:
        model = Material
        fields = (
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
