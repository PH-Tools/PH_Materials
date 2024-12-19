from enum import Enum

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.db.models.functions import Lower
from django.template.loader import render_to_string
from django.template import Context
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST
from django_htmx.http import retarget
from tablib import Dataset
from render_block import render_block_to_string

from webportal.filters import MaterialCategoryFilter
from webportal.forms import MaterialForm, MaterialSearchForm
from webportal.models import Material, Assembly, Layer, User, Team, User, Project
from webportal.resources import MaterialResource


def get_user(request: WSGIRequest) -> User:
    """Wrapper function to mask type-hint warnings."""
    return request.user  # type: ignore


class UnitSystem(Enum):
    SI = "SI"
    IP = "IP"


class LayerView:
    """A helper class to manage the Layer and its segments/forms in the Assembly view."""

    def __init__(self, layer: Layer):
        self.layer = layer
        self.segments = layer.get_ordered_segments()
        self.forms = [
            MaterialSearchForm(
                prefix=f"form_{segment.pk}",
                initial={"material": segment.material.pk if segment.material else None},
            )
            for segment in self.segments
        ]

    @property
    def segments_and_forms(self):
        return zip(self.segments, self.forms)


@require_POST
def set_unit_system(request: WSGIRequest) -> HttpResponse:
    if request.POST.get("unit-system", None):
        request.session["unit_system"] = UnitSystem.IP.value
    else:
        request.session["unit_system"] = UnitSystem.SI.value

    # -- Since material-list reads the GET, redirect to a GET
    # Extract other parameters from the POST request
    other_params = request.POST.dict()
    other_params.pop("unit-system", None)  # Remove the unit-system parameter

    # Build the query string for the redirect URL
    query_string = "&".join([f"{key}={value}" for key, value in other_params.items()])

    # Redirect to the materials_list view with the query parameters
    return redirect(f"{reverse('get-materials')}?{query_string}")


def index(request: WSGIRequest) -> HttpResponse:
    return render(request, "webportal/index.html")


# ---------------------------------------------------------------------------------------
# -- User / Team Management Views


@login_required
def account_settings(request: WSGIRequest) -> HttpResponse:
    print(">> account_settings")

    user = get_user(request)
    context = {
        "user": user,
        "team": user.team,
        "team_members": user.team_members,
    }
    return render(request, "webportal/account_settings.html", context)


@require_POST
@login_required
def update_team_name(request: WSGIRequest) -> HttpResponse:
    print(">> update_team_name")

    locked_names = {"PUBLIC", "ADMIN"}
    user = get_user(request)

    if not user.team or user.team.name in locked_names:
        return HttpResponse(user.team.name if user.team else "PUBLIC")

    new_team_name = request.POST.get("team_name")
    if new_team_name and new_team_name not in locked_names:
        user.team.update_name(new_team_name)
        return HttpResponse(new_team_name)

    return HttpResponse(user.team.name)


@require_POST
@login_required
def update_first_name(request: WSGIRequest) -> HttpResponse:
    print(">> update_first_name")

    user = get_user(request)
    if request.method == "POST":
        if new_first_name := request.POST.get("first_name"):
            user.first_name = new_first_name
            user.save()
            return HttpResponse(new_first_name)
    return HttpResponse(user.first_name)


@require_POST
@login_required
def update_last_name(request: WSGIRequest) -> HttpResponse:
    print(">> update_last_name")

    user = get_user(request)
    if request.method == "POST":
        if new_last_name := request.POST.get("last_name"):
            user.last_name = new_last_name
            user.save()
            return HttpResponse(new_last_name)
    return HttpResponse(user.last_name)


@require_POST
@login_required
def update_email(request: WSGIRequest) -> HttpResponse:
    print(">> update_email")

    user = get_user(request)
    if request.method == "POST":
        if new_email := request.POST.get("email"):
            user.email = new_email
            user.save()
            return HttpResponse(new_email)
    return HttpResponse(user.email)


@require_POST
@login_required
def invite_user_to_team(request: WSGIRequest) -> HttpResponse:
    print(">> invite_user_to_team")

    user = get_user(request)
    if not user.team:
        return HttpResponse("No Team to invite to")

    if request.method == "POST":
        if email := request.POST.get("user_email"):
            if invited_user := User.objects.get(email=email):
                invited_user.invite_to_team(user)
                invited_user.save()
                return HttpResponse(
                    f"Invited User '{email}' to Team '{user.team.name}'"
                )
            return HttpResponse(f"Error: User '{email}' not found?")
    return HttpResponse("Invite User to Team")


