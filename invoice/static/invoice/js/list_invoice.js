function formatCurrency(value) {
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "EUR",
  }).format(value);
}

function filterInvoices() {
  const companyName = document.getElementById("company_name").value;
  const invoiceYear = document.getElementById("invoice_year").value;

  fetch(`/invoices/filter/?company_name=${companyName}&year=${invoiceYear}`)
    .then((response) => {
      // Aggiungi questa linea per esaminare la risposta
      return response.json();
    })
    .then((data) => {
      const formattedRevenue = new Intl.NumberFormat("it-IT", {
        style: "currency",
        currency: "EUR",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(data.revenue);

      const formattedRevenueIVA = new Intl.NumberFormat("it-IT", {
        style: "currency",
        currency: "EUR",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(data.revenue_iva);

      const formattedRevenue_tot_IVA = new Intl.NumberFormat("it-IT", {
        style: "currency",
        currency: "EUR",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(data.revenue_tot);

      // Aggiorna la somma del fatturato
      document.getElementById(
        "revenue-amount"
      ).innerHTML = `Totale Fatturato (noli): <strong>${formattedRevenue}</strong>`;
      document.getElementById(
        "revenue-iva"
      ).innerHTML = `Totale IVA: <strong>${formattedRevenueIVA}</strong>`;
      document.getElementById(
        "revenue-tot"
      ).innerHTML = `Totale fattura + IVA: <strong>${formattedRevenue_tot_IVA}</strong>`;

      // Mostra la ragione sociale selezionata
      document.getElementById(
        "selected-company"
      ).innerHTML = `<strong>${companyName}</strong>`;
      document.getElementById(
        "year_company"
      ).innerHTML = ` per l'anno: <strong>${invoiceYear}</strong>`;

      // Aggiorna la tabella delle fatture
      const tableBody = document.querySelector("#invoice-table tbody");
      tableBody.innerHTML = ""; // Pulisce la tabella
      data.invoices.forEach((invoice) => {
        const row = document.createElement("tr");
        row.innerHTML = `
                <td>${invoice.invoice_number}</td>
                <td>${invoice.invoice_date}</td>
                <td><b>${formatCurrency(invoice.freight_cost)}</b></td>`;
        tableBody.appendChild(row);
      });
    })
    .catch((error) => console.error("Errore nel filtro delle fatture:", error));
}
