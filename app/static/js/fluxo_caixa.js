// app/static/js/fluxo_caixa.js

document.addEventListener("DOMContentLoaded", function () {
  const selectMesFluxoCaixa = document.getElementById("mes_ano_fluxo_caixa");
  if (selectMesFluxoCaixa) {
    $(selectMesFluxoCaixa)
      .datepicker({
        format: "mm-yyyy",
        startView: "months",
        minViewMode: "months",
        language: "pt-BR",
        autoclose: true,
        orientation: "bottom auto"
      })
      .on("changeDate", function (e) {
        document.getElementById("form-fluxo-caixa").submit();
      });
  }
});
