from django import forms

from .models import Vehicle


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        # fields = '__all__'
        fields = [
            "company_own",
            "plate",
            "vehicle_category",
            "eur_category",
            "contract_type",
            "insurance_term_expires",
            "review_deadline",
            "bollo_deadline",
            "aci_card_deadline",
        ]
        labels = {
            "company_own": "Ragione sociale",
            "plate": "Targa",
            "vehicle_category": "Categoria mezzo",
            "eur_category": "Euro",
            "contract_type": "Tipo di contratto",
            "insurance_term_expires": "Scadenza assicurazione",
            "review_deadline": "Scadenza revisione",
            "bollo_deadline": "Scadenza bollo",
            "aci_card_deadline": "Scadenza tessera ACI",
        }
        widgets = {
            "company_own": forms.TextInput(attrs={"class": "form-control"}),
            "plate": forms.TextInput(attrs={"class": "form-control"}),
            "vehicle_category": forms.Select(attrs={"class": "form-control"}),
            "eur_category": forms.Select(attrs={"class": "form-control"}),
            "contract_type": forms.Select(attrs={"class": "form-control"}),
            "insurance_term_expires": forms.DateInput(attrs={"class": "form-control"}),
            "review_deadline": forms.DateInput(attrs={"class": "form-control"}),
            "bollo_deadline": forms.DateInput(attrs={"class": "form-control"}),
            "aci_card_deadline": forms.DateInput(attrs={"class": "form-control"}),
        }
