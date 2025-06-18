document.addEventListener("DOMContentLoaded", function () {
  document
    .getElementById("invoice-form")
    .addEventListener("submit", function (event) {
      event.preventDefault(); // Evita il reload della pagina

      let form = this;
      let formData = new FormData(form);

      fetch(form.action, {
        method: "POST",
        body: formData,
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            document.getElementById("success-message").classList.remove("d-none");
            form.reset(); // Pulisce il form dopo l'invio
          } else {
            alert("Errore nell'invio: " + JSON.stringify(data.errors));
          }
        })
        .catch((error) => console.error("Errore:", error));
    });
});


document.addEventListener("DOMContentLoaded", function () {
    const pdfUploadForm = document.getElementById("pdf-upload-form");
    const invoiceForm = document.getElementById("invoice-form");
    const pdfUploadFeedback = document.getElementById("pdf-upload-feedback");
    const successMessage = document.getElementById("success-message");
    const manualFillBtn = document.getElementById("manual-fill-btn");

    // Funzione per popolare il form con i dati estratti
    function populateForm(data) {
        const fieldMapping = {
            'company_name': 'id_company_name',
            'invoice_number': 'id_invoice_number',
            'invoice_date': 'id_invoice_date',
            'freight_cost': 'id_freight_cost',
            'vat_rate': 'id_vat_rate',
            'vat_amount': 'id_vat_amount',
            'total_amount': 'id_total_amount',
            'payment_due_date': 'id_payment_due_date',
        };

        for (const key in data) {
            if (fieldMapping[key]) {
                const inputElement = document.getElementById(fieldMapping[key]);
                if (inputElement) {
                    inputElement.value = data[key];
                    inputElement.classList.add('pre-filled');
                } else {
                    console.warn(`Elemento input con ID ${fieldMapping[key]} non trovato.`);
                }
            } else {
                console.warn(`Mappatura mancante per la chiave: ${key}`);
            }
        }
        pdfUploadFeedback.innerHTML = '<div class="alert alert-success">Dati caricati e form compilato automaticamente! Controlla i campi.</div>';
    }

    function resetAllForms() {
        if (invoiceForm) invoiceForm.reset();
        if (pdfUploadForm) pdfUploadForm.reset();
        if (pdfUploadFeedback) pdfUploadFeedback.innerHTML = '';
        if (successMessage) successMessage.classList.add('d-none');
        document.querySelectorAll('.pre-filled').forEach(el => el.classList.remove('pre-filled'));
    }

    // --- Gestione Caricamento PDF ---
    if (pdfUploadForm) {
        pdfUploadForm.addEventListener("submit", function (event) {
            console.log("PDF upload form submitted!");
            event.preventDefault();

            const fileInput = document.getElementById("id_pdf_file");
            if (fileInput.files.length === 0) {
                pdfUploadFeedback.innerHTML = '<div class="alert alert-warning">Seleziona un file PDF.</div>';
                return;
            }

            let formData = new FormData(pdfUploadForm);
            pdfUploadFeedback.innerHTML = '<div class="alert alert-info">Caricamento e analisi PDF in corso...</div>';

            fetch(uploadPdfUrl, {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
                    "X-Requested-With": "XMLHttpRequest",
                },
            })
            .then(response => response.text().then(text => ({
                ok: response.ok,
                status: response.status,
                text: text
            })))
            .then(responseInfo => {
                let data;
                try {
                    data = JSON.parse(responseInfo.text);
                } catch (e) {
                    data = { error: responseInfo.text || 'Errore sconosciuto dal server.' };
                }

                if (responseInfo.ok) {
                    if (data.error) {
                        pdfUploadFeedback.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                    } else {
                        populateForm(data);
                    }
                } else {
                    const errorMessage = data.error || `Errore del server: ${responseInfo.status} - ${responseInfo.text}`;
                    pdfUploadFeedback.innerHTML = `<div class="alert alert-danger">Errore durante l'elaborazione del PDF: ${errorMessage}</div>`;
                }
            })
            .catch(error => {
                console.error("Errore durante l'upload o l'estrazione del PDF:", error);
                pdfUploadFeedback.innerHTML = `<div class="alert alert-danger">Errore di rete o del client durante l'elaborazione del PDF: ${error.message || error}</div>`;
            });
        });
    }

    // --- Gestione Compila Manualmente ---
    if (manualFillBtn) {
        manualFillBtn.addEventListener('click', function() {
            resetAllForms();
            pdfUploadFeedback.innerHTML = '<div class="alert alert-info">Procedi con l\'inserimento manuale dei dati.</div>';
        });
    }

    // --- Gestione Sottomissione Form Fattura ---
    if (invoiceForm) {
        invoiceForm.addEventListener("submit", function (event) {
            console.log("Invoice form submitted!");
            event.preventDefault();

            let form = this;
            let formData = new FormData(form);

            fetch(form.action, {
                method: "POST",
                body: formData,
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                },
            })
            .then(response => response.text().then(text => ({
                ok: response.ok,
                status: response.status,
                text: text
            })))
            .then(responseInfo => {
                let data;
                try {
                    data = JSON.parse(responseInfo.text);
                } catch (e) {
                    data = { success: false, errors: { non_field_errors: [responseInfo.text || 'Errore sconosciuto dal server.'] } };
                }

                if (responseInfo.ok) {
                    if (data.success) {
                        if (successMessage) successMessage.classList.remove("d-none");
                        resetAllForms();
                    } else {
                        let errorMessages = "Errore nell'invio:\n";
                        for (const field in data.errors) {
                            errorMessages += `${field}: ${data.errors[field].join(', ')}\n`;
                        }
                        alert(errorMessages);
                    }
                } else {
                    let errorMessages = "Si è verificato un errore durante l'invio del form:\n";
                    if (data.errors) {
                        for (const field in data.errors) {
                            errorMessages += `${field}: ${data.errors[field].join(', ')}\n`;
                        }
                    } else if (data.error) {
                        errorMessages += data.error;
                    } else {
                        errorMessages += `Errore del server: ${responseInfo.status} - ${responseInfo.text}`;
                    }
                    alert(errorMessages);
                }
            })
            .catch(error => {
                console.error("Errore:", error);
                alert(`Si è verificato un errore di rete o del client durante l'invio del form: ${error.message || error}`);
            });
        });
    }
});
