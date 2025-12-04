// app\static\js\salario_form.js

document.addEventListener("DOMContentLoaded", function () {
  const mesReferenciaInput = document.getElementById("mes_referencia");

  if (mesReferenciaInput) {
    $(mesReferenciaInput).datepicker({
      format: "mm/yyyy",
      startView: "months",
      minViewMode: "months",
      maxViewMode: "years",
      language: "pt-BR",
      autoclose: true,
      orientation: "bottom auto",
    });
  }

  const tipoFolhaSelect = document.getElementById("tipo_folha");
  const containerData = document.getElementById("container_data_recebimento");
  const inputData = containerData ? containerData.querySelector("input") : null;

  function toggleDataField() {
    if (!tipoFolhaSelect || !containerData) return;

    if (tipoFolhaSelect.value === "Mensal" || tipoFolhaSelect.value === "") {
      containerData.style.display = "none";

      if (inputData) {
        inputData.required = false;
      }
    } else {
      containerData.style.display = "block";

      if (inputData) {
        inputData.required = true;
      }
    }
  }

  if (tipoFolhaSelect) {
    tipoFolhaSelect.addEventListener("change", toggleDataField);
    toggleDataField();
  }

  const tipoItemSelect = document.getElementById("tipo");
  const contaDestinoField = document.getElementById("conta_destino_id");

  if (tipoItemSelect && contaDestinoField) {
    const contaDestinoContainer =
      contaDestinoField.closest(".mb-3") || contaDestinoField.parentElement;

    function toggleContaDestinoField() {
      if (tipoItemSelect.value === "Benefício") {
        contaDestinoContainer.style.display = "block";
      } else {
        contaDestinoContainer.style.display = "none";
        contaDestinoField.value = "";
      }
    }

    toggleContaDestinoField();
    tipoItemSelect.addEventListener("change", toggleContaDestinoField);
  }
});
