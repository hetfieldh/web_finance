// app/static/js/global.js

// Exibe uma mensagem no console para confirmar que o script foi carregado
console.log("global.js carregado com sucesso!");

document.addEventListener("DOMContentLoaded", () => {
  // --- Script para toggler da sidebar ---
  const sidebarToggle = document.getElementById("sidebarToggle");
  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", () => {
      document.getElementById("wrapper").classList.toggle("toggled");
    });
  }

  // --- Script para inicializar tooltips do Bootstrap ---
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // --- Lógica para o Botão "Voltar ao Topo" ---
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
});

/**
 * Inicializa o bootstrap-datepicker em um elemento para seleção de Mês/Ano.
 * @param {string} selector - O seletor jQuery para o campo de input (ex: '#meu-campo').
 * @param {function} onChangeCallback - Uma função a ser executada quando a data é alterada.
 */
function inicializarDatepickerMesAno(selector, onChangeCallback) {
  const elemento = $(selector);
  if (elemento.length) {
    elemento
      .datepicker({
        format: "mm-yyyy",
        startView: "months",
        minViewMode: "months",
        language: "pt-BR",
        autoclose: true,
        orientation: "bottom right",
      })
      .on("changeDate", function (e) {
        if (typeof onChangeCallback === "function") {
          onChangeCallback(e);
        }
      });
  }
}
