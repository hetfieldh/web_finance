// app/static/js/script.js

// Exibe uma mensagem no console para confirmar que o script foi carregado
console.log("script.js carregado com sucesso!");

// Adiciona um listener para quando o DOM estiver completamente carregado
document.addEventListener("DOMContentLoaded", () => {
  // --- 1. Script para toggler da sidebar ---
  const sidebarToggle = document.getElementById("sidebarToggle");
  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", () => {
      document.getElementById("wrapper").classList.toggle("toggled");
    });
  }

  // --- 2. Script para inicializar tooltips do Bootstrap ---
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // --- 3. Script para exibir a data atual no Dashboard ---
  const dataAtual = new Date();
  const opcoes = {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  };
  const formatoElegante = new Intl.DateTimeFormat("pt-BR", opcoes).format(
    dataAtual
  );
  const elementoDataAtual = document.getElementById("data-atual");
  if (elementoDataAtual) {
    const frase =
      formatoElegante.charAt(0).toUpperCase() + formatoElegante.slice(1);
    elementoDataAtual.innerText = frase;
  }

  // --- 4. Lógica para o Botão "Voltar ao Topo" ---
  const backToTopButton = document.getElementById("back-to-top-btn");
  const scrollContainer = document.getElementById("page-content-wrapper");
  if (backToTopButton && scrollContainer) {
    scrollContainer.addEventListener("scroll", () => {
      if (scrollContainer.scrollTop > 200) {
        backToTopButton.style.display = "block";
      } else {
        backToTopButton.style.display = "none";
      }
    });
    backToTopButton.addEventListener("click", (e) => {
      e.preventDefault();
      scrollContainer.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  // --- 5. Script para formulário dinâmico da Folha de Pagamento ---
  const formLancamento = document.getElementById("form-lancamento-folha");
  if (formLancamento) {
    const itensContainer = document.getElementById("itens-container");
    const addItemBtn = document.getElementById("add-item-btn");
    const itemTemplateHtml =
      document.getElementById("item-template")?.innerHTML;

    const reindexRows = () => {
      const itemRows = itensContainer.querySelectorAll(".item-row");
      itemRows.forEach((row, index) => {
        const fields = row.querySelectorAll("select, input");
        fields.forEach((field) => {
          for (const attr of ["name", "id"]) {
            const attrValue = field.getAttribute(attr);
            if (attrValue) {
              const newAttrValue = attrValue.replace(
                /itens-\d+-/,
                `itens-${index}-`
              );
              field.setAttribute(attr, newAttrValue);
            }
          }
        });
      });
    };

    if (addItemBtn && itemTemplateHtml) {
      addItemBtn.addEventListener("click", () => {
        const currentIndex =
          itensContainer.querySelectorAll(".item-row").length;
        const newRowHtml = itemTemplateHtml.replace(
          /__prefix__/g,
          currentIndex
        );
        const tempDiv = document.createElement("div");
        tempDiv.innerHTML = newRowHtml;
        itensContainer.appendChild(tempDiv.firstElementChild);
      });
    }

    itensContainer.addEventListener("click", (event) => {
      const removeBtn = event.target.closest(".remove-item-btn");
      if (removeBtn) {
        const itemRow = removeBtn.closest(".item-row");
        if (itensContainer.querySelectorAll(".item-row").length > 1) {
          itemRow.remove();
          reindexRows();
        } else {
          alert("É necessário pelo menos uma verba na folha de pagamento.");
        }
      }
    });
  }

  // --- 6. Script para Modal de Pagamento ---
  const pagamentoModal = document.getElementById("pagamentoModal");
  if (pagamentoModal) {
    pagamentoModal.addEventListener("show.bs.modal", function (event) {
      const button = event.relatedTarget;
      const itemId = button.getAttribute("data-item-id");
      const itemTipo = button.getAttribute("data-item-tipo");
      const itemValor = button.getAttribute("data-item-valor");
      const itemDescricao = button.getAttribute("data-item-descricao");
      const modal = this;
      modal.querySelector("#item_id").value = itemId;
      modal.querySelector("#item_tipo").value = itemTipo;
      modal.querySelector("#valor_pago").value = itemValor;
      modal.querySelector("#item_descricao").value = itemDescricao;
    });
  }

  // --- 7. Script para Modal de Recebimento ---
  const recebimentoModal = document.getElementById("recebimentoModal");
  if (recebimentoModal) {
    recebimentoModal.addEventListener("show.bs.modal", function (event) {
      const button = event.relatedTarget;
      const itemId = button.getAttribute("data-item-id");
      const itemTipo = button.getAttribute("data-item-tipo");
      const itemValor = button.getAttribute("data-item-valor");
      const itemDescricao = button.getAttribute("data-item-descricao");
      const itemData = button.getAttribute("data-item-data");
      const modal = this;
      modal.querySelector("#item_id").value = itemId;
      modal.querySelector("#item_tipo").value = itemTipo;
      modal.querySelector("#valor_recebido").value = itemValor;
      modal.querySelector("#item_descricao").value = itemDescricao;
      modal.querySelector("#data_recebimento").value = itemData;
    });
  }

  // --- 8. Script para seleção do tipo de movimentação bancária ---
  const tipoOperacaoRadios = document.querySelectorAll(
    'input[name="tipo_operacao"]'
  );
  const simplesFields = document.getElementById("movimentacao_simples_fields");
  const transferenciaFields = document.getElementById("transferencia_fields");
  const descricaoFieldContainer = document.getElementById(
    "descricao_field_container"
  );

  const contaIdField = document.querySelector(
    'label[for="conta_id"]'
  ).nextElementSibling;
  const dataMovimentoField = document.querySelector(
    'label[for="data_movimento"]'
  ).nextElementSibling;
  const valorField =
    document.querySelector('label[for="valor"]').nextElementSibling;

  function toggleMovimentoFields() {
    const selectedValue = document.querySelector(
      'input[name="tipo_operacao"]:checked'
    ).value;

    if (selectedValue === "simples") {
      if (simplesFields) simplesFields.style.display = "block";
      if (transferenciaFields) transferenciaFields.style.display = "none";
      if (descricaoFieldContainer)
        descricaoFieldContainer.style.display = "block";

      simplesFields
        .querySelector(".row:nth-of-type(1) .col-md-6:nth-of-type(1)")
        .appendChild(contaIdField);
      simplesFields
        .querySelector(".row:nth-of-type(2) .col-md-6:nth-of-type(1)")
        .appendChild(dataMovimentoField);
      simplesFields
        .querySelector(".row:nth-of-type(2) .col-md-6:nth-of-type(2)")
        .appendChild(valorField);
    } else {
      if (simplesFields) simplesFields.style.display = "none";
      if (transferenciaFields) transferenciaFields.style.display = "block";
      if (descricaoFieldContainer)
        descricaoFieldContainer.style.display = "none";

      transferenciaFields
        .querySelector(".row:nth-of-type(1) .col-md-6:nth-of-type(1)")
        .appendChild(contaIdField);
      transferenciaFields
        .querySelector(".row:nth-of-type(2) .col-md-4:nth-of-type(2)")
        .appendChild(dataMovimentoField);
      transferenciaFields
        .querySelector(".row:nth-of-type(2) .col-md-4:nth-of-type(3)")
        .appendChild(valorField);
    }
  }

  if (tipoOperacaoRadios.length > 0) {
    tipoOperacaoRadios.forEach((radio) => {
      radio.addEventListener("change", toggleMovimentoFields);
    });
    toggleMovimentoFields();
  }

  // --- 9. Lógica para o formulário de transferência ---
  const contaOrigemSelect = document.querySelector("#conta_id");
  const contaDestinoSelect = document.querySelector("#conta_destino_id");

  if (contaOrigemSelect && contaDestinoSelect) {
    const atualizarContaDestino = () => {
      const selectedOrigemId = contaOrigemSelect.value;

      for (const option of contaDestinoSelect.options) {
        if (option.value === selectedOrigemId && option.value !== "") {
          option.style.display = "none";
        } else {
          option.style.display = "block";
        }
      }

      if (contaDestinoSelect.value === selectedOrigemId) {
        contaDestinoSelect.value = "";
      }
    };

    contaOrigemSelect.addEventListener("change", atualizarContaDestino);

    atualizarContaDestino();
  }
});
