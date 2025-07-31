// app/static/js/script.js

// Exibe uma mensagem no console para confirmar que o script foi carregado
console.log("script.js carregado com sucesso!");

// Adiciona um listener para quando o DOM estiver completamente carregado
document.addEventListener("DOMContentLoaded", () => {
  // --- Script para toggler da sidebar ---
  const sidebarToggle = document.getElementById("sidebarToggle");
  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", () => {
      document.getElementById("wrapper").classList.toggle("toggled");
    });
  }

  // --- Scripts para conta_movimentos/add.html (visibilidade de campos de transferência) ---
  const contaTransacaoSelect = document.getElementById("conta_transacao_id");
  const isTransferenciaCheckboxContainer = document.getElementById(
    "is_transferencia_field_container"
  );
  const isTransferenciaCheckbox = document.getElementById("is_transferencia");
  const contaDestinoField = document.getElementById("conta_destino_field");
  const contaOrigemSelect = document.getElementById("conta_id"); // Para a lógica de desabilitar conta de origem
  const contaDestinoSelect = document.getElementById("conta_destino_id"); // Para a lógica de desabilitar conta de origem

  // Verifica se os elementos específicos de conta_movimentos/add.html existem
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
    updateTransferenciaFieldsVisibility(); // Define o estado inicial
  }

  // --- Scripts para conta_movimentos/add.html (desabilitar conta de origem na destino) ---
  // Verifica se os elementos específicos de conta_movimentos/add.html existem para esta lógica
  if (contaOrigemSelect && contaDestinoSelect) {
    function atualizarContaDestino() {
      const selectedOrigemId = contaOrigemSelect.value;

      for (const option of contaDestinoSelect.options) {
        if (option.value === selectedOrigemId && option.value !== "") {
          option.style.display = "none";
          // Se a conta de destino selecionada for a mesma que a de origem, reseta
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

  // --- Scripts para inicializar tooltips do Bootstrap (usado em várias telas) ---
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // --- Exibe a data atual ---
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
});
