// app/static/js/recebimentos.js

function formatCurrencyJS(value) {
  const number = parseFloat(value);
  if (isNaN(number)) {
    return "R$ 0,00";
  }
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(number);
}

document.addEventListener("DOMContentLoaded", function () {
  $("#mes_ano_recebimentos").datepicker({
    format: "mm-yyyy",
    startView: "months",
    minViewMode: "months",
    language: "pt-BR",
    autoclose: true,
  });

  $("#mes_ano_recebimentos").on("changeDate", function () {
    const form = document.getElementById("form-recebimentos-mes");
    if (form) {
      const spinner = document.createElement("div");
      spinner.className = "spinner-border spinner-border-sm ms-2";
      spinner.setAttribute("role", "status");
      spinner.innerHTML = `<span class="visually-hidden">Loading...</span>`;
      form.appendChild(spinner);
      form.submit();
    }
  });

  const recebimentoModal = document.getElementById("recebimentoModal");
  const contasDataElement = document.getElementById("contas-data");

  if (!recebimentoModal || !contasDataElement) {
    console.error(
      "Elementos essenciais (modal ou script de dados das contas) não encontrados."
    );
    return;
  }

  const todasAsContas = JSON.parse(contasDataElement.textContent);

  const regrasDeFiltro = {
    Salário: [
      "Corrente",
      "Poupança",
      "Digital",
      "Investimento",
      "Caixinha",
      "Dinheiro",
    ],
    Receita: [
      "Corrente",
      "Poupança",
      "Digital",
      "Investimento",
      "Caixinha",
      "Dinheiro",
    ],
    Benefício: ["Benefício"],
    FGTS: ["FGTS"],
  };

  recebimentoModal.addEventListener("show.bs.modal", function (event) {
    const button = event.relatedTarget;
    const modalForm = recebimentoModal.querySelector("form");

    const itemTipo = button.getAttribute("data-item-tipo");
    const contaSugeridaId = button.getAttribute("data-conta-sugerida-id");
    const contaSelectInput = modalForm.querySelector('select[name="conta_id"]');

    if (contaSelectInput) {
      contaSelectInput.innerHTML = '<option value="">Selecione...</option>';
      const tiposPermitidos = regrasDeFiltro[itemTipo] || [];
      const contasFiltradas = todasAsContas.filter((conta) =>
        tiposPermitidos.includes(conta.tipo)
      );

      contasFiltradas.forEach((conta) => {
        const saldoFormatado = formatCurrencyJS(conta.saldo_atual);
        const optionText = `${conta.nome} (${conta.tipo}) | Saldo: ${saldoFormatado}`;
        const option = new Option(optionText, conta.id);
        contaSelectInput.add(option);
      });

      if (contaSugeridaId) {
        contaSelectInput.value = contaSugeridaId;
      }
    }

    const itemId = button.getAttribute("data-item-id");
    const itemValor = button.getAttribute("data-item-valor");
    const itemDescricao = button.getAttribute("data-item-descricao");
    const itemIdInput = modalForm.querySelector('input[name="item_id"]');
    const itemTipoInput = modalForm.querySelector('input[name="item_tipo"]');
    const valorRecebidoInput = modalForm.querySelector(
      'input[name="valor_recebido"]'
    );
    const itemDescricaoInput = modalForm.querySelector(
      'input[name="item_descricao"]'
    );
    if (itemIdInput) itemIdInput.value = itemId;
    if (itemTipoInput) itemTipoInput.value = itemTipo;
    if (valorRecebidoInput) valorRecebidoInput.value = itemValor;
    if (itemDescricaoInput) itemDescricaoInput.value = itemDescricao;
  });
});
