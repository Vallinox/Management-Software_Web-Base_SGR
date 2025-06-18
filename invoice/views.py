from django.db.models import Sum
from django.db.models.functions import ExtractYear
from django.db.models.functions import ExtractMonth
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages

import invoice  # Per messaggi di feedback


from .models import Invoice
from .forms import InvoiceForm, InvoiceFormEdit

from decimal import ROUND_HALF_UP, Decimal
import datetime
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
                    {
                        "success": True,
                        "message": "Fattura aggiunta con successo!"
                    }
                )
            else:
                messages.success(request, "Fattura aggiunta con successo!")
                return render(
                    request,
                    "invoice/add.html",
                    {"form": InvoiceForm(), "success": True},
                )
        else:
            # Se il form non è valido, restituiamo gli errori in JSON se la richiesta è AJAX
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": False,
                        "errors": form.errors,
                        "message": "Ci sono errori nel form. Si prega di correggerli.",
                    },
                    status=400,
                )
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                return render(request, "invoice/add.html", {"form": form})
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
                return JsonResponse(
                    {"success": True, "message": "Fattura modificata con successo!"}
                )
            else:
                messages.success(request, "Fattura modificata con successo!")
                return redirect("index")
        else:
            # print("Errori form:", json.dumps(form.errors))  # Debug
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "success": False,
                        "errors": form.errors,
                        "message": "Ci sono errori nel form. Si prega di correggerli.",
                    },
                    status=400,
                )
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                return render(
                    request, "invoice/edit.html", {"form": form, "invoice": invoice}
                )

    return render(request, "invoice/edit.html", {"form": form, "invoice": invoice})


def delete(request, id):
    if request.method == "POST":
        invoice = get_object_or_404(
            Invoice, pk=id
        )  # Use get_object_or_404 for robustness
        invoice.delete()
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {"success": True, "message": "Fattura eliminata con successo!"}
            )
        else:
            messages.success(request, "Fattura eliminata con successo!")
            return HttpResponseRedirect(reverse("index"))
    # Handle GET request to delete, or just redirect
    return HttpResponseRedirect(reverse("index"))


def list_invoice(request):
    company_names = Invoice.objects.values("company_name").distinct()
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

    if company_name:
        invoices = invoices.filter(company_name=company_name)

    if year:
        invoices = invoices.filter(invoice_date__year=year)

    revenue = invoices.aggregate(Sum("freight_cost"))["freight_cost__sum"] or 0
    revenue_iva = invoices.aggregate(Sum("vat_amount"))["vat_amount__sum"] or 0
    revenue_tot = invoices.aggregate(Sum("total_amount"))["total_amount__sum"] or 0

    invoice_data = list(
        invoices.values(
            "company_name", "invoice_number", "invoice_date", "freight_cost"
        )
    )

    return JsonResponse(
        {
            "invoices": invoice_data,
            "revenue": revenue,
            "revenue_iva": revenue_iva,
            "revenue_tot": revenue_tot,
        }
    )


def parse_euro(euro_str: str) -> Decimal:
    clean = euro_str.replace(".", "").replace(",", ".")
    return Decimal(clean)


