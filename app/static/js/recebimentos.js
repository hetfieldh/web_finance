// app/static/js/recebimentos.js

function formatCurrencyJS(value) {
  const number = parseFloat(value);
  if (isNaN(number)) {
    return " 0,00";
  }
  return new Intl.NumberFormat("pt-BR").format(number);
}

document.addEventListener("DOMContentLoaded", function () {
  const fgtsInfoElement = document.getElementById("fgts-info-data");

  if (fgtsInfoElement) {
    const salarioRows = document.querySelectorAll(
      "tr[data-categoria='Salário']"
    );

    salarioRows.forEach((salarioRow) => {
      const itemTipo = salarioRow.getAttribute("data-item-tipo");
      const folhaTemFgts =
        salarioRow.getAttribute("data-folha-tem-fgts") === "true";

      if (itemTipo === "Mensal" && !folhaTemFgts) {
        const actionsCell = salarioRow.querySelector("td:last-child");

        if (actionsCell) {
          let title = "Recebimento bloqueado.";
          title +=
            " Motivo: A folha de pagamento (Mensal) não possui um item de FGTS com valor.";

          const lockIcon = actionsCell.querySelector(".fa-lock");

          if (!lockIcon) {
            actionsCell.innerHTML = `<i class="fas fa-lock text-danger" data-bs-toggle="tooltip" title="${title}"></i>`;
          } else {
            lockIcon.setAttribute("data-bs-toggle", "tooltip");
            lockIcon.setAttribute("title", title);
          }
        }
      }
    });
  }

  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

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
    return;
  }

  const todasAsContas = JSON.parse(contasDataElement.textContent);

  const contasPadrao = [
    "Corrente",
    "Poupança",
    "Digital",
    "Investimento",
    "Caixinha",
    "Dinheiro",
  ];

  const regrasDeFiltro = {
    Mensal: contasPadrao,
    "13° Salário": contasPadrao,
    Férias: contasPadrao,
    PLR: contasPadrao,
    Rescisão: contasPadrao,
    Receita: contasPadrao,
    Benefício: ["Benefício"],
    FGTS: ["FGTS"],
  };

  recebimentoModal.addEventListener("show.bs.modal", function (event) {
    const button = event.relatedTarget;
    const modalForm = recebimentoModal.querySelector("form");

    const dataInput = this.querySelector("#data_recebimento");
    if (!dataInput.value) {
      const hoje = new Date();
      const ano = hoje.getFullYear();
      const mes = String(hoje.getMonth() + 1).padStart(2, "0");
      const dia = String(hoje.getDate()).padStart(2, "0");
      dataInput.value = `${ano}-${mes}-${dia}`;
    }

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

    modalForm.querySelector('input[name="item_id"]').value = itemId;
    modalForm.querySelector('input[name="item_tipo"]').value = itemTipo;
    modalForm.querySelector('input[name="valor_recebido"]').value = itemValor;
    modalForm.querySelector('input[name="item_descricao"]').value =
      itemDescricao;
  });
});
