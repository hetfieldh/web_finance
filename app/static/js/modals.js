// app/static/js/modals.js
console.log("modals.js carregado com sucesso!");

document.addEventListener("DOMContentLoaded", () => {
  const pagamentoModal = document.getElementById("pagamentoModal");
  if (pagamentoModal) {
    pagamentoModal.addEventListener("show.bs.modal", function (event) {
      const button = event.relatedTarget;
      const itemId = button.getAttribute("data-item-id");
      const itemTipo = button.getAttribute("data-item-tipo");
      const itemValor = button.getAttribute("data-item-valor");
      const itemDescricao = button.getAttribute("data-item-descricao");
      const modal = this;
      modal.querySelector("#item_id").value = itemId;
      modal.querySelector("#item_tipo").value = itemTipo;
      modal.querySelector("#valor_pago").value = itemValor;
      modal.querySelector("#item_descricao").value = itemDescricao;
    });
  }

  const recebimentoModal = document.getElementById("recebimentoModal");
  if (recebimentoModal) {
    recebimentoModal.addEventListener("show.bs.modal", function (event) {
      const button = event.relatedTarget;
      const itemId = button.getAttribute("data-item-id");
      const itemTipo = button.getAttribute("data-item-tipo");
      const itemValor = button.getAttribute("data-item-valor");
      const itemDescricao = button.getAttribute("data-item-descricao");
      const modal = this;
      const hoje = new Date();
      const ano = hoje.getFullYear();
      const mes = String(hoje.getMonth() + 1).padStart(2, "0");
      const dia = String(hoje.getDate()).padStart(2, "0");
      const dataFormatada = `${ano}-${mes}-${dia}`;
      modal.querySelector("#item_id").value = itemId;
      modal.querySelector("#item_tipo").value = itemTipo;
      modal.querySelector("#valor_recebido").value = itemValor;
      modal.querySelector("#item_descricao").value = itemDescricao;
      modal.querySelector("#data_recebimento").value = dataFormatada;
    });
  }

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
});
