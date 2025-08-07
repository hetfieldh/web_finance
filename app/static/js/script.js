// app/static/js/script.js

// Exibe mensagem no console
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

  // --- 2. Scripts para formulário de movimentação de conta ---
  const contaTransacaoSelect = document.getElementById("conta_transacao_id");
  const isTransferenciaCheckboxContainer = document.getElementById(
    "is_transferencia_field_container"
  );
  const isTransferenciaCheckbox = document.getElementById("is_transferencia");
  const contaDestinoField = document.getElementById("conta_destino_field");
  const contaOrigemSelect = document.getElementById("conta_id");
  const contaDestinoSelect = document.getElementById("conta_destino_id");

  if (
    contaTransacaoSelect &&
    isTransferenciaCheckboxContainer &&
    isTransferenciaCheckbox &&
    contaDestinoField
  ) {
    const tipoMovimentoMap = {};
    Array.from(contaTransacaoSelect.options).forEach((option) => {
      const match = option.textContent.match(/\((Crédito|Débito)\)/);
      if (match) {
        tipoMovimentoMap[option.value] = match[1];
      }
    });

    function updateTransferenciaFieldsVisibility() {
      const selectedTransacaoId = contaTransacaoSelect.value;
      const tipoMovimento = tipoMovimentoMap[selectedTransacaoId];

      if (tipoMovimento === "Débito") {
        isTransferenciaCheckboxContainer.style.display = "block";
        if (isTransferenciaCheckbox.checked) {
          contaDestinoField.style.display = "block";
        } else {
          contaDestinoField.style.display = "none";
        }
      } else {
        isTransferenciaCheckboxContainer.style.display = "none";
        contaDestinoField.style.display = "none";
        isTransferenciaCheckbox.checked = false;
      }
    }

    contaTransacaoSelect.addEventListener(
      "change",
      updateTransferenciaFieldsVisibility
    );
    isTransferenciaCheckbox.addEventListener(
      "change",
      updateTransferenciaFieldsVisibility
    );
    updateTransferenciaFieldsVisibility();
  }

  if (contaOrigemSelect && contaDestinoSelect) {
    function atualizarContaDestino() {
      const selectedOrigemId = contaOrigemSelect.value;

      for (const option of contaDestinoSelect.options) {
        if (option.value === selectedOrigemId && option.value !== "") {
          option.style.display = "none";
          if (contaDestinoSelect.value === selectedOrigemId) {
            contaDestinoSelect.value = "";
          }
        } else {
          option.style.display = "";
        }
      }
    }

    contaOrigemSelect.addEventListener("change", atualizarContaDestino);
    atualizarContaDestino();
  }

  // --- 3. Script para inicializar tooltips do Bootstrap ---
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // --- 4. Script para exibir a data atual no Dashboard ---
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

  // --- 5. Lógica para o Botão "Voltar ao Topo" ---
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
      scrollContainer.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    });
  }

  // --- 6. Script para formulário dinâmico da Folha de Pagamento ---
  const formLancamento = document.getElementById("form-lancamento-folha");
  if (formLancamento) {
    const itensContainer = document.getElementById("itens-container");
    const addItemBtn = document.getElementById("add-item-btn");
    const itemTemplate = document.getElementById("item-template");

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

    // Adiciona uma nova linha de item
    if (addItemBtn && itemTemplate) {
      addItemBtn.addEventListener("click", () => {
        // Clona o template
        const newRow = itemTemplate.content.cloneNode(true);

        // Pega o índice para a nova linha
        const currentIndex =
          itensContainer.querySelectorAll(".item-row").length;

        // Atualiza os atributos 'name' e 'id' dos campos no novo clone
        const fields = newRow.querySelectorAll("select, input");
        fields.forEach((field) => {
          for (const attr of ["name", "id"]) {
            const attrValue = field.getAttribute(attr);
            if (attrValue) {
              field.setAttribute(
                attr,
                attrValue.replace("__prefix__", currentIndex)
              );
            }
          }
        });

        // Adiciona a nova linha ao container
        itensContainer.appendChild(newRow);
      });
    }

    // Delegação de evento para o botão de remover
    itensContainer.addEventListener("click", (event) => {
      const removeBtn = event.target.closest(".remove-item-btn");
      if (removeBtn) {
        const itemRow = removeBtn.closest(".item-row");
        if (itensContainer.querySelectorAll(".item-row").length > 1) {
          itemRow.remove();
          reindexRows(); // Re-indexa as linhas restantes
        } else {
          alert("É necessário pelo menos uma verba na folha de pagamento.");
        }
      }
    });
  }
});
