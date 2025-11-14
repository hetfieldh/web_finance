// app/static/js/modals.js

document.addEventListener("DOMContentLoaded", () => {
  const rejeicaoModal = document.getElementById("rejeicaoModal");
  if (rejeicaoModal) {
    rejeicaoModal.addEventListener("show.bs.modal", function (event) {
      const button = event.relatedTarget;
      const solicitacaoId = button.getAttribute("data-solicitacao-id");
      const form = rejeicaoModal.querySelector("#form-rejeicao");
      const solicitacaoIdInput = form.querySelector("#solicitacao_id");
      solicitacaoIdInput.value = solicitacaoId;
    });
  }

  const confirmModal = document.getElementById("confirmDeleteModal");
  if (confirmModal) {
    confirmModal.addEventListener("show.bs.modal", function (event) {
      const button = event.relatedTarget;

      const formAction = button.getAttribute("data-form-action");

      const form = confirmModal.querySelector(
        "#confirm-form-confirmDeleteModal"
      );

      if (form && formAction) {
        form.setAttribute("action", formAction);
      }
    });
  }

  const confirmEstornarModal = document.getElementById("confirmEstornarModal");
  if (confirmEstornarModal) {
    confirmEstornarModal.addEventListener("show.bs.modal", function (event) {
      const button = event.relatedTarget;

      const itemId = button.getAttribute("data-item-id");
      const itemTipo = button.getAttribute("data-item-tipo");
      const mesAno = button.getAttribute("data-mes-ano");

      const modalItemIdInput = confirmEstornarModal.querySelector(
        "#confirmEstornarModal-item-id"
      );
      const modalItemTipoInput = confirmEstornarModal.querySelector(
        "#confirmEstornarModal-item-tipo"
      );
      const modalMesAnoInput = confirmEstornarModal.querySelector(
        "#confirmEstornarModal-mes-ano"
      );

      if (modalItemIdInput) modalItemIdInput.value = itemId;
      if (modalItemTipoInput) modalItemTipoInput.value = itemTipo;
      if (modalMesAnoInput) modalMesAnoInput.value = mesAno;
    });
  }
});
