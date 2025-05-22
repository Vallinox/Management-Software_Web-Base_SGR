from django.contrib import admin
from . import models

# Register your models here.


class VehicleAdmin(admin.ModelAdmin):
    list_display = [
        "company_own",
        "plate",
        "vehicle_category",
        "eur_category",
        "contract_type",
        "insurance_term_expires",
        "review_deadline",
        "bollo_deadline",
        "aci_card_deadline",
        "matched_driver",
    ]


admin.site.register(models.Vehicle, VehicleAdmin)
