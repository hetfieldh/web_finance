// app/static/js/financiamento.js

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

  const formAmortizacao = document.getElementById("form-amortizacao");
  if (formAmortizacao) {
    const valorAmortizacaoInput = document.getElementById("valor_amortizacao");
    const estrategiaSelect = document.getElementById("estrategia_selecao");
    const saldoDevedorAtual = parseFloat(
      formAmortizacao.dataset.saldoDevedorAtual
    );

    const resumoValor = document.getElementById("resumo-valor");
    const resumoSaldoDepois = document.getElementById("resumo-saldo-depois");
    const resumoPrazoDiv = document.getElementById("resumo-prazo");
    const resumoParcelaDiv = document.getElementById("resumo-parcela");
    const resumoEconomiaJuros = document.getElementById(
      "resumo-economia-juros"
    );
    const resumoParcelasQuitadasLista = document.getElementById(
      "resumo-parcelas-quitadas-lista"
    );
    const resumoAmortizacaoParcialDetalhe = document.getElementById(
      "resumo-amortizacao-parcial-detalhe"
    );
    const resumoParcelasAfetadas = document.getElementById(
      "resumo-parcelas-afetadas"
    );
    const resumoReducaoParcela = document.getElementById(
      "resumo-reducao-parcela"
    );

    const formatCurrency = (value) => {
      return value.toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL",
      });
    };

    const atualizarResumo = () => {
      let valorAmortizar = parseFloat(valorAmortizacaoInput.value) || 0;
      const estrategia = estrategiaSelect.value;

      if (valorAmortizar > saldoDevedorAtual) {
        valorAmortizar = saldoDevedorAtual;
        valorAmortizacaoInput.value = valorAmortizar.toFixed(2);
      }

      resumoValor.textContent = formatCurrency(valorAmortizar);
      resumoSaldoDepois.textContent = formatCurrency(
        saldoDevedorAtual - valorAmortizar
      );

      if (estrategia === "prazo") {
        resumoPrazoDiv.style.display = "block";
        resumoParcelaDiv.style.display = "none";

        let valorRestante = valorAmortizar;
        let jurosEconomizados = 0;
        let numerosParcelasQuitadas = [];
        let detalheParcelaParcial = "Nenhuma";

        if (typeof parcelasPrazo !== "undefined" && parcelasPrazo.length > 0) {
          for (const parcela of parcelasPrazo) {
            if (valorRestante <= 0) break;

            const valorPrincipal = parseFloat(parcela.valor_principal);
            const valorPagoAnteriormente = parseFloat(parcela.valor_pago);
            const valorNecessario = valorPrincipal - valorPagoAnteriormente;

            if (valorRestante >= valorNecessario) {
              valorRestante -= valorNecessario;
              jurosEconomizados += parseFloat(parcela.valor_juros);
              numerosParcelasQuitadas.push(parcela.numero_parcela);
            } else {
              const novoValorPago = valorPagoAnteriormente + valorRestante;
              detalheParcelaParcial = `Parcela ${parcela.numero_parcela} (Total pago será ${formatCurrency(novoValorPago)})`;
              valorRestante = 0;
            }
          }
        }

        resumoEconomiaJuros.textContent = formatCurrency(jurosEconomizados);
        resumoParcelasQuitadasLista.textContent =
          numerosParcelasQuitadas.length > 0
            ? `${numerosParcelasQuitadas.length} (${numerosParcelasQuitadas.reverse().join(", ")})`
            : "Nenhuma";
        resumoAmortizacaoParcialDetalhe.textContent = detalheParcelaParcial;
      } else if (estrategia === "parcela") {
        resumoPrazoDiv.style.display = "none";
        resumoParcelaDiv.style.display = "block";

        const qtdParcelas =
          typeof parcelasParcela !== "undefined" ? parcelasParcela.length : 0;
        const reducaoPorParcela =
          qtdParcelas > 0 ? valorAmortizar / qtdParcelas : 0;

        resumoParcelasAfetadas.textContent = qtdParcelas;
        resumoReducaoParcela.textContent = formatCurrency(reducaoPorParcela);
      }
    };

    if (valorAmortizacaoInput) {
      valorAmortizacaoInput.addEventListener("input", atualizarResumo);
    }
    if (estrategiaSelect) {
      estrategiaSelect.addEventListener("change", atualizarResumo);
    }

    atualizarResumo();
  }
});
