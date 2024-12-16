from enum import Enum
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Max
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
from webportal.models import Material, Assembly, Layer
from webportal.resources import MaterialResource


class UnitSystem(Enum):
    SI = "SI"
    IP = "IP"


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
def assemblies_page(request: WSGIRequest) -> HttpResponse:
    context = {
        "current_user": request.user,
        "assemblies": Assembly.objects.filter(user=request.user),
    }
    return render(request, "webportal/assemblies.html", context)


@login_required
def assembly(request: WSGIRequest, pk: int | None) -> HttpResponse:
    """The Assembly view with the sidebar.

    Sidebar includes the 'active' assembly highlighted.
    """
    # -------------------------------------------------------------------------
    # -- Detail-View
    this_assembly = get_object_or_404(Assembly, pk=pk)
    layers: list[Layer] = this_assembly.get_ordered_layers()
    if not layers:
        new_layer = Layer.objects.create(assembly=this_assembly, thickness=1.0)
        this_assembly.layer_id_order.append(new_layer.id)
        this_assembly.save()
        layers = this_assembly.get_ordered_layers()
    forms: list[MaterialSearchForm] = [
        MaterialSearchForm(request=request, prefix=f"form_{layer.pk}")
        for layer in layers
    ]
    assembly_html = render_to_string(
        "webportal/partials/assemblies/assembly.html",
        context={
            "assembly": this_assembly,
            "layers_and_forms": zip(layers, forms),
        },
    )

    # -------------------------------------------------------------------------
    # -- Sidebar
    sidebar_html = render_block_to_string(
        "webportal/partials/assemblies/sidebar.html",
        block_name="assembly-sidebar-list",
        context=Context(
            {
                "assemblies": Assembly.objects.filter(user=request.user),
                "active_assembly_id": pk,
            }
        ),
        request=request,
    )
    return HttpResponse(assembly_html + sidebar_html, content_type="text/html")


# ---------------------------------------------------------------------------------------
# -- Assembly-Operations


@login_required
@require_POST
def update_assembly_name(request: WSGIRequest, pk: int) -> HttpResponse:
    if request.method == "POST":
        if name := request.POST.get("name"):
            this_assembly = get_object_or_404(Assembly, pk=pk)
            this_assembly.name = name
            this_assembly.save()

    template_name = "webportal/partials/assemblies/assembly.html"
    context = Context({"assembly": this_assembly})
    detail_view_name = render_block_to_string(
        template_name, block_name="assembly-name", context=context, request=request
    )
    sidebar_name = f"<div id='assembly-name-{this_assembly.pk}' hx-swap-oob='true'>{this_assembly.name}</div>"
    return HttpResponse(content=detail_view_name + sidebar_name)


@login_required
def add_new_assembly(request: WSGIRequest) -> HttpResponse:
    if request.method == "POST":
        new_assembly = Assembly(user=request.user, name="unnamed")
        new_assembly.save()

    return assembly(request, new_assembly.pk)


@login_required
def delete_assembly(request: WSGIRequest, pk: int) -> HttpResponse:
    this_assembly = get_object_or_404(Assembly, pk=pk)
    this_assembly.delete()
    return assembly(
        request, getattr(Assembly.objects.filter(user=request.user).first(), "pk", None)
    )


@login_required
def add_layer(request: WSGIRequest, pk: int) -> HttpResponse:
    this_assembly = get_object_or_404(Assembly, id=pk)
    new_layer = Layer(assembly=this_assembly, thickness=1.0)
    new_layer.save()
    this_assembly.layer_id_order.append(new_layer.id)
    this_assembly.save()

    layer_html = render_block_to_string(
        "webportal/partials/assemblies/assembly.html",
        block_name="layer",
        context=Context(
            {
                "layer": new_layer,
                "assembly": this_assembly,
                "form": MaterialSearchForm(
                    request=request, prefix=f"form_{new_layer.pk}"
                ),
            }
        ),
        request=request,
    )
    return HttpResponse(layer_html, content_type="text/html")


@login_required
def delete_layer(request: WSGIRequest, assembly_pk: int, layer_pk: int) -> HttpResponse:
    this_assembly = get_object_or_404(Assembly, id=assembly_pk)
    this_assembly.delete_layer(layer_pk)
    this_layer = get_object_or_404(Layer, id=layer_pk)
    this_layer.delete()

    return assembly(request, assembly_pk)


@login_required
@require_POST
def update_layer_thickness(
    request: WSGIRequest, assembly_pk: int, layer_pk: int
) -> HttpResponse:
    layer = get_object_or_404(Layer, id=layer_pk)
    if request.method == "POST":
        if thickness := request.POST.get("thickness"):
            layer.thickness = float(thickness)
            layer.save()
    return HttpResponse(layer.thickness)


def material_dropdown(request):
    # if request.htmx:
    #     materials = Material.objects.filter(
    #         Q(user=request.user) | Q(user__id=1)
    #     ).values_list("id", "name")
    #     data = [{"id": material[0], "text": material[1]} for material in materials]
    #     return JsonResponse({"results": data})

    forms = [
        MaterialSearchForm(request=request, prefix=str(uuid.uuid4())[6:])
        for i in range(10)
    ]

    return HttpResponse(
        render_to_string("select2_example.html", {"forms": forms}),
        content_type="text/html",
    )