@require_POST
@login_required
def accept_team_invite(request: WSGIRequest) -> HttpResponse:
    print(">> accept_team_invite")

    user = get_user(request)
    if request.method == "POST":
        if not user.team_invite:
            return HttpResponse("No Team Invite to accept")
        if team := Team.objects.get(id=user.team_invite.pk):
            user.team = team
            user.team_invite = None
            user.save()
            return HttpResponse(f"Joined Team '{team.name}'")
    return HttpResponse("Accepted Team Invite")


@require_POST
@login_required
def decline_team_invite(request: WSGIRequest) -> HttpResponse:
    print(">> decline_team_invite")

    user = get_user(request)
    if request.method == "POST":
        if not user.team_invite:
            return HttpResponse("No Team Invite to accept")
        if team := Team.objects.get(id=user.team_invite.pk):
            user.team_invite = None
            user.save()
            return HttpResponse(f"Declined Team Invite to join '{team.name}'")
    return HttpResponse("Declined Team Invite")


@require_POST
@login_required
def leave_team(request: WSGIRequest) -> HttpResponse:
    print(">> leave_team")

    user = get_user(request)
    if request.method == "POST":
        user.team, created = Team.objects.get_or_create(
            name=user.username, created_by=user
        )
        user.team_invite = None
        user.save()

    block_html = render_block_to_string(
        "webportal/partials/account_settings/settings.html",
        block_name="teams",
        context=Context(
            {
                "user": user,
                "team": user.team,
                "team_members": user.team_members,
            }
        ),
        request=request,
    )
    return HttpResponse(block_html, content_type="text/html")


# ---------------------------------------------------------------------------------------
# -- Materials-List Views


def _get_materials(request: WSGIRequest) -> dict:
    """Helper function to get the materials for the materials page."""
    materials = Material.objects.filter(
        Q(user=request.user) | Q(user__id=1)
    ).select_related("category", "user")

    # -- order by name, case-insensitive
    materials = materials.annotate(lower_name=Lower("name")).order_by(
        "category", "lower_name"
    )
    materials_filter = MaterialCategoryFilter(request.GET, queryset=materials)
    paginator = Paginator(materials_filter.qs, settings.PAGE_SIZE)
    page = request.GET.get("page", 1)
    material_page = paginator.page(page)

    return {
        "materials": material_page,
        "filter": materials_filter,
        "current_user": request.user,
    }


@login_required
def materials_page(request: WSGIRequest) -> HttpResponse:
    """The main Material-List view page. Called on first load."""
    context = _get_materials(request)
    return render(request, "webportal/materials.html", context)


@login_required
def materials_list(request: WSGIRequest) -> HttpResponse:
    """The material-list when page is loaded via HTMX."""
    context = _get_materials(request)
    return render(request, "webportal/partials/materials/container.html", context)


@login_required
def get_materials(request: WSGIRequest) -> HttpResponse:
    """Get the materials list when the user interacts with the filters."""
    context = _get_materials(request)
    return render(request, "webportal/partials/materials/table.html", context)


# ---------------------------------------------------------------------------------------
# -- Materials-List Operations


@login_required
def create_material(request: WSGIRequest) -> HttpResponse:
    if request.method == "POST":
        form = MaterialForm(request.POST)
        if form.is_valid():
            material = form.save(commit=False)
            material.user = request.user
            material.save()
            context = {"message": "Material created successfully!"}
            return render(request, "webportal/partials/materials/success.html", context)
        else:
            context = {"form": form}
            response = render(
                request, "webportal/partials/materials/create.html", context
            )
            return retarget(response, "#material-list-page")

    context = {"form": MaterialForm()}
    return render(request, "webportal/partials/materials/create.html", context)


@login_required
def update_material(request: WSGIRequest, pk: int) -> HttpResponse:
    material = get_object_or_404(Material, pk=pk)

    if request.method == "POST":
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            material = form.save()
            context = {"message": "Material updated successfully!"}
            return render(request, "webportal/partials/materials/success.html", context)
        else:
            context = {"form": form, "material": material}
            response = render(
                request, "webportal/partials/materials/update.html", context
            )
            return retarget(response, "#material-list-page")

    context = {
        "form": MaterialForm(instance=material),
        "material": material,
    }

    return render(request, "webportal/partials/materials/update.html", context)


@login_required
@require_http_methods(["DELETE"])
def delete_material(request: WSGIRequest, pk: int) -> HttpResponse:
    material = get_object_or_404(Material, pk=pk)
    material.delete()
    context = {
        "message": f"Material deleted successfully!",
    }
    return render(request, "webportal/partials/materials/success.html", context)


# ---------------------------------------------------------------------------------------
# -- Materials-List I/O


