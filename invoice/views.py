from django.db.models import Sum
from django.db.models.functions import ExtractYear
from django.db.models.functions import ExtractMonth
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from .models import Invoice
from .forms import InvoiceForm, InvoiceFormEdit


# Create your views here.
def index(request):
    invoices = Invoice.objects.all().order_by('company_name', 'invoice_date', 'invoice_number')
    return render(request, 'invoice/index.html', {
        'invoices': invoices
    })


def view_invoice(request, id):
    invoice = Invoice.objects.get(pk=id)
    return HttpResponseRedirect(reverse('index'))


'''
def add(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            new_company_name = form.cleaned_data['company_name']
            new_invoice_number = form.cleaned_data['invoice_number']
            new_invoice_date = form.cleaned_data['invoice_date']
            new_freight_cost = form.cleaned_data['freight_cost']
            new_vat_rate = form.cleaned_data['vat_rate']
            new_vat_amount = form.cleaned_data['vat_amount']
            new_total_amount = form.cleaned_data['total_amount']
            new_payment_due_date = form.cleaned_data['payment_due_date']

            new_invoice = Invoice(
                company_name=new_company_name,
                invoice_number=new_invoice_number,
                invoice_date=new_invoice_date,
                freight_cost=new_freight_cost,
                vat_rate=new_vat_rate,
                vat_amount=new_vat_amount,
                total_amount=new_total_amount,
                payment_due_date=new_payment_due_date
            )
            new_invoice.save()
            return render(request, 'invoice/add.html', {
                'form': InvoiceForm(),
                'success': True
            })
    else:
        form = InvoiceForm()
    return render(request, 'invoice/add.html', {
        'form': InvoiceForm()
    })
'''


def add(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            new_invoice = form.save()

            # Se la richiesta è AJAX, restituiamo JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"success": True, "message": "Fattura aggiunta con successo!"})

            # Se non è AJAX, torniamo alla pagina normalmente
            return render(request, 'invoice/add.html', {
                'form': InvoiceForm(),
                'success': True
            })
        # Se il form non è valido, restituiamo gli errori in JSON se la richiesta è AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
    else:
        form = InvoiceForm()

    return render(request, 'invoice/add.html', {
        'form': form
    })


def edit(request, id):
    invoice = get_object_or_404(Invoice, id=id)
    form = InvoiceFormEdit(request.POST or None, instance=invoice)

    if request.method == "POST":
        # print("POST ricevuto:", request.POST)  # Debug
        if form.is_valid():

            invoice.vat_amount = invoice.freight_cost * (invoice.vat_rate / 100)
            invoice.total_amount = invoice.freight_cost + invoice.vat_amount
            form.save()

            # Controlla se è una richiesta AJAX
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": True})
            else:
                return redirect("index")  # Reindirizza solo per richieste normali
        else:
            # print("Errori form:", json.dumps(form.errors))  # Debug
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "errors": form.errors})

    return render(request, "invoice/edit.html", {"form": form, "invoice": invoice})


'''
def edit(request, id):
    invoice = Invoice.objects.get(pk=id)  # Recupera la fattura dal database

    if request.method == 'POST':
        form = InvoiceFormEdit(request.POST, instance=invoice)
        if form.is_valid():
            invoice = form.save(commit=False)

            invoice.vat_amount = invoice.freight_cost * (invoice.vat_rate / 100)
            invoice.total_amount = invoice.freight_cost + invoice.vat_amount

            invoice.save()  # Salva nel DB con i nuovi calcoli

            return render(request, 'invoice/edit.html', {
                'form': form,
                'success': True
            })
    else:
        form = InvoiceFormEdit(instance=invoice)

    return render(request, 'invoice/edit.html', {'form': form})
'''


def delete(request, id):
    if request.method == 'POST':
        invoice = Invoice.objects.get(pk=id)
        invoice.delete()
    return HttpResponseRedirect(reverse('index'))


'''
def list_invoice(request):
    return render(request, 'invoice/list_invoice.html', {
        'invoices': Invoice.objects.all()})
'''


def list_invoice(request):
    # Ottieni tutti i nomi di ragione sociale unici
    company_names = Invoice.objects.values('company_name').distinct()

    # Ottieni tutti gli anni unici dalle date delle fatture
    invoice_years = Invoice.objects.annotate(year=ExtractYear('invoice_date')).values('year').distinct()
    invoice_month = Invoice.objects.annotate(month=ExtractMonth('invoice_date')).values('month').distinct()

    context = {
        'company_names': company_names,
        'invoice_years': invoice_years
    }
    return render(request, 'invoice/list_invoice.html', context)


def filter_invoices(request):
    company_name = request.GET.get('company_name')
    year = request.GET.get('year')

    invoices = Invoice.objects.all()

    # Filtra per nome dell'azienda
    if company_name:
        invoices = invoices.filter(company_name=company_name)

    # Filtra per anno
    if year:
        invoices = invoices.filter(invoice_date__year=year)

    # Calcola la somma del fatturato
    revenue = invoices.aggregate(Sum('freight_cost'))['freight_cost__sum'] or 0

    revenue_iva = invoices.aggregate(Sum('vat_amount'))['vat_amount__sum'] or 0
    revenue_tot = invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # Restituisci i risultati come JSON
    invoice_data = list(invoices.values('company_name', 'invoice_number', 'invoice_date', 'freight_cost'))

    return JsonResponse({
        'invoices': invoice_data,
        'revenue': revenue,  # Aggiungi la somma del fatturato
        'revenue_iva': revenue_iva,  # totale iva
        'revenue_tot': revenue_tot  # fatturato con IVA
    })

