document.addEventListener("DOMContentLoaded", function () {
    const pdfUploadForm = document.getElementById("pdf-upload-form");
    const invoiceForm = document.getElementById("invoice-form");
    const pdfUploadFeedback = document.getElementById("pdf-upload-feedback");
    const successMessageContainer = document.getElementById("success-message"); // Renamed for clarity
    const manualFillBtn = document.getElementById("manual-fill-btn");

    // Centralized function to display messages
    function displayFeedbackMessage(container, message, type) {
        let alertClass = '';
        switch (type) {
            case 'success':
                alertClass = 'alert-success';
                break;
            case 'warning':
                alertClass = 'alert-warning';
                break;
            case 'error':
                alertClass = 'alert-danger';
                break;
            case 'info':
            default:
                alertClass = 'alert-info';
                break;
        }
        container.innerHTML = `<div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                                   ${message}
                                   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                               </div>`;
        container.classList.remove('d-none'); // Ensure container is visible
        container.scrollIntoView({ behavior: 'smooth', block: 'start' }); // Scroll to message
    }

    // Function to populate the form with extracted data
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
                    if (key === 'vat_rate') { // <--- Specific handling for vat_rate
                        // Ensure vat_rate is formatted to 2 decimal places as a string
                        inputElement.value = parseFloat(data[key]).toFixed(2);
                    } else if (['freight_cost', 'vat_amount', 'total_amount'].includes(key)) {
                        // These fields allow 3 decimal places
                        inputElement.value = parseFloat(data[key]).toFixed(3);
                    } else {
                        inputElement.value = data[key];
                    }
                    inputElement.classList.add('pre-filled');
                } else {
                    console.warn(`Elemento input con ID ${fieldMapping[key]} non trovato.`);
                }
            } else {
                console.warn(`Mappatura mancante per la chiave: ${key}`);
            }
        }
        // Specific success message for PDF upload
        displayFeedbackMessage(pdfUploadFeedback, 'Dati caricati e form compilato automaticamente! Controlla i campi.', 'success');
    }

    // Function to reset the form and PDF upload feedback
    function resetAllForms() {
        if (invoiceForm) invoiceForm.reset();
        if (pdfUploadForm) pdfUploadForm.reset();
        if (pdfUploadFeedback) pdfUploadFeedback.innerHTML = ''; // Clear PDF feedback
        if (successMessageContainer) successMessageContainer.classList.add('d-none'); // Hide the main success message
        document.querySelectorAll('.pre-filled').forEach(el => el.classList.remove('pre-filled'));
    }

    // --- PDF Upload Handling ---
    if (pdfUploadForm) {
        pdfUploadForm.addEventListener("submit", function (event) {
            event.preventDefault();
            pdfUploadFeedback.innerHTML = ''; // Clear previous messages

            const fileInput = document.getElementById("id_pdf_file");
            if (fileInput.files.length === 0) {
                displayFeedbackMessage(pdfUploadFeedback, 'Seleziona un file PDF.', 'warning');
                return;
            }

            let formData = new FormData(pdfUploadForm);
            displayFeedbackMessage(pdfUploadFeedback, 'Caricamento e analisi PDF in corso...', 'info');

            fetch(uploadPdfUrl, { // uploadPdfUrl is defined in the HTML template
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
                    "X-Requested-With": "XMLHttpRequest",
                },
            })
            .then(response => {
                // Ensure the response is always read as text once
                return response.text().then(text => ({
                    ok: response.ok,
                    status: response.status,
                    text: text
                }));
            })
            .then(responseInfo => {
                let data;
                try {
                    data = JSON.parse(responseInfo.text);
                } catch (e) {
                    console.error("Failed to parse JSON response:", responseInfo.text, e);
                    // Treat non-JSON response as a general error
                    data = { success: false, messages: [{ type: 'error', text: 'Risposta non valida dal server: ' + responseInfo.text }] };
                }

                if (responseInfo.ok && data.success) {
                    populateForm(data.data); // 'data' now contains 'data' and 'messages' keys
                    // Display any additional messages from the extraction process
                    if (data.messages && data.messages.length > 0) {
                        data.messages.forEach(msg => {
                            displayFeedbackMessage(pdfUploadFeedback, msg.text, msg.type);
                        });
                    }
                } else {
                    // Handle server-side errors or success=false
                    let errorMessage = 'Errore sconosciuto durante l\'elaborazione del PDF.';
                    if (data.messages && data.messages.length > 0) {
                        // Display all messages from the server
                        data.messages.forEach(msg => {
                            displayFeedbackMessage(pdfUploadFeedback, msg.text, msg.type);
                        });
                        errorMessage = data.messages.map(msg => msg.text).join('<br>'); // For console/alert fallback
                    } else if (data.error) { // Fallback for old error format
                         displayFeedbackMessage(pdfUploadFeedback, data.error, 'error');
                         errorMessage = data.error;
                    } else {
                        displayFeedbackMessage(pdfUploadFeedback, `Errore del server: ${responseInfo.status} - ${responseInfo.text}`, 'error');
                        errorMessage = `Errore del server: ${responseInfo.status} - ${responseInfo.text}`;
                    }
                    console.error("PDF processing error:", errorMessage);
                }
            })
            .catch(error => {
                console.error("Network or client-side error during PDF upload:", error);
                displayFeedbackMessage(pdfUploadFeedback, `Errore di rete o del client durante l'elaborazione del PDF: ${error.message || 'Verifica la connessione e riprova.'}`, 'error');
            });
        });
    }

    // --- Invoice Form Submission Handling ---
    if (invoiceForm) {
        invoiceForm.addEventListener("submit", function (event) {
            event.preventDefault();
            successMessageContainer.classList.add('d-none'); // Hide previous success message
            pdfUploadFeedback.innerHTML = ''; // Clear PDF feedback

            let form = this;
            let formData = new FormData(form);

            fetch(form.action, {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
                    "X-Requested-With": "XMLHttpRequest",
                },
            })
            .then(response => {
                return response.text().then(text => ({
                    ok: response.ok,
                    status: response.status,
                    text: text
                }));
            })
            .then(responseInfo => {
                let data;
                try {
                    data = JSON.parse(responseInfo.text);
                } catch (e) {
                    console.error("Failed to parse JSON response:", responseInfo.text, e);
                    // Treat non-JSON response as a general error
                    data = { success: false, messages: [{ type: 'error', text: 'Risposta non valida dal server: ' + responseInfo.text }] };
                }

                resetAllForms();
                 if (responseInfo.ok && data.success) {
                    if (successMessageContainer) {
                        // Rimuovi la classe 'd-none' per mostrare il div
                        successMessageContainer.classList.remove("d-none");
                        // Opzionale: scrolla al messaggio per assicurarti che l'utente lo veda
                        successMessageContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                    
                    
                    // Assicurati che il form venga resettato SOLO DOPO aver mostrato il messaggio
                    // o gestisci il redirect se lo vuoi automatico
                    
                    // Questo nasconde il form di upload PDF e pulisce i campi.

                    // Se il server ha inviato un redirect_url (come suggerito in un commento precedente),
                    // e vuoi reindirizzare subito, fallo qui:
                    // if (data.redirect_url) {
                    //     // Potresti voler mostrare il messaggio per un paio di secondi prima di reindirizzare
                    //     setTimeout(() => {
                    //         window.location.href = data.redirect_url;
                    //     }, 2000); // Reindirizza dopo 2 secondi
                    // } else {
                    //     // Se non c'è un redirect_url, significa che il messaggio deve rimanere visibile
                    //     // e l'utente clicca sul link "Torna alla home Page".
                    // }
                } else {
                    // Handle validation errors or server-side issues
                    let errorMessagesHtml = '';
                    if (data.errors) {
                        // Display form-specific validation errors near the fields if possible,
                        // or consolidate them into a single message.
                        for (const field in data.errors) {
                            errorMessagesHtml += `<strong>${field}:</strong> ${data.errors[field].join(', ')}<br>`;
                        }
                        displayFeedbackMessage(pdfUploadFeedback, `Si prega di correggere i seguenti errori:<br>${errorMessagesHtml}`, 'error');
                    } else if (data.message) { // General error message from Django
                        displayFeedbackMessage(pdfUploadFeedback, data.message, 'error');
                    } else if (data.error) { // Fallback for old error format
                         displayFeedbackMessage(pdfUploadFeedback, data.error, 'error');
                    }
                    else {
                        displayFeedbackMessage(pdfUploadFeedback, `Errore del server: ${responseInfo.status} - ${responseInfo.text}`, 'error');
                    }
                    console.error("Invoice form submission error:", data);
                }
            })
            .catch(error => {
                console.error("Network or client-side error during invoice form submission:", error);
                displayFeedbackMessage(pdfUploadFeedback, `Errore di rete o del client durante l'invio del form: ${error.message || 'Verifica la connessione e riprova.'}`, 'error');
            });
        });
    }
});

// Define uploadPdfUrl in your HTML template BEFORE including this JS file:
// <script>
//     const uploadPdfUrl = "{% url 'upload_pdf_ajax_process' %}";
// </script>
// <script src="{% static 'invoice/js/add_invoice.js' %}"></script>