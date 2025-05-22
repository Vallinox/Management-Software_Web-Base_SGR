from django.contrib import admin
from . import models
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "company_name",
        "invoice_number",
        "invoice_date",
        "freight_cost",
        "vat_rate",
        "vat_amount",
        "total_amount",
        "payment_due_date",
    ]


# Register your models here.
admin.site.register(models.Invoice, InvoiceAdmin)
