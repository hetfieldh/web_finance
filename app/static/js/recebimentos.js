// app/static/js/recebimentos.js

document.addEventListener("DOMContentLoaded", function () {
  var recebimentoModal = document.getElementById("recebimentoModal");

  if (recebimentoModal) {
    recebimentoModal.addEventListener("show.bs.modal", function (event) {
      var button = event.relatedTarget;
      var itemId = button.getAttribute("data-item-id");
      var itemTipo = button.getAttribute("data-item-tipo");
      var itemValor = button.getAttribute("data-item-valor");
      var itemDescricao = button.getAttribute("data-item-descricao");
      var contaSugeridaId = button.getAttribute("data-conta-sugerida-id");
      var modalForm = recebimentoModal.querySelector("form");
      var itemIdInput = modalForm.querySelector('input[name="item_id"]');
      var itemTipoInput = modalForm.querySelector('input[name="item_tipo"]');
      var valorRecebidoInput = modalForm.querySelector(
        'input[name="valor_recebido"]'
      );
      var itemDescricaoInput = modalForm.querySelector(
        'input[name="item_descricao"]'
      );
      var contaSelectInput = modalForm.querySelector('select[name="conta_id"]');

      if (itemIdInput) itemIdInput.value = itemId;
      if (itemTipoInput) itemTipoInput.value = itemTipo;
      if (valorRecebidoInput) valorRecebidoInput.value = itemValor;
      if (itemDescricaoInput) itemDescricaoInput.value = itemDescricao;

      if (contaSelectInput && contaSugeridaId) {
        contaSelectInput.value = contaSugeridaId;
      } else if (contaSelectInput) {
        contaSelectInput.selectedIndex = 0;
      }
    });
  }
});
