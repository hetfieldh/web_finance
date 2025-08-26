// app/static/js/recebimentos.js

console.log("recebimentos.js carregado com sucesso\!");

document.addEventListener("DOMContentLoaded", function () {
  const selectMesRecebimentos = document.getElementById(
    "mes\_ano\_recebimentos"
  );
  if (selectMesRecebimentos) {
    $(selectMesRecebimentos)
      .datepicker({
        format: "mm-yyyy",
        startView: "months",
        minViewMode: "months",
        language: "pt-BR",
        autoclose: true,
        orientation: "bottom auto",
      })
      .on("changeDate", function (e) {
        document.getElementById("form-recebimentos-mes").submit();
      });
  }
});
