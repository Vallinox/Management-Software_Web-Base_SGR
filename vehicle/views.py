from django.shortcuts import render
from .models import Vehicle
from django.views.decorators.http import require_POST, require_http_methods


from .forms import VehicleForm
from django.http import JsonResponse
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse


def add_vehicle(request):
    if request.method == "POST":
        form = VehicleForm(request.POST)
        if form.is_valid():
            new_vehicle = form.save()

            # Se la richiesta è AJAX, restituiamo JSON
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": True, "message": "Mezzo aggiunto con successo!"}
                )

            # Se non è AJAX, torniamo alla pagina normalmente
            return render(
                request,
                "vehicle/add_vehicle.html",
                {"form": VehicleForm(), "success": True},
            )
        # Se il form non è valido, restituiamo gli errori in JSON se la richiesta è AJAX
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
    else:
        form = VehicleForm()

    return render(request, "vehicle/add_vehicle.html", {"form": form})


def list_vehicle(request):
    # Ottieni tutti i nomi di ragione sociale unici
    company_names = Vehicle.objects.values("company_own").distinct()

    # Ottieni tutti gli anni unici dalle date delle fatture
    plate = Vehicle.objects.values("plate").values().distinct()

    context = {"company_own": company_names, "plate": plate}
    return render(request, "vehicle/list_vehicle.html", context)


def filter_vehicle(request):
    company_own = request.GET.get("company_own")
    vehicles = Vehicle.objects.filter(company_own=company_own)

    data = {
        "vehicles": [
            {
                "id": v.id,  # <-- IMPORTANTE!
                "plate": v.plate,
                "vehicle_category": v.vehicle_category,
                "eur_category": v.eur_category,
                "contract_type": v.contract_type,
                "insurance_term_expires": v.insurance_term_expires.strftime("%d/%m/%Y"),
                "review_deadline": v.review_deadline.strftime("%d/%m/%Y"),
                "bollo_deadline": v.bollo_deadline.strftime("%d/%m/%Y"),
                "aci_card_deadline": v.aci_card_deadline.strftime("%d/%m/%Y"),
            }
            for v in vehicles
        ]
    }
    return JsonResponse(data)


@require_http_methods(["DELETE"])
def delete_vehicle(request, vehicle_id):
    try:
        vehicle = Vehicle.objects.get(id=vehicle_id)
        vehicle.delete()
        return JsonResponse({"success": True})
    except Vehicle.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Veicolo non trovato"}, status=404
        )

def edit_vehicle(request, id):
    vehicle = get_object_or_404(Vehicle, id=id)
    form = VehicleForm(request.POST or None, instance=vehicle)

    if request.method == "POST" and form.is_valid():
        form.save()
        return JsonResponse({"success": True})

    return render(request, "vehicle/edit_vehicle.html", {"form": form, "vehicle": vehicle})