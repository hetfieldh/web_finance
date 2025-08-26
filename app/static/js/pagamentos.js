// app/static/js/pagamentos.js

console.log("pagamentos.js carregado com sucesso\!");

document.addEventListener("DOMContentLoaded", function () {
  const selectMesPagamentos = document.getElementById("mes\_ano\_pagamentos");
  if (selectMesPagamentos) {
    $(selectMesPagamentos)
      .datepicker({
        format: "mm-yyyy",
        startView: "months",
        minViewMode: "months",
        language: "pt-BR",
        autoclose: true,
        orientation: "bottom auto",
      })
      .on("changeDate", function (e) {
        document.getElementById("form-pagamentos-mes").submit();
      });
  }
});
