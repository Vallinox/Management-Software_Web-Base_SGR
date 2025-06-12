from django import forms

from .models import Invoice


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        # fields = '__all__'
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
            'invoice_date': forms.DateInput(attrs={'class': 'form-control'}),
            'freight_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'vat_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'vat_amount': forms.HiddenInput(),  # Nascosto
            'total_amount': forms.HiddenInput(),
            'payment_due_date': forms.DateInput(attrs={'class': 'form-control'}),
        }

    vat_amount = forms.DecimalField(required=False, widget=forms.HiddenInput())
    total_amount = forms.DecimalField(required=False, widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super().clean()

        freight_cost = cleaned_data.get('freight_cost')
        vat_rate = cleaned_data.get('vat_rate')

        # Calcolare l'IVA e il totale
        if freight_cost and vat_rate:
            vat_amount = round(freight_cost * (vat_rate / 100), 3)
            total_amount = round(freight_cost + vat_amount, 3)


            # Aggiungi i calcoli ai dati puliti
            cleaned_data['vat_amount'] = vat_amount
            cleaned_data['total_amount'] = total_amount

        return cleaned_data


class InvoiceFormEdit(forms.ModelForm):
    class Meta(InvoiceForm.Meta):
        exclude = ['vat_amount', 'total_amount']