from django.shortcuts import render
from .models import Vehicle

from .forms import VehicleForm
from django.http import JsonResponse
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse


def add_vehicle(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            new_vehicle = form.save()

            # Se la richiesta è AJAX, restituiamo JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"success": True, "message": "Mezzo aggiunto con successo!"})

            # Se non è AJAX, torniamo alla pagina normalmente
            return render(request, 'vehicle/add_vehicle.html', {
                'form': VehicleForm(),
                'success': True
            })
        # Se il form non è valido, restituiamo gli errori in JSON se la richiesta è AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
    else:
        form = VehicleForm()

    return render(request, 'vehicle/add_vehicle.html', {
        'form': form
    })

def list_vehicle(request):
   
    return render(request, 'vehicle/list_vehicle.html')