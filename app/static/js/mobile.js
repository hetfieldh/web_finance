// app\static\js\mobile.js

// app/static/js/mobile.js

$(document).ready(function () {
  // Lógica para Expandir/Recolher linhas na Tabela de Crediário Detalhado (Desktop)
  $(".toggle-row").click(function () {
    var target = $(this).data("target");
    var icon = $(this).find(".toggle-icon");

    // Alterna visibilidade
    $(target).toggle();

    // Alterna ícone
    if ($(target).is(":visible")) {
      icon
        .removeClass("fa-plus-square fa-caret-right")
        .addClass("fa-minus-square fa-caret-down");
    } else {
      // Se estiver fechando (recolhendo) um Grupo, fecha também os Subgrupos filhos recursivamente
      if (target && target.startsWith(".grupo-child")) {
        var childrenRows = $(target);
        childrenRows.each(function () {
          var childTarget = $(this).data("target");
          if (childTarget) {
            $(childTarget).hide();
            // Reseta ícone do filho (Subgrupo) para "fechado"
            $(this)
              .find(".toggle-icon")
              .removeClass("fa-minus-square fa-caret-down")
              .addClass("fa-plus-square fa-caret-right");
          }
        });
      }
      icon
        .removeClass("fa-minus-square fa-caret-down")
        .addClass("fa-plus-square fa-caret-right");
    }
  });
});
