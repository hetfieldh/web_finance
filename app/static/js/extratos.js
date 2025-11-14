// app/static/js/extratos.js

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

  const formResumoFolha = document.getElementById("form-resumo-folha");
  if (formResumoFolha) {
    const selectAnoFolha = document.getElementById("ano_resumo_folha");
    if (selectAnoFolha) {
      selectAnoFolha.addEventListener("change", function () {
        formResumoFolha.submit();
      });
    }
  }

const btnSaldoDevedor = document.getElementById("btn-saldo-devedor");
  const btnTotal = document.getElementById("btn-total");
  const tabelaSaldoDevedor = document.getElementById("tabela-saldo-devedor");
  const tabelaTotal = document.getElementById("tabela-total");
  const tituloDinamico = document.getElementById("titulo-tabela-dinamica");

  function mostrarTabela(tipo) {
    if (!tabelaSaldoDevedor || !tabelaTotal || !btnSaldoDevedor || !btnTotal) {
      return;
    }

    if (tipo === "saldo-devedor") {
      tabelaSaldoDevedor.style.display = "block";
      tabelaTotal.style.display = "none";
      btnSaldoDevedor.classList.add("active");
      btnTotal.classList.remove("active");
      if (tituloDinamico) {
        tituloDinamico.textContent = " - Saldo Devedor";
      }
    } else {
      tabelaSaldoDevedor.style.display = "none";
      tabelaTotal.style.display = "block";
      btnSaldoDevedor.classList.remove("active");
      btnTotal.classList.add("active");
      if (tituloDinamico) {
        tituloDinamico.textContent = " - Todas as parcelas";
      }
    }
  }

  if (btnSaldoDevedor && btnTotal) {
    btnSaldoDevedor.addEventListener("click", () =>
      mostrarTabela("saldo-devedor")
    );
    btnTotal.addEventListener("click", () => mostrarTabela("total"));

    mostrarTabela("saldo-devedor");
  }
});
