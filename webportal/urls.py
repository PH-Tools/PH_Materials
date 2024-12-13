from django.urls import path, include

from webportal import views

urlpatterns = [
    path("select2/", include("django_select2.urls")),
    path("", views.index, name="index"),
    # -----------------------------------------------------------------------------------
    # -- Materials
    path("materials/", views.materials_page, name="materials-page"),
    path("materials-list/", views.materials_list, name="materials-list"),
    path("create-material/", views.create_material, name="create-material"),
    path(
        "materials/<int:pk>/update",
        views.update_material,
        name="update-material",
    ),
    path(
        "material/<int:pk>/delete",
        views.delete_material,
        name="delete-material",
    ),
    path("get-materials", views.get_materials, name="get-materials"),
    path("materials/export-csv", views.export_csv, name="export-csv"),
    path("materials/import-materials", views.import_materials, name="import-materials"),
    path("materials/set-unit-system", views.set_unit_system, name="set-unit-system"),
    # -----------------------------------------------------------------------------------
    # -- Assemblies
    path("assemblies/", views.assemblies_page, name="assemblies-page"),
    path("assemblies/<int:pk>", views.assembly, name="assembly"),
    path(
        "assemblies/add-new-assembly", views.add_new_assembly, name="add-new-assembly"
    ),
    path(
        "assemblies/<int:pk>/update-assembly-name",
        views.update_assembly_name,
        name="update-assembly-name",
    ),
    path(
        "assemblies/<int:pk>/delete-assembly",
        views.delete_assembly,
        name="delete-assembly",
    ),
    # -----------------------------------------------------------------------------------
    # -- Assembly Details
    path("assemblies/<int:pk>/add-layer/", views.add_layer, name="add-layer"),
    path(
        "assemblies/<int:assembly_pk>/delete-layer/<int:layer_pk>/",
        views.delete_layer,
        name="delete-layer",
    ),
    path(
        "assemblies/<int:assembly_pk>/update-layer-thickness/<int:layer_pk>/",
        views.update_layer_thickness,
        name="update-layer-thickness",
    ),
    # Testing Select2 Dropdown
    path(
        "materialss/",
        views.material_dropdown,
        name="material-dropdown",
    ),
]