def extract_data_with_pdfquery(pdf_file_object):
    # This function should NOT use django.contrib.messages directly.
    # Instead, it should return an additional list of messages/warnings
    # that the AJAX view will then include in the JsonResponse.
    extracted_data = {
        "company_name": "",
        "invoice_number": "",
        "invoice_date": "",
        "freight_cost": None,  # Use None for missing numeric values
        "vat_rate": None,
        "vat_amount": None,
        "total_amount": None,
        "payment_due_date": "",
    }
    # List to collect messages for the user
    user_messages = []

    try:
        pdf = pdfquery.PDFQuery(pdf_file_object)
        pdf.load()
        # convert the pdf to XML
        pdf.tree.write("invoice/media/temp/fattura.xml", pretty_print=True)
        print("XML file created successfully.", pdf)

        # Company Name
        own_c = (
            lambda s: "TSVG S.r.l"
            if s.upper().startswith("TSVG")
            else "Logistica Trasporti Segreto S.r.l"
            if s.upper().startswith("LOGISTICA")
            else s
        )
        own_company_text_element = pdf.pq(
            'LTTextLineHorizontal:in_bbox("24.0, 763.648, 508.8, 771.648")'
        )
        extracted_data["company_name"] = (
            own_c(own_company_text_element.text().strip())
            if own_company_text_element
            else ""
        )

        # Invoice Number
        invoice_number_element = pdf.pq(
            'LTTextLineHorizontal:in_bbox("122.76, 695.067, 154.752, 702.987")'
        )
        extracted_data["invoice_number"] = (
            invoice_number_element.text().replace(" ", "").strip()
            if invoice_number_element
            else ""
        )

        # Invoice Date
        invoice_date_element = pdf.pq(
            'LTTextLineHorizontal:in_bbox("211.68, 695.067, 253.392, 702.987")'
        )
        invoice_date_raw = (
            invoice_date_element.text().replace(" ", "").strip()
            if invoice_date_element
            else ""
        )
        try:
            extracted_data["invoice_date"] = datetime.datetime.strptime(
                invoice_date_raw, "%d/%m/%Y"
            ).strftime("%Y-%m-%d")
        except ValueError:
            user_messages.append(
                {
                    "type": "warning",
                    "text": f"Formato data fattura non valido: '{invoice_date_raw}'. Campo lasciato vuoto.",
                }
            )
            extracted_data["invoice_date"] = ""

        # Payment Due Date
        expires_invoice_element = pdf.pq(
            'LTTextLineHorizontal:in_bbox("300.358, 619.107, 444.912, 627.027")'
        )
        expires_invoice_raw = (
            expires_invoice_element.text().replace(" ", "").strip()
            if expires_invoice_element
            else ""
        )
        try:
            payment_due_date_str = expires_invoice_raw.split(":")[1].strip()
            extracted_data["payment_due_date"] = datetime.datetime.strptime(
                payment_due_date_str, "%d/%m/%Y"
            ).strftime("%Y-%m-%d")
        except (IndexError, ValueError):
            user_messages.append(
                {
                    "type": "warning",
                    "text": f"Formato data scadenza pagamento non valido: '{expires_invoice_raw}'. Campo lasciato vuoto.",
                }
            )
            extracted_data["payment_due_date"] = ""

        # Freight Cost (Imponibile)
        tot_invoice_imponibile_element = pdf.pq(
            'LTTextLineHorizontal:contains("Totale imponibile")'
        )
        tot_invoice_imponibile_raw = (
            tot_invoice_imponibile_element.text().strip()
            if tot_invoice_imponibile_element
            else ""
        )
        match_freight_cost = re.search(
            r"(\d{1,3}(?:\.\d{3})*,\d{2})", tot_invoice_imponibile_raw
        )
        if match_freight_cost:
            extracted_data["freight_cost"] = parse_euro(
                match_freight_cost.group(1)
            ).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        else:
            user_messages.append(
                {
                    "type": "warning",
                    "text": f"Costo imponibile non trovato nel testo: '{tot_invoice_imponibile_raw}'. Campo lasciato vuoto.",
                }
            )
            extracted_data["freight_cost"] = None

        # VAT Rate
        vat_rate_element = pdf.pq(
            'LTTextLineHorizontal:in_bbox("505.08, 532.551, 518.404, 539.391")'
        )
        vat_rate_raw = (
            vat_rate_element.text().replace(" ", "").replace("%", "").strip()
            if vat_rate_element
            else ""
        )
        try:
            vat_rate_decimal = Decimal(vat_rate_raw).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            extracted_data["vat_rate"] = vat_rate_decimal
        except Exception:
            user_messages.append(
                {
                    "type": "warning",
                    "text": f"Aliquota IVA non valida: '{vat_rate_raw}'. Campo lasciato vuoto.",
                }
            )
            extracted_data["vat_rate"] = None

        # Calculate VAT Amount and Total Amount
        try:
            freight_cost_decimal = (
                extracted_data["freight_cost"]
                if extracted_data["freight_cost"] is not None
                else Decimal(0)
            )
            vat_rate_decimal = (
                extracted_data["vat_rate"]
                if extracted_data["vat_rate"] is not None
                else Decimal(0)
            )

            vat_amount = (freight_cost_decimal * vat_rate_decimal / 100).quantize(
                Decimal("0.001"), rounding=ROUND_HALF_UP
            )
            total_amount = (freight_cost_decimal + vat_amount).quantize(
                Decimal("0.001"), rounding=ROUND_HALF_UP
            )

            extracted_data["vat_amount"] = vat_amount
            extracted_data["total_amount"] = total_amount
        except Exception as calc_e:
            user_messages.append(
                {
                    "type": "warning",
                    "text": f"Errore nel calcolo IVA/Totale: {calc_e}. Campi calcolati lasciati vuoti.",
                }
            )
            extracted_data["vat_amount"] = None
            extracted_data["total_amount"] = None

    except Exception as e:
        user_messages.append(
            {
                "type": "error",
                "text": f"Errore generale durante l'estrazione dal PDF: {str(e)}",
            }
        )
        # In case of severe error, ensure numeric fields are None
        extracted_data["freight_cost"] = None
        extracted_data["vat_rate"] = None
        extracted_data["vat_amount"] = None
        extracted_data["total_amount"] = None

    # Convert Decimal objects to string for JSON serialization
    for key, value in extracted_data.items():
        if isinstance(value, Decimal):
            extracted_data[key] = str(value)

    return extracted_data, user_messages


def upload_pdf_ajax_process(request):
    if request.method == "POST" and request.FILES.get("pdf_file"):
        pdf_file = request.FILES["pdf_file"]
        all_messages = []  # Collect all messages here

        try:
            extracted_data, func_messages = extract_data_with_pdfquery(pdf_file)
            all_messages.extend(func_messages)

            response_data = {
                "success": True,
                "data": extracted_data,
                "messages": all_messages,  # Include messages from extraction
            }
            return JsonResponse(response_data)
        except Exception as e:
            all_messages.append(
                {
                    "type": "error",
                    "text": f"Errore imprevisto durante l'upload o l'estrazione: {str(e)}",
                }
            )
            return JsonResponse(
                {"success": False, "messages": all_messages}, status=500
            )

    all_messages = [
        {"type": "error", "text": "Nessun file PDF fornito o metodo non supportato."}
    ]
    return JsonResponse({"success": False, "messages": all_messages}, status=400)
