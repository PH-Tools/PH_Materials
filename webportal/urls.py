from django.urls import include, path

from webportal.views import assembly, materials, settings, views

urlpatterns = [
    path("select2/", include("django_select2.urls")),
    path("", views.index, name="index"),
    path("account-settings/", settings.account_settings, name="account-settings"),
    path(
        "account-settings/update-team-name/",
        settings.update_team_name,
        name="update-team-name",
    ),
    path(
        "account-settings/update-first-name/",
        settings.update_first_name,
        name="update-first-name",
    ),
    path(
        "account-settings/update-last-name/",
        settings.update_last_name,
        name="update-last-name",
    ),
    path(
        "account-settings/update-email/",
        settings.update_email,
        name="update-email",
    ),
    path(
        "account-settings/invite-user-to-team/",
        settings.invite_user_to_team,
        name="invite-user-to-team",
    ),
    path(
        "account-settings/accept-team-invite/",
        settings.accept_team_invite,
        name="accept-team-invite",
    ),
    path(
        "account-settings/decline-team-invite/",
        settings.decline_team_invite,
        name="decline-team-invite",
    ),
    path(
        "account-settings/leave-team/",
        settings.leave_team,
        name="leave-team",
    ),
    # -----------------------------------------------------------------------------------
    # -- Materials
    path("materials/", materials.materials_page, name="materials-page"),
    path("materials-list/", materials.materials_list, name="materials-list"),
    path("create-material/", materials.create_material, name="create-material"),
    path(
        "materials/<int:pk>/update",
        materials.update_material,
        name="update-material",
    ),
    path(
        "material/<int:pk>/delete",
        materials.delete_material,
        name="delete-material",
    ),
    path("get-materials", materials.get_materials, name="get-materials"),
    path("materials/export-csv", materials.export_csv, name="export-csv"),
    path(
        "materials/import-materials",
        materials.import_materials,
        name="import-materials",
    ),
    path(
        "materials/set-unit-system", materials.set_unit_system, name="set-unit-system"
    ),
    # -----------------------------------------------------------------------------------
    # -- Assemblies
    path("assemblies/", assembly.assemblies_page, name="assemblies-page-landing"),
    path("assemblies/<int:project_pk>/", assembly.assembly, name="assembly-landing"),
    path("assemblies/change-project/", assembly.change_project, name="change-project"),
    path(
        "assemblies/<int:project_pk>/<int:assembly_pk>/",
        assembly.assembly,
        name="assembly",
    ),
    path(
        "assemblies/<int:project_pk>/add-new-assembly",
        assembly.add_new_assembly,
        name="add-new-assembly",
    ),
    path(
        "assemblies/<int:project_pk>/<int:assembly_pk>/update-assembly-name",
        assembly.update_assembly_name,
        name="update-assembly-name",
    ),
    path(
        "assemblies/<int:project_pk>/<int:assembly_pk>/delete-assembly",
        assembly.delete_assembly,
        name="delete-assembly",
    ),
    # -----------------------------------------------------------------------------------
    # -- Assembly Details
    path(
        "assemblies/<int:project_pk>/<int:assembly_pk>/add-layer/",
        assembly.add_layer,
        name="add-layer",
    ),
    path(
        "assemblies/<int:project_pk>/<int:assembly_pk>/delete-layer/<int:layer_pk>/",
        assembly.delete_layer,
        name="delete-layer",
    ),
    path(
        "assemblies/<int:project_pk>/<int:assembly_pk>/update-layer-thickness/<int:layer_pk>/",
        assembly.update_layer_thickness,
        name="update-layer-thickness",
    ),
    path(
        "assemblies/<int:project_pk>/<int:assembly_pk>/update-layer-material/<int:layer_pk>/",
        assembly.update_layer_material,
        name="update-layer-material",
    ),
]
