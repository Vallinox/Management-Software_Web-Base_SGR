document.addEventListener("DOMContentLoaded", function () {
  document
    .getElementById("invoice-form")
    .addEventListener("submit", function (event) {
      event.preventDefault(); // Evita il reload della pagina

      let form = this;
      let formData = new FormData(form);

      form.style.display = "none";
      document.getElementById("card-edit").style.visibility = "hidden";

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
            document
              .getElementById("success-message")
              .classList.remove("d-none");
            form.reset(); // Pulisce il form dopo l'invio
            let errorElements = document.querySelectorAll(".error-message");
            errorElements.forEach((el) => el.remove());
          } else {
            alert("Errore nell'invio: " + JSON.stringify(data.errors));
          }
        })
        .catch((error) => console.error("Errore:", error));
    });
});
