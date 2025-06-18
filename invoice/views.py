import datetime
from django.db.models import Sum
from django.db.models.functions import ExtractYear
from django.db.models.functions import ExtractMonth
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages # Per messaggi di feedback


from .models import Invoice
from .forms import InvoiceForm, InvoiceFormEdit

import io
from decimal import Decimal
import pdfquery
import re


# Create your views here.
def index(request):
    invoices = Invoice.objects.all().order_by(
        "company_name", "invoice_date", "invoice_number"
    )
    return render(request, "invoice/index.html", {"invoices": invoices})


def view_invoice(request, id):
    invoice = Invoice.objects.get(pk=id)
    return HttpResponseRedirect(reverse("index"))

def add(request):
    if request.method == "POST":
        form = InvoiceForm(request.POST)
        if form.is_valid():
            new_invoice = form.save()

            # Se la richiesta è AJAX, restituiamo JSON
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"success": True, "message": "Fattura aggiunta con successo!"}
                )

            # Se non è AJAX, torniamo alla pagina normalmente
            return render(
                request, "invoice/add.html", {"form": InvoiceForm(), "success": True}
            )
        # Se il form non è valido, restituiamo gli errori in JSON se la richiesta è AJAX
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
    else:
        form = InvoiceForm()

    return render(request, "invoice/add.html", {"form": form})


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


def delete(request, id):
    if request.method == "POST":
        invoice = Invoice.objects.get(pk=id)
        invoice.delete()
    return HttpResponseRedirect(reverse("index"))

def list_invoice(request):
    # Ottieni tutti i nomi di ragione sociale unici
    company_names = Invoice.objects.values("company_name").distinct()

    # Ottieni tutti gli anni unici dalle date delle fatture
    invoice_years = (
        Invoice.objects.annotate(year=ExtractYear("invoice_date"))
        .values("year")
        .distinct()
    )
    invoice_month = (
        Invoice.objects.annotate(month=ExtractMonth("invoice_date"))
        .values("month")
        .distinct()
    )

    context = {"company_names": company_names, "invoice_years": invoice_years}
    return render(request, "invoice/list_invoice.html", context)


def filter_invoices(request):
    company_name = request.GET.get("company_name")
    year = request.GET.get("year")

    invoices = Invoice.objects.all()

    # Filtra per nome dell'azienda
    if company_name:
        invoices = invoices.filter(company_name=company_name)

    # Filtra per anno
    if year:
        invoices = invoices.filter(invoice_date__year=year)

    # Calcola la somma del fatturato
    revenue = invoices.aggregate(Sum("freight_cost"))["freight_cost__sum"] or 0

    revenue_iva = invoices.aggregate(Sum("vat_amount"))["vat_amount__sum"] or 0
    revenue_tot = invoices.aggregate(Sum("total_amount"))["total_amount__sum"] or 0

    # Restituisci i risultati come JSON
    invoice_data = list(
        invoices.values(
            "company_name", "invoice_number", "invoice_date", "freight_cost"
        )
    )

    return JsonResponse(
        {
            "invoices": invoice_data,
            "revenue": revenue,  # Aggiungi la somma del fatturato
            "revenue_iva": revenue_iva,  # totale iva
            "revenue_tot": revenue_tot,  # fatturato con IVA
        }
    )



def parse_euro(euro_str: str) -> Decimal:
    """
    Converte una stringa in formato italiano (es. '9.098,00') in Decimal.
    Gestisce punti per migliaia e virgole decimali.
    """
    clean = euro_str.replace(".", "").replace(",", ".")
    return Decimal(clean)


