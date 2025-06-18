from django.db import models
from datetime import date, timedelta


class Invoice(models.Model):
    company_name = models.CharField(max_length=100)  # Nome dell'azienda
    invoice_number = models.CharField(
        max_length=50
    )  # Numero fattura, spesso alfanumerico
    invoice_date = models.DateField()  # Data della fattura
    freight_cost = models.DecimalField(
        max_digits=10, decimal_places=3, default=0.00
    )  # Imponibile
    vat_rate = models.DecimalField(
        max_digits=5, decimal_places=2
    )  # Aliquota IVA in percentuale (es. 22.00)
    vat_amount = models.DecimalField(max_digits=40, decimal_places=3)  # Importo IVA
    total_amount = models.DecimalField(
        max_digits=40, decimal_places=3
    )  # Totale fattura
    payment_due_date = models.DateField()  # Data di scadenza pagamento

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.company_name}"

    def formatted_invoice_date(self):
        return self.invoice_date.strftime("%d/%m/%Y")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company_name", "invoice_number", "invoice_date"],
                name="unique_invoice_number_date_company",
            )
        ]
