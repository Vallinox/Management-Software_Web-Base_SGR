from django.db import models
from datetime import date, timedelta



class Invoice(models.Model):
    company_name = models.CharField(max_length=100)  # Nome dell'azienda
    invoice_number = models.CharField(max_length=50, unique=True)  # Numero fattura, spesso alfanumerico
    invoice_date = models.DateField()  # Data della fattura
    freight_cost = models.DecimalField(max_digits=10, decimal_places=3, default=0.00)  # Imponibile
    vat_rate = models.DecimalField(max_digits=5, decimal_places=0)  # Aliquota IVA in percentuale (es. 22.00)
    vat_amount = models.DecimalField(max_digits=40, decimal_places=3)  # Importo IVA
    total_amount = models.DecimalField(max_digits=40, decimal_places=3)  # Totale fattura
    payment_due_date = models.DateField()  # Data di scadenza pagamento

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.company_name}"

    def formatted_invoice_date(self):
        return self.invoice_date.strftime("%d.%m.%Y")

class Vehicle(models.Model):
    VEHICLE_CATEGORIES = [
        ('motrice', 'Motrice'),
        ("trattore", "Trattore"),
        ('furgone', 'Furgone'),
        ('autovettura', 'Autovettura'),
        ('rimorchio', 'Rimorchio'),
        ('semirimorchio', 'Semirimorchio'),
    ]

    CONTRACT_TYPES = [
        ('leasing', 'Leasing'),
        ('proprietà', 'Di proprietà'),
    ]

    EUR_CATEGORIES = [
        ('EURO 2', 'EURO 2'),
        ('EURO 3', 'EURO 3'),
        ('EURO 4', 'EURO 4'),
        ('EURO 5', 'EURO 5'),
        ('EURO 6', 'EURO 6'),
    ]
    company_own = models.CharField(max_length=100)  # Nome dell'azienda
    plate = models.CharField(max_length=10)  # Targa
    vehicle_category = models.CharField(max_length=15, choices=VEHICLE_CATEGORIES)  # Categoria del mezzo
    eur_category = models.CharField(max_length=10, choices=EUR_CATEGORIES )  # Euro
    contract_type = models.CharField(max_length=15, choices=CONTRACT_TYPES)  # contratto tipo: leasing o di proprietà
    insurance_term_expires = models.DateField()  # Scadenza assicurazione
    review_deadline = models.DateField()  # Revisione assicurazione
    bollo_deadline = models.DateField() # Scadenza bollo
    aci_card_deadline = models.DateField() # Scadenza tessera ACI
    matched_driver = models.CharField(max_length=15) # Autista abbinato
    # matched_driver = models.ForeignKey("Driver", on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Vehicle {self.plate} - {self.company_own}"
    
    def formatted_vehicle_date(self): 
        return self.insurance_term_expires.strftime("%d.%m.%Y")
    
    def formatted_vehicle_date(self): 
        return self.review_deadline.strftime("%d.%m.%Y")
    
    def formatted_vehicle_date(self): 
        return self.bollo_deadline.strftime("%d.%m.%Y")
    
    def formatted_vehicle_date(self): 
        return self.aci_card_deadline.strftime("%d.%m.%Y")
    
    '''
    def is_insurance_expiring_soon(self):
        return self.insurance_term_expires <= date.today() + timedelta(days=30)'''