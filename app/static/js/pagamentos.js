// app/static/js/pagamentos.js

document.addEventListener("DOMContentLoaded", function () {
  const selectMesPagamentos = document.getElementById("mes_ano_pagamentos");
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

  const pagamentoModal = document.getElementById("pagamentoModal");
  const jsonDataElement = document.getElementById("json-data-pagamentos");

  const todasAsContas = jsonDataElement
    ? JSON.parse(jsonDataElement.textContent)
    : [];

  if (pagamentoModal && todasAsContas.length > 0) {
    const tiposDeContaPermitidosParaPagamento = [
      "Corrente",
      "Poupança",
      "Digital",
      "Investimento",
      "Caixinha",
      "Dinheiro",
    ];

    function formatCurrency(value) {
      const number = parseFloat(value);
      if (isNaN(number)) {
        return "R$ 0,00";
      }
      return new Intl.NumberFormat("pt-BR", {
        style: "currency",
        currency: "BRL",
      }).format(number);
    }

    pagamentoModal.addEventListener("show.bs.modal", function (event) {
      const button = event.relatedTarget;
      const modalForm = pagamentoModal.querySelector("form");
      const contaSelectInput = modalForm.querySelector(
        'select[name="conta_id"]'
      );

      if (contaSelectInput) {
        contaSelectInput.innerHTML = '<option value="">Selecione...</option>';

        const contasFiltradas = todasAsContas.filter((conta) =>
          tiposDeContaPermitidosParaPagamento.includes(conta.tipo)
        );

        contasFiltradas.forEach((conta) => {
          const saldoDisponivel = conta.saldo_atual;
          const saldoLimite = conta.limite;
          const optionText = `${conta.nome} (${conta.tipo}) - Saldo: ${formatCurrency(saldoDisponivel)} | Limite: ${formatCurrency(saldoLimite)} `;
          const option = new Option(optionText, conta.id);
          contaSelectInput.add(option);
        });
      }

      const itemId = button.getAttribute("data-item-id");
      const itemTipo = button.getAttribute("data-item-tipo");
      const itemValor = button.getAttribute("data-item-valor");
      const itemDescricao = button.getAttribute("data-item-descricao");

      modalForm.querySelector('input[name="item_id"]').value = itemId;
      modalForm.querySelector('input[name="item_tipo"]').value = itemTipo;
      modalForm.querySelector('input[name="item_descricao"]').value =
        itemDescricao;
      const valorPagoInput = modalForm.querySelector(
        'input[name="valor_pago"]'
      );
      const valorPagoHelp = document.getElementById("valor-pago-help");

      valorPagoInput.value = itemValor;

      if (itemTipo === "Financiamento") {
        valorPagoInput.readOnly = false;
        valorPagoInput.style.backgroundColor = "";
        valorPagoInput.style.fontWeight = "normal";
        valorPagoInput.style.color = "";
        if (valorPagoHelp) valorPagoHelp.style.display = "none";
      } else {
        valorPagoInput.readOnly = true;
        valorPagoInput.style.fontWeight = "bold";
        valorPagoInput.style.backgroundColor = "var(--wf-box-negativo)";
        valorPagoInput.style.color = "var(--wf-texto-negativo)";
        if (valorPagoHelp) valorPagoHelp.style.display = "block";
      }
    });
  }
});
