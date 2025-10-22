// app/static/js/extratos.js

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

  // RESUMO MENSAL
  const formResumoMensal = document.getElementById("form-resumo-mensal");
  if (formResumoMensal) {
    const selectMesResumo = document.getElementById("mes_ano_resumo");

    if (selectMesResumo) {
      $(selectMesResumo)
        .datepicker({
          format: "mm-yyyy",
          startView: "months",
          minViewMode: "months",
          language: "pt-BR",
          autoclose: true,
          orientation: "bottom auto",
        })
        .on("changeDate", function (e) {
          formResumoMensal.submit();
        });
    }
  }

  // RESUMO DA FOLHA
  const formResumoFolha = document.getElementById("form-resumo-folha");
  if (formResumoFolha) {
    const selectAnoFolha = document.getElementById("ano_resumo_folha");
    if (selectAnoFolha) {
      selectAnoFolha.addEventListener("change", function () {
        formResumoFolha.submit();
      });
    }
  }
});
