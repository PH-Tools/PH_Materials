from enum import Enum
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
from django.core.paginator import Paginator
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


@login_required
def materials_page(request: WSGIRequest) -> HttpResponse:
    materials = Material.objects.all().select_related("category")
    materials_filter = MaterialCategoryFilter(request.GET, queryset=materials)
    paginator = Paginator(materials_filter.qs, settings.PAGE_SIZE)
    material_page = paginator.page(1)

    context = {
        "materials": material_page,
        "filter": materials_filter,
    }
    return render(request, "webportal/materials.html", context)


@login_required
def materials_list(request: WSGIRequest) -> HttpResponse:
    """The main Material-List view page."""
    materials = Material.objects.all().select_related("category")
    materials_filter = MaterialCategoryFilter(request.GET, queryset=materials)
    paginator = Paginator(materials_filter.qs, settings.PAGE_SIZE)
    material_page = paginator.page(1)

    context = {
        "materials": material_page,
        "filter": materials_filter,
    }
    return render(request, "webportal/partials/materials/container.html", context)


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


@login_required
def get_materials(request: WSGIRequest) -> HttpResponse:
    page = request.GET.get("page", 1)
    material_filter = MaterialCategoryFilter(
        request.GET,
        queryset=Material.objects.all().select_related("category"),
    )
    paginator = Paginator(material_filter.qs, settings.PAGE_SIZE)
    context = {
        "materials": paginator.page(page),
    }
    return render(
        request,
        "webportal/partials/materials/table.html",
        context,
    )


@login_required
def export_csv(request: WSGIRequest) -> HttpResponse | JsonResponse:
    # -- If the request comes from HTMX, do a client-side redirect but now
    # -- as a normal (ie: non-HTMX / Ajax) request to allow file downloading.
    if getattr(request, "htmx", None):
        return HttpResponse(headers={"HX-Redirect": request.get_full_path()})

    material_filter = MaterialCategoryFilter(
        request.GET,
        queryset=Material.objects.all().select_related("category"),
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
        file = request.FILES.get("file")
        if not file:
            context = {"message": "Please select a file to import"}
            return render(request, "webportal/partials/materials/import.html", context)

        resource = MaterialResource()
        dataset = Dataset()
        dataset.load(file.read().decode("utf-8"), format="csv")
        result = resource.import_data(dataset, user=request.user, dry_run=True)

        for row in result:
            for error in row.errors:
                print(error)

        if result.has_errors():
            print(result.base_errors)
            context = {"message": "Sorry, an error occurred during upload"}
        else:
            # Auto-generate unique_id for new Material objects if it does not exist
            for row in dataset.dict:
                if not row.get("unique_id"):
                    row["unique_id"] = uuid.uuid4().hex[:6]
                else:
                    # Check for existing Material with the same unique_id
                    existing_material = Material.objects.filter(
                        unique_id=row["unique_id"]
                    ).first()
                    if existing_material:
                        # Update existing Material
                        for key, value in row.items():
                            setattr(existing_material, key, value)
                        existing_material.save()
                    else:
                        # Create new Material
                        Material.objects.create(**row)
            context = {"message": f"{len(dataset)} materials imported successfully!"}

        return render(request, "webportal/partials/materials/success.html", context)

    return render(request, "webportal/partials/materials/import.html", context={})
