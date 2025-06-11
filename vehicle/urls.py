from django.urls import path
from . import views

app_name = "vehicle"
urlpatterns = [
    path("list/", views.list_vehicle, name="list_vehicle"),
    path("add_vehicle/", views.add_vehicle, name="add_vehicle"),
    path("vehicles/filter/", views.filter_vehicle, name="filter_vehicles"),
    path("edit_vehicle/<int:id>/", views.edit_vehicle, name="edit_vehicle"),
    path("vehicles/delete/<int:vehicle_id>/", views.delete_vehicle, name="delete_vehicle"),
]
