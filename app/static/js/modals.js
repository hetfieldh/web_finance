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

document.addEventListener("DOMContentLoaded", function () {
  // Lógica para o modal de confirmação de exclusão ou outras ações
  const confirmModal = document.getElementById("confirmDeleteModal");
  if (confirmModal) {
    confirmModal.addEventListener("show.bs.modal", function (event) {
      // Botão que acionou o modal
      const button = event.relatedTarget;

      // Extrai a URL da ação do atributo data-form-action do botão
      const formAction = button.getAttribute("data-form-action");

      // Encontra o formulário dentro do modal
      const form = confirmModal.querySelector(
        "#confirm-form-confirmDeleteModal"
      );

      // Define o atributo 'action' do formulário com a URL correta
      if (form && formAction) {
        form.setAttribute("action", formAction);
      }
    });
  }
  // NOVA LÓGICA PARA O MODAL DE ESTORNO GENÉRICO
  const confirmEstornarModal = document.getElementById("confirmEstornarModal");
  if (confirmEstornarModal) {
    confirmEstornarModal.addEventListener("show.bs.modal", function (event) {
      const button = event.relatedTarget;

      // Extrai as informações dos atributos data-* do botão
      const itemId = button.getAttribute("data-item-id");
      const itemTipo = button.getAttribute("data-item-tipo");
      const mesAno = button.getAttribute("data-mes-ano");

      // Encontra os inputs hidden dentro do modal de estorno
      const modalItemIdInput = confirmEstornarModal.querySelector(
        "#confirmEstornarModal-item-id"
      );
      const modalItemTipoInput = confirmEstornarModal.querySelector(
        "#confirmEstornarModal-item-tipo"
      );
      const modalMesAnoInput = confirmEstornarModal.querySelector(
        "#confirmEstornarModal-mes-ano"
      );

      // Atualiza os valores dos inputs
      if (modalItemIdInput) modalItemIdInput.value = itemId;
      if (modalItemTipoInput) modalItemTipoInput.value = itemTipo;
      if (modalMesAnoInput) modalMesAnoInput.value = mesAno;
    });
  }
});
