from django.contrib import admin
from . import models



class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'invoice_number', 'invoice_date', 'freight_cost',
                    'vat_rate', 'vat_amount', 'total_amount', 'payment_due_date']

class VehicleAdmin(admin.ModelAdmin):
    list_display= ["company_own", "plate", "vehicle_category", "eur_category", "contract_type",
                   "insurance_term_expires", "review_deadline", "bollo_deadline", "aci_card_deadline",
                   "matched_driver"]

# Register your models here.
admin.site.register(models.Invoice, InvoiceAdmin)
admin.site.register(models.Vehicle, VehicleAdmin)
