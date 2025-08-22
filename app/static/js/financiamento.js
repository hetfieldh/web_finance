// app/static/js/financiamento.js

console.log("financiamento.js carregado com sucesso!");

document.addEventListener("DOMContentLoaded", () => {
  const formImportar = document.getElementById("form-importar-csv");

  if (formImportar) {
    formImportar.addEventListener("submit", function () {
      const submitButton = formImportar.querySelector('button[type="submit"]');
      const buttonSpinner = submitButton.querySelector(".spinner-border");
      const buttonText = submitButton.querySelector(".button-text");
      const fileInput = document.getElementById("csv_file");
      if (fileInput && fileInput.files.length > 0) {
        submitButton.disabled = true;
        if (buttonText) buttonText.classList.add("d-none");
        if (buttonSpinner) buttonSpinner.classList.remove("d-none");
      }
    });
  }
});
