from decimal import ROUND_HALF_UP, Decimal
from django import forms

from .models import Invoice


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['company_name', 'invoice_number', 'invoice_date', 'freight_cost',
                  'vat_rate', 'vat_amount', 'total_amount', 'payment_due_date']
        labels = {
            'company_name': 'Ragione sociale',
            'invoice_number': 'Num. Fatt.',
            'invoice_date': 'Data Fatt.',
            'freight_cost': 'Imponibile',
            'vat_rate': 'IVA%',
            'vat_amount': 'Tot. IVA',
            'total_amount': 'Tot. Fatt.',
            'payment_due_date': 'Data saldo',
        }
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), # Added type="date" for better UX
            'freight_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}), # Added step for precision
            'vat_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}), # Added step for precision
            'vat_amount': forms.HiddenInput(),
            'total_amount': forms.HiddenInput(),
            'payment_due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), # Added type="date"
        }

    vat_amount = forms.DecimalField(required=False, widget=forms.HiddenInput())
    total_amount = forms.DecimalField(required=False, widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super().clean()
        invoice_number = cleaned_data.get('invoice_number')
        invoice_date = cleaned_data.get('invoice_date')

        # Check for uniqueness only if both fields are present
        if invoice_number and invoice_date:
            # Exclude current instance in edit view to allow saving without unique constraint error
            qs = Invoice.objects.filter(invoice_number=invoice_number, invoice_date=invoice_date)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise forms.ValidationError("Fattura con questo numero e data esiste già.")

        freight_cost = cleaned_data.get('freight_cost')
        vat_rate = cleaned_data.get('vat_rate')

        if freight_cost is not None and vat_rate is not None:
            vat_amount = (freight_cost * (vat_rate / 100)).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
            total_amount = (freight_cost + vat_amount).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)

            cleaned_data['vat_amount'] = vat_amount
            cleaned_data['total_amount'] = total_amount
        elif freight_cost is None and vat_rate is None:
            # If both are None, set calculated fields to None as well
            cleaned_data['vat_amount'] = None
            cleaned_data['total_amount'] = None
        else:
            # If one is present and the other is not, it's an incomplete calculation
            # You might want to add a validation error here or just leave them None
            cleaned_data['vat_amount'] = None
            cleaned_data['total_amount'] = None
            # raise forms.ValidationError("Imponibile e/o Aliquota IVA non validi per il calcolo.")

        return cleaned_data

'''
class InvoiceFormEdit(forms.ModelForm):
    class Meta(InvoiceForm.Meta):
        exclude = ['vat_amount', 'total_amount']
'''       
        
class InvoiceFormEdit(forms.ModelForm):
    class Meta(InvoiceForm.Meta): # Eredita Meta da InvoiceForm per coerenza
        fields = ['company_name', 'invoice_number', 'invoice_date', 'freight_cost',
                  'vat_rate', 'vat_amount', 'total_amount', 'payment_due_date']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            # *** MODIFICA QUI PER LA DATA ***
            'invoice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'freight_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'vat_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'vat_amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            # *** MODIFICA QUI PER LA DATA ***
            'payment_due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
        }

    def clean(self):
        cleaned_data = super().clean()
        # ... (il resto del tuo metodo clean)
        freight_cost = cleaned_data.get('freight_cost')
        vat_rate = cleaned_data.get('vat_rate')

        if freight_cost is not None and vat_rate is not None:
            vat_amount = (freight_cost * (vat_rate / 100)).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
            total_amount = (freight_cost + vat_amount).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
            cleaned_data['vat_amount'] = vat_amount
            cleaned_data['total_amount'] = total_amount
        else:
            # È importante gestire il caso in cui questi campi siano None dopo il clean
            # altrimenti potresti avere KeyError o TypeError
            cleaned_data['vat_amount'] = None
            cleaned_data['total_amount'] = None

        return cleaned_data