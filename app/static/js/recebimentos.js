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
  // --- ALTERAÇÃO INICIADA ---
  const fgtsInfoElement = document.getElementById("fgts-info-data");
  if (fgtsInfoElement) {
    const fgtsInfo = JSON.parse(fgtsInfoElement.textContent);
    const hasFgtsAccount = fgtsInfo.has_account;

    const salarioRow = document.querySelector(
      "tr[data-item-tipo='Salário Líquido']"
    );

    if (salarioRow) {
      const folhaTemFgts =
        salarioRow.getAttribute("data-folha-tem-fgts") === "true";

      // A baixa é bloqueada se a conta FGTS não existir OU se a folha não tiver o item de FGTS
      if (!hasFgtsAccount || !folhaTemFgts) {
        const actionsCell = salarioRow.querySelector("td:last-child");
        if (actionsCell) {
          // Cria uma mensagem de erro específica para o tooltip
          let title = "Recebimento bloqueado.";
          if (!hasFgtsAccount) {
            title +=
              " Motivo: Nenhuma conta bancária do tipo FGTS foi cadastrada.";
          } else if (!folhaTemFgts) {
            title +=
              " Motivo: A folha de pagamento não possui um item de FGTS com valor.";
          }

          actionsCell.innerHTML = `<i class="fas fa-lock text-danger" data-bs-toggle="tooltip" title="${title}"></i>`;
        }
      }
    }
  }

  // Inicializa os tooltips para que a nova mensagem apareça
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
  // --- ALTERAÇÃO FINALIZADA ---
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
    "Salário Líquido": [
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
