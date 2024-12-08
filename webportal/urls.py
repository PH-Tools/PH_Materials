from django.urls import path

from webportal import views

urlpatterns = [
    path("", views.index, name="index"),
    path("materials/", views.materials_list, name="materials-list"),
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
]