# Modifica qui: aggiungi 'request' come argomento
def extract_data_with_pdfquery(pdf_file_object, request=None): # Aggiungi request con un default None
    extracted_data = {
        'company_name': '',
        'invoice_number': '',
        'invoice_date': '',
        'freight_cost': '',
        'vat_rate': '',
        'vat_amount': '',
        'total_amount': '.',
        'payment_due_date': '',
    }
    try:
        pdf = pdfquery.PDFQuery(pdf_file_object)
        pdf.load()
        # convert the pdf to XML
        pdf.tree.write("invoice/media/temp/fattura.xml", pretty_print=True)
        print("XML file created successfully.", pdf)
        
        own_c = (lambda s: "TSVG S.r.l" if s.upper().startswith("TSVG") else "Logistica Trasporti Segreto S.r.l" 
                             if s.upper().startswith("LOGISTICA") else s)
        own_company_text = pdf.pq('LTTextLineHorizontal:in_bbox("24.0, 763.648, 508.8, 771.648")')
        extracted_data["company_name"] = own_c(own_company_text.text()) # Aggiunto .text() per prendere il contenuto del tag

        # Numero Fattura
        extracted_data["invoice_number"] = (pdf.pq('LTTextLineHorizontal:in_bbox("122.76, 695.067, 154.752, 702.987")').text().replace(" ", ""))

        # Data Fattura
        invoice_date_raw = pdf.pq('LTTextLineHorizontal:in_bbox("211.68, 695.067, 253.392, 702.987")').text().replace(" ", "")
        try:
            extracted_data["invoice_date"] = datetime.datetime.strptime(invoice_date_raw, '%d/%m/%Y').strftime('%Y-%m-%d')
        except ValueError:
            if request: # Controlla se request è presente prima di chiamare messages.warning
                messages.warning(request, f"Formato data fattura non valido: {invoice_date_raw}. Lasciato vuoto.")
            extracted_data["invoice_date"] = ""

        # Fornitore (destinatario) - sembra che questo campo non venga usato nel form InvoiceForm, ma lo lascio per completezza
        # f_invoice = (lambda s: "S.D.M. S.r.l" if s.upper().startswith("S.D.M.") else "BRT S.P.A" if s.upper().startswith("BRT") else s)
        # forni_invoice = f_invoice(pdf.pq('LTTextLineHorizontal:in_bbox("300.369, 764.772, 469.414, 773.412")').text().replace(" ", ""))

        # Data Scadenza Pagamento
        expires_invoice_raw = pdf.pq('LTTextLineHorizontal:in_bbox("300.358, 619.107, 444.912, 627.027")').text().replace(" ", "")
        try:
            # Assumo che sia 'Scadenza: DD/MM/YYYY'
            payment_due_date_str = expires_invoice_raw.split(":")[1].strip()
            extracted_data["payment_due_date"] = datetime.datetime.strptime(payment_due_date_str, '%d/%m/%Y').strftime('%Y-%m-%d')
        except (IndexError, ValueError):
            if request: # Controlla se request è presente
                messages.warning(request, f"Formato data scadenza non valido: {expires_invoice_raw}. Lasciato vuoto.")
            extracted_data["payment_due_date"] = ""

        # Costo Spedizione (Imponibile)
        tot_invoice_imponibile_raw = pdf.pq('LTTextLineHorizontal:contains("Totale imponibile")').text()
        match_freight_cost = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})", tot_invoice_imponibile_raw)
        if match_freight_cost:
            extracted_data["freight_cost"] = str(parse_euro(match_freight_cost.group(1))) # Converti in stringa per JSON
        else:
            if request: # Controlla se request è presente
                messages.warning(request, f"Costo imponibile non trovato nel testo: '{tot_invoice_imponibile_raw}'. Lasciato vuoto.")
            extracted_data["freight_cost"] = ""

        # Aliquota IVA
        vat_rate_raw = pdf.pq('LTTextLineHorizontal:in_bbox("505.08, 532.551, 518.404, 539.391")').text().replace(" ", "").replace("%", "")
        try:
            extracted_data["vat_rate"] = str(Decimal(vat_rate_raw)) # Converti in Decimal e poi stringa
        except Exception:
            if request: # Controlla se request è presente
                messages.warning(request, f"Aliquota IVA non valida: {vat_rate_raw}. Lasciata vuota.")
            extracted_data["vat_rate"] = ""
        
        # Calcolo IVA e Totale (se i valori precedenti sono stati estratti correttamente)
        try:
            freight_cost_decimal = Decimal(extracted_data['freight_cost']) if extracted_data['freight_cost'] else Decimal(0)
            vat_rate_decimal = Decimal(extracted_data['vat_rate']) if extracted_data['vat_rate'] else Decimal(0)

            extracted_data["vat_amount"] = str(freight_cost_decimal * (vat_rate_decimal / 100))
            extracted_data["total_amount"] = str(freight_cost_decimal + Decimal(extracted_data["vat_amount"]))
        except Exception as calc_e:
            if request: # Controlla se request è presente
                messages.warning(request, f"Errore nel calcolo IVA/Totale: {calc_e}. Campi calcolati lasciati vuoti.")
            extracted_data["vat_amount"] = ""
            extracted_data["total_amount"] = ""

    except Exception as e:
        if request: # Controlla se request è presente
            messages.error(request, f"Errore generale durante l'estrazione dal PDF: {e}")
        # In caso di errore grave, alcuni campi potrebbero rimanere vuoti
    
    return extracted_data

# --- Nuova View per l'upload e l'estrazione AJAX ---
def upload_pdf_ajax_process(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        pdf_file = request.FILES['pdf_file']
        try:
            # Modifica qui: passa l'oggetto request a extract_data_with_pdfquery
            data = extract_data_with_pdfquery(pdf_file, request)
            return JsonResponse(data)
        except Exception as e:
            # Anche qui, se vuoi usare i messaggi, devi passarli
            # Dato che questa è una risposta AJAX, è meglio restituire l'errore nel JSON
            # e lasciare che il JS lo gestisca visivamente.
            return JsonResponse({"error": f"Errore durante l'estrazione: {str(e)}"}, status=500)
    return JsonResponse({"error": "Nessun file PDF fornito o metodo non supportato"}, status=400)
