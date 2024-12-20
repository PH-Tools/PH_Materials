from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.functions import Lower
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST
from django_htmx.http import retarget
from tablib import Dataset

from webportal.filters import MaterialCategoryFilter
from webportal.forms import MaterialForm
from webportal.models import Material
from webportal.resources import MaterialResource
from webportal.views._types import UnitSystem


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
