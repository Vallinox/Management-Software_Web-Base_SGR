function filterVehicle() {
  const companyName = document.getElementById("company_own").value;
  const errorDiv = document.getElementById("error-message");
  const tableBody = document.querySelector("#vehicle-table tbody");

  errorDiv.textContent = "";
  tableBody.innerHTML = "";

  if (!companyName) {
    errorDiv.textContent = "Seleziona un'azienda prima di filtrare i mezzi.";
    return;
  }

  fetch(`/vehicles/filter/?company_own=${encodeURIComponent(companyName)}`)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      const vehicles = data.vehicles || [];

      if (vehicles.length === 0) {
        errorDiv.textContent = "Nessun veicolo trovato per questa azienda.";
        return;
      }

      vehicles.forEach((vehicle) => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td><strong>${vehicle.plate}</strong></td>
            <td>${vehicle.vehicle_category}</td>
            <td><strong>${vehicle.eur_category}</strong></td>
            <td>${vehicle.contract_type}</td>
            <td>${vehicle.insurance_term_expires}</td>
            <td>${vehicle.review_deadline}</td>
            <td>${vehicle.bollo_deadline}</td>
            <td>${vehicle.aci_card_deadline}</td>
            <td>
              <a class="btn btn-warning me-1" href="/edit_vehicle/${vehicle.id}/">
                <i class="fa-regular fa-pen-to-square"></i>
              </a>
              <button type="button" class="btn btn-danger delete-btn" data-id="${vehicle.id}">
                <i class="fa-regular fa-trash-can"></i>
              </button>
            </td>

          `;
        tableBody.appendChild(row);
      });
    })
    .catch((error) => {
      console.error("Errore nel filtro dei mezzi:", error);
      errorDiv.textContent =
        "Errore nel caricamento dei dati. Riprova più tardi.";
    });
}

document.addEventListener("click", function (event) {
  if (event.target.closest(".delete-btn")) {
    const button = event.target.closest(".delete-btn");
    const vehicleId = button.getAttribute("data-id");

    if (confirm("Sei sicuro di voler eliminare questo veicolo?")) {
      fetch(`/vehicles/delete/${vehicleId}/`, {
        method: "DELETE",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"), // Necessario in Django
        },
      })
        .then((response) => {
          if (!response.ok) throw new Error("Errore durante l'eliminazione.");
          return response.json();
        })

        .then((data) => {
          if (data.success) {
            const row = button.closest("tr");
            row.remove();

            const tableBody = document.querySelector("#vehicle-table tbody");
            const errorDiv = document.getElementById("error-message");

            if (tableBody.children.length === 0) {
              errorDiv.textContent =
                "Nessun veicolo trovato per questa azienda.";

              document.getElementById("company_own").value = "";
            }
          } else {
            alert("Errore: " + data.error);
          }
        })
        .catch((err) => {
          console.error("Errore:", err);
          alert("Errore nella comunicazione col server.");
        });
    }
  }
});

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