@login_required
def export_csv(request: WSGIRequest) -> HttpResponse | JsonResponse:
    # -- If the request comes from HTMX, do a client-side redirect but now
    # -- as a normal (ie: non-HTMX / Ajax) request to allow file downloading.
    if getattr(request, "htmx", None):
        return HttpResponse(headers={"HX-Redirect": request.get_full_path()})

    material_filter = MaterialCategoryFilter(
        request.GET,
        queryset=Material.objects.filter(
            Q(user=request.user) | Q(user__id=1)
        ).select_related("category"),
    )

    data = MaterialResource().export(material_filter.qs)
    if csv_data := getattr(data, "csv", None):
        response = HttpResponse(csv_data)
        response["Content-Disposition"] = "attachment; filename=ph_materials.csv"
        return response
    else:
        return JsonResponse({"message": "No data to export"})


@login_required
def import_materials(request: WSGIRequest) -> HttpResponse:
    if request.method == "POST":
        # -------------------------------------------------------------------------------
        # -- Read in the CSV file
        file = request.FILES.get("file")
        if not file:
            context = {"message": "Please select a file to import"}
            return render(request, "webportal/partials/materials/import.html", context)

        resource = MaterialResource()
        dataset = Dataset()
        dataset.load(file.read().decode("utf-8"), format="csv")

        # -------------------------------------------------------------------------------
        # -- Check the import data for errors
        result = resource.import_data(dataset, user=request.user, dry_run=True)

        for row in result:
            for error in row.errors:
                print(f"IMPORT ERROR: {error}")

        if result.has_errors():
            print(result.base_errors)
            context = {"message": "Sorry, an error occurred during upload"}
            return render(request, "webportal/partials/materials/success.html", context)

        # -------------------------------------------------------------------------------
        # Create the new Material objects in the Database
        resource.import_data(dataset, user=request.user, dry_run=False)
        context = {"message": f"{len(dataset)} materials imported successfully!"}
        return render(request, "webportal/partials/materials/success.html", context)

    # -- GET request
    return render(request, "webportal/partials/materials/import.html", context={})


# ---------------------------------------------------------------------------------------
# -- Assembly-Views


@login_required
def assemblies_page(
    request: WSGIRequest, project_pk: int | None = None
) -> HttpResponse:
    print(">> assemblies/")

    user = get_user(request)
    projects = Project.objects.filter_by_team(team=user.team)
    assemblies = Assembly.objects.filter(project__in=projects)

    context = {
        "current_user": user,
        "projects": projects,
        "active_project_pk": projects.first().pk,
        "assemblies": assemblies,
    }
    return render(request, "webportal/assemblies.html", context)


def sidebar_add_assembly_button(request: WSGIRequest, project_pk: int) -> str:
    active_project = get_object_or_404(Project, pk=project_pk)
    return render_block_to_string(
        "webportal/partials/assemblies/sidebar.html",
        block_name="assembly-sidebar-add-button",
        context=Context(
            {
                "active_project_pk": active_project.pk,
            }
        ),
        request=request,
    )


def sidebar_assembly_list(
    request: WSGIRequest, project_pk: int, assembly_pk: int | None
) -> str:
    """HTML String for the Assembly sidebar-list of all assemblies in the project."""
    active_project = get_object_or_404(Project, pk=project_pk)
    project_assemblies = Assembly.objects.filter(project=active_project)
    return render_block_to_string(
        "webportal/partials/assemblies/sidebar.html",
        block_name="assembly-sidebar-list",
        context=Context(
            {
                "assemblies": project_assemblies,
                "active_assembly_id": assembly_pk,
                "active_project_pk": active_project.pk,
            }
        ),
        request=request,
    )


def assembly_detail(project_pk: int, assembly_pk: int | None) -> str:
    """HTML String for the Assembly detail view with all layer and materials."""
    if assembly_pk:
        this_assembly = get_object_or_404(Assembly, pk=assembly_pk)
        layers: list[Layer] = this_assembly.get_ordered_layers()
        if not layers:
            this_assembly.add_new_layer()
            layers = this_assembly.get_ordered_layers()

        return render_to_string(
            "webportal/partials/assemblies/assembly.html",
            context={
                "assembly": this_assembly,
                "layer_views": (LayerView(layer) for layer in layers),
                "active_project_pk": project_pk,
            },
        )
    else:
        return render_to_string(
            "webportal/partials/assemblies/assembly.html",
            {
                "active_project_pk": project_pk,
            },
        )


@login_required
def change_project(request: WSGIRequest) -> HttpResponse:
    print(f">> change_project/")

    if new_project_pk := request.GET.get("project_pk", None):
        project_pk = int(new_project_pk)

    sidebar_button = sidebar_add_assembly_button(request, project_pk)
    sidebar_list = sidebar_assembly_list(request, project_pk, None)
    assembly_html = assembly_detail(project_pk, None)
    full_html = assembly_html + sidebar_button + sidebar_list
    return HttpResponse(full_html, content_type="text/html")


