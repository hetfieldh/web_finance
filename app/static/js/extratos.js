// app/static/js/extratos.js (VERSÃO COMPLETA E FINAL)

console.log("extratos.js carregado com sucesso!");

document.addEventListener("DOMContentLoaded", function () {
  const formExtratoBancario = document.getElementById("form-extrato-bancario");

  if (formExtratoBancario) {
    const selectMesExtrato = document.getElementById("mes_ano_extratos");
    const selectConta = document.getElementById("conta_id");

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
          formExtratoBancario.submit();
        });
    }

    if (selectConta) {
      selectConta.addEventListener("change", function () {
        formExtratoBancario.submit();
      });
    }
  }

  const formExtratoConsolidado = document.getElementById(
    "form-extrato-consolidado"
  );
  if (formExtratoConsolidado) {
    const selectMesConsolidado = document.getElementById("mes_ano_consolidado");

    if (selectMesConsolidado) {
      $(selectMesConsolidado)
        .datepicker({
          format: "mm-yyyy",
          startView: "months",
          minViewMode: "months",
          language: "pt-BR",
          autoclose: true,
          orientation: "bottom auto",
        })
        .on("changeDate", function (e) {
          formExtratoConsolidado.submit();
        });
    }
  }
});
