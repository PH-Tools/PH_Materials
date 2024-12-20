from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template import Context
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from render_block import render_block_to_string

from webportal.models import Assembly, Layer, Material, Project
from webportal.views._types import LayerView, get_user

# ---------------------------------------------------------------------------------------
# -- Assembly-Views


@login_required
def assemblies_page(
    request: WSGIRequest, project_pk: int | None = None
) -> HttpResponse:
    print(">> assemblies/")

    user = get_user(request)
    active_project = Project.get_team_projects(team=user.team).first()
    if not active_project:
        active_project = Project.create_new_project(user, name="Default Project")

    projects = Project.get_team_projects(team=user.team)
    assemblies = Assembly.objects.filter(project__in=projects)

    context = {
        "current_user": user,
        "projects": projects,
        "active_project": active_project,
        "assemblies": assemblies,
    }
    return render(request, "webportal/assemblies.html", context)


def sidebar_add_assembly_button(request: WSGIRequest, project_pk: int) -> str:
    """HTML String for the Assembly sidebar-add-button."""

    active_project = get_object_or_404(Project, pk=project_pk)
    return render_block_to_string(
        "webportal/partials/assemblies/sidebar.html",
        block_name="assembly-sidebar-add-button",
        context=Context(
            {
                "active_project": active_project,
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
                "active_project": active_project,
            }
        ),
        request=request,
    )


def assembly_detail(project_pk: int, assembly_pk: int | None) -> str:
    """HTML String for the Assembly detail view with all layer and materials."""

    active_project = get_object_or_404(Project, pk=project_pk)
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
                "active_project": active_project,
            },
        )
    else:
        return render_to_string(
            "webportal/partials/assemblies/assembly.html",
            {
                "active_project": active_project,
            },
        )


@login_required
def change_project(request: WSGIRequest) -> HttpResponse:
    print(f">> change_project/")

    if new_project_pk := request.GET.get("project_pk", None):
        project_pk = int(new_project_pk)
    else:
        if this_team := get_user(request).team:
            if project := Project.get_team_default_project(this_team):
                project_pk = project.pk

    sidebar_button = sidebar_add_assembly_button(request, project_pk)
    sidebar_list = sidebar_assembly_list(request, project_pk, None)
    assembly_html = assembly_detail(project_pk, None)

    active_project = get_object_or_404(Project, pk=project_pk)
    active_uid = (
        f'<span id="active-project-uid" hx-swap-oob="true">{active_project.uid}</span>'
    )
    full_html = assembly_html + sidebar_button + sidebar_list + active_uid
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

    this_assembly = get_object_or_404(Assembly, pk=assembly_pk)
    if name := request.POST.get("name"):
        this_assembly.set_name(name)

    template_name = "webportal/partials/assemblies/assembly.html"
    active_project = get_object_or_404(Project, pk=project_pk)
    context = Context(
        {
            "assembly": this_assembly,
            "active_project": active_project,
        }
    )
    detail_view_name = render_block_to_string(
        template_name, block_name="assembly-name", context=context, request=request
    )
    sidebar_name = f"<div id='assembly-name-{this_assembly.pk}' hx-swap-oob='true'>{this_assembly.name}</div>"
    return HttpResponse(content=detail_view_name + sidebar_name)


@login_required
@require_POST
def add_new_assembly(request: WSGIRequest, project_pk: int) -> HttpResponse:
    print(f">> add_new_assembly/{project_pk}")

    active_project = get_object_or_404(Project, pk=project_pk)
    new_assembly = Assembly.create_new_assembly(
        user=get_user(request),
        name="unnamed",
        project=active_project,
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
    active_project = get_object_or_404(Project, pk=project_pk)

    layer_html = render_block_to_string(
        "webportal/partials/assemblies/assembly.html",
        block_name="layer",
        context=Context(
            {
                "assembly": this_assembly,
                "layer_view": LayerView(new_layer),
                "active_project": active_project,
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

    this_layer = get_object_or_404(Layer, id=layer_pk)
    if thickness := request.POST.get("thickness"):
        this_layer.set_layer_thickness(float(thickness))
    return HttpResponse(this_layer.thickness)


@login_required
@require_POST
def update_layer_material(
    request: WSGIRequest, project_pk: int, assembly_pk: int, layer_pk: int
) -> HttpResponse:
    print(f">> {project_pk}/{assembly_pk}/update_layer_material/{layer_pk}")

    this_layer = get_object_or_404(Layer, id=layer_pk)
    # TODO: Support multiple segments.
    # for now, set all segments to the same material...
    for segment in this_layer.segments.all():
        # Select2 will return something like 'form_2-material' as the key
        if mat_id := request.POST.get(f"form_{segment.pk}-material", None):
            new_material = Material.objects.get(id=mat_id)
            segment.set_segment_material(new_material)
            return HttpResponse(new_material.name)
    return HttpResponse()
