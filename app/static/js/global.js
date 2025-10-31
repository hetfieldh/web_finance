// app/static/js/global.js

document.addEventListener("DOMContentLoaded", () => {
  const sidebarToggle = document.getElementById("sidebarToggle");
  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", () => {
      document.getElementById("wrapper").classList.toggle("toggled");
    });
  }

  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

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
 * @param {string} selector
 * @param {function} onChangeCallback -
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