@login_required
def assembly(
    request: WSGIRequest, project_pk: int, assembly_pk: int | None = None
) -> HttpResponse:
    """The Assembly view with the sidebar.

    Sidebar includes the 'active' assembly highlighted.
    """

    print(f">> assembly/{project_pk}/{assembly_pk}")

    assembly_html = assembly_detail(project_pk, assembly_pk)
    sidebar_project_list_html = sidebar_assembly_list(request, project_pk, assembly_pk)
    full_html = assembly_html + sidebar_project_list_html
    return HttpResponse(full_html, content_type="text/html")


# ---------------------------------------------------------------------------------------
# -- Assembly-Operations


@login_required
@require_POST
def update_assembly_name(
    request: WSGIRequest, project_pk: int, assembly_pk: int
) -> HttpResponse:
    print(f">> {project_pk}/{assembly_pk}/update_assembly_name")
    if request.method == "POST":
        if name := request.POST.get("name"):
            this_assembly = get_object_or_404(Assembly, pk=assembly_pk)
            this_assembly.name = name
            this_assembly.save()

    template_name = "webportal/partials/assemblies/assembly.html"
    context = Context({"assembly": this_assembly, "active_project_pk": project_pk})
    detail_view_name = render_block_to_string(
        template_name, block_name="assembly-name", context=context, request=request
    )
    sidebar_name = f"<div id='assembly-name-{this_assembly.pk}' hx-swap-oob='true'>{this_assembly.name}</div>"
    return HttpResponse(content=detail_view_name + sidebar_name)


@login_required
@require_POST
def add_new_assembly(request: WSGIRequest, project_pk: int) -> HttpResponse:
    print(f">> add_new_assembly/{project_pk}")

    if request.method == "POST":
        new_assembly = Assembly.create_new_assembly(
            user=get_user(request),
            name="unnamed",
            project=Project.objects.get(pk=project_pk),
        )

    return assembly(request, project_pk, new_assembly.pk)


@login_required
def delete_assembly(
    request: WSGIRequest, project_pk: int, assembly_pk: int
) -> HttpResponse:
    print(f">> {project_pk}/{assembly_pk}/delete_assembly")

    this_assembly = get_object_or_404(Assembly, pk=assembly_pk)
    this_assembly.delete()
    active_project = get_object_or_404(Project, pk=project_pk)
    project_assemblies = Assembly.objects.filter(project=active_project)
    return assembly(
        request,
        project_pk,
        getattr(project_assemblies.first(), "pk", None),
    )


@login_required
def add_layer(request: WSGIRequest, project_pk: int, assembly_pk: int) -> HttpResponse:
    print(f">> {project_pk}/{assembly_pk}/add_layer")
    this_assembly = get_object_or_404(Assembly, id=assembly_pk)
    new_layer = this_assembly.add_new_layer()

    layer_html = render_block_to_string(
        "webportal/partials/assemblies/assembly.html",
        block_name="layer",
        context=Context(
            {
                "assembly": this_assembly,
                "layer_view": LayerView(new_layer),
                "active_project_pk": project_pk,
            },
        ),
        request=request,
    )
    return HttpResponse(layer_html, content_type="text/html")


@login_required
def delete_layer(
    request: WSGIRequest, project_pk: int, assembly_pk: int, layer_pk: int
) -> HttpResponse:
    print(f">> {project_pk}/{assembly_pk}/delete_layer/{layer_pk}")
    this_assembly = get_object_or_404(Assembly, id=assembly_pk)
    this_assembly.delete_layer(layer_pk)
    this_layer = get_object_or_404(Layer, id=layer_pk)
    this_layer.delete()

    return assembly(request, project_pk, assembly_pk)


@login_required
@require_POST
def update_layer_thickness(
    request: WSGIRequest, project_pk: int, assembly_pk: int, layer_pk: int
) -> HttpResponse:
    print(f">> {project_pk}/{assembly_pk}/update_layer_thickness/{layer_pk}")
    layer = get_object_or_404(Layer, id=layer_pk)
    if request.method == "POST":
        if thickness := request.POST.get("thickness"):
            layer.thickness = float(thickness)
            layer.save()
    return HttpResponse(layer.thickness)


@login_required
@require_POST
def update_layer_material(
    request: WSGIRequest, project_pk: int, assembly_pk: int, layer_pk: int
) -> HttpResponse:
    print(f">> {project_pk}/{assembly_pk}/update_layer_material/{layer_pk}")

    layer = get_object_or_404(Layer, id=layer_pk)
    if request.method == "POST":
        for segment in layer.segments.all():
            # Select2 will return something like 'form_2-material' as the key
            if mat_id := request.POST.get(f"form_{segment.pk}-material", None):
                new_material = Material.objects.get(id=mat_id)
                segment.material = new_material
                segment.save()
                return HttpResponse(new_material.name)
    return HttpResponse()
