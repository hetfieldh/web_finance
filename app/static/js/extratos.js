// app/static/js/extratos.js

console.log("extratos.js carregado com sucesso!");

document.addEventListener("DOMContentLoaded", function () {
  const selectMesExtrato = document.getElementById("mes_ano_extratos");
  if (selectMesExtrato) {
    $(selectMesExtrato)
      .datepicker({
        format: "mm-yyyy",
        startView: "months",
        minViewMode: "months",
        language: "pt-BR",
        autoclose: true,
        orientation: "bottom auto",
      })
      .on("changeDate", function (e) {
        document.getElementById("form-extrato-bancario").submit();
      });
  }

  const selectConta = document.getElementById("conta_id");
  if (selectConta) {
    selectConta.addEventListener("change", function () {
      document.getElementById("form-extrato-bancario").submit();
    });
  }
});
