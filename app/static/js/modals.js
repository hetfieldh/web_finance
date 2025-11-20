// app/static/js/modals.js

// Modal de exclusão
document.addEventListener("DOMContentLoaded", function () {
  const confirmDeleteModal = document.getElementById("confirmDeleteModal");
  if (confirmDeleteModal) {
    confirmDeleteModal.addEventListener("show.bs.modal", function (event) {
      const button = event.relatedTarget;
      const actionUrl = button.getAttribute("data-form-action");
      const modalForm = confirmDeleteModal.querySelector("form");
      if (modalForm && actionUrl) {
        modalForm.action = actionUrl;
      }
    });
  }

  // Modal de estorno
  const confirmEstornarModal = document.getElementById("confirmEstornarModal");
  if (confirmEstornarModal) {
    confirmEstornarModal.addEventListener("show.bs.modal", function (event) {
      const button = event.relatedTarget;
      const itemId = button.getAttribute("data-item-id");
      const itemTipo = button.getAttribute("data-item-tipo");
      const mesAno = button.getAttribute("data-mes-ano");
      const formAction = button.getAttribute("data-form-action");

      const modalBodyInputId = confirmEstornarModal.querySelector(
        "input[name='item_id']"
      );
      const modalBodyInputTipo = confirmEstornarModal.querySelector(
        "input[name='item_tipo']"
      );
      const modalBodyInputMesAno = confirmEstornarModal.querySelector(
        "input[name='mes_ano']"
      );
      const modalForm = confirmEstornarModal.querySelector("form");

      if (modalBodyInputId) modalBodyInputId.value = itemId;
      if (modalBodyInputTipo) modalBodyInputTipo.value = itemTipo;
      if (modalBodyInputMesAno) modalBodyInputMesAno.value = mesAno;
      if (modalForm && formAction) {
        modalForm.action = formAction;
      }
    });
  }

  // Modal de rejeição (Solicitações)
  const rejeicaoModal = document.getElementById("rejeicaoModal");
  if (rejeicaoModal) {
    rejeicaoModal.addEventListener("show.bs.modal", function (event) {
      const button = event.relatedTarget;
      const solicitacaoId = button.getAttribute("data-solicitacao-id");
      const form = rejeicaoModal.querySelector("#form-rejeicao");
      const solicitacaoIdInput = form.querySelector("#solicitacao_id");

      if (solicitacaoIdInput) {
        solicitacaoIdInput.value = solicitacaoId;
      } else {
        const inputByName = form.querySelector('input[name="solicitacao_id"]');
        if (inputByName) inputByName.value = solicitacaoId;
      }
    });
  }
});
