// app\static\js\dashboard.js

document.addEventListener("DOMContentLoaded", function () {
  // Lógica para o seletor de mês do painel de movimentos
  $("#mes_ano_dashboard")
    .datepicker({
      format: "mm-yyyy",
      startView: "months",
      minViewMode: "months",
      language: "pt-BR",
      autoclose: true,
      orientation: "bottom right",
    })
    .on("changeDate", function (e) {
      document.getElementById("form-movimentos-mes").submit();
    });

  // Lógica para exibir a data atual no topo da página
  const dataAtualElement = document.getElementById("data-atual");
  if (dataAtualElement) {
    const hoje = new Date();
    const options = {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    };
    dataAtualElement.textContent = hoje.toLocaleDateString("pt-BR", options);
  }
});
