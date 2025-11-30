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

  const checkboxes = document.querySelectorAll(".item-checkbox");
  const selectAllDesktop = document.getElementById("select-all-desktop");
  const selectAllMobile = document.getElementById("select-all-mobile");
  const btnExcluir = document.getElementById("btn-excluir-massa");
  const countSpan = document.getElementById("count-selected");

  function updateButtonState() {
    const allChecked = document.querySelectorAll(".item-checkbox:checked");

    const visibleCount = Array.from(allChecked).filter(
      (cb) => cb.offsetParent !== null
    ).length;

    if (countSpan) countSpan.textContent = visibleCount;

    if (btnExcluir) {
      if (visibleCount > 0) {
        btnExcluir.classList.remove("d-none");
      } else {
        btnExcluir.classList.add("d-none");
      }
    }
  }

  function toggleAll(checked) {
    checkboxes.forEach((cb) => (cb.checked = checked));
    if (selectAllDesktop) selectAllDesktop.checked = checked;
    if (selectAllMobile) selectAllMobile.checked = checked;
    updateButtonState();
  }

  if (selectAllDesktop)
    selectAllDesktop.addEventListener("change", (e) =>
      toggleAll(e.target.checked)
    );
  if (selectAllMobile)
    selectAllMobile.addEventListener("change", (e) =>
      toggleAll(e.target.checked)
    );

  checkboxes.forEach((cb) => {
    cb.addEventListener("change", updateButtonState);
  });
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

$(document).ready(function () {
  $(".sortable-table").DataTable({
    language: {
      url: "//cdn.datatables.net/plug-ins/1.13.6/i18n/pt-BR.json",
    },
    paging: false,
    searching: false,
    info: false,
    responsive: true,
    order: [],
  });
});
