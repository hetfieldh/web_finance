// app/static/js/script.js

// Exibe uma mensagem no console para confirmar que o script foi carregado
console.log("script.js carregado com sucesso!");

// Adiciona um listener para quando o DOM estiver completamente carregado
document.addEventListener("DOMContentLoaded", () => {
  // --- 1. Script para toggler da sidebar ---
  const sidebarToggle = document.getElementById("sidebarToggle");
  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", () => {
      document.getElementById("wrapper").classList.toggle("toggled");
    });
  }

  // --- 2. Script para inicializar tooltips do Bootstrap ---
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // --- 3. Script para exibir a data atual no Dashboard ---
  const dataAtual = new Date();
  const opcoes = {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  };
  const formatoElegante = new Intl.DateTimeFormat("pt-BR", opcoes).format(
    dataAtual
  );
  const elementoDataAtual = document.getElementById("data-atual");
  if (elementoDataAtual) {
    const frase =
      formatoElegante.charAt(0).toUpperCase() + formatoElegante.slice(1);
    elementoDataAtual.innerText = frase;
  }

  // --- 4. Lógica para o Botão "Voltar ao Topo" ---
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

  // --- 6. Script para Modal de Pagamento ---
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

  // --- 7. Script para Modal de Recebimento ---
  const recebimentoModal = document.getElementById("recebimentoModal");
  if (recebimentoModal) {
    recebimentoModal.addEventListener("show.bs.modal", function (event) {
      const button = event.relatedTarget;
      const itemId = button.getAttribute("data-item-id");
      const itemTipo = button.getAttribute("data-item-tipo");
      const itemValor = button.getAttribute("data-item-valor");
      const itemDescricao = button.getAttribute("data-item-descricao");
      const itemData = button.getAttribute("data-item-data");
      const modal = this;
      modal.querySelector("#item_id").value = itemId;
      modal.querySelector("#item_tipo").value = itemTipo;
      modal.querySelector("#valor_recebido").value = itemValor;
      modal.querySelector("#item_descricao").value = itemDescricao;
      modal.querySelector("#data_recebimento").value = itemData;
    });
  }

  // --- 8. Lógica para formulário dinâmico de Lançamento Bancário ---
  const formMovimentacao = document.getElementById("form-movimentacao");
  if (formMovimentacao) {
    const contaId = document.getElementById("container-conta_id");
    const dataMovimento = document.getElementById("container-data_movimento");
    const valor = document.getElementById("container-valor");
    const descricao = document.getElementById("container-descricao");
    const simplesFields = document.getElementById(
      "movimentacao_simples_fields"
    );
    const transferenciaFields = document.getElementById("transferencia_fields");
    const placeholders = {
      simples: {
        conta_id: document.getElementById("placeholder-simples-conta_id"),
        data_movimento: document.getElementById(
          "placeholder-simples-data_movimento"
        ),
        valor: document.getElementById("placeholder-simples-valor"),
        descricao: document.getElementById("placeholder-simples-descricao"),
      },
      transferencia: {
        conta_id: document.getElementById("placeholder-transf-conta_origem"),
        data_movimento: document.getElementById(
          "placeholder-transf-data_movimento"
        ),
        valor: document.getElementById("placeholder-transf-valor"),
        descricao: document.getElementById("placeholder-transf-descricao"),
      },
    };

    function moverCampos() {
      const tipoSelecionado = formMovimentacao.querySelector(
        'input[name="tipo_operacao"]:checked'
      ).value;
      if (tipoSelecionado === "simples") {
        simplesFields.style.display = "block";
        transferenciaFields.style.display = "none";
        placeholders.simples.conta_id.appendChild(contaId);
        placeholders.simples.data_movimento.appendChild(dataMovimento);
        placeholders.simples.valor.appendChild(valor);
        placeholders.simples.descricao.appendChild(descricao);
        contaId.querySelector("label").textContent = "Conta Bancária";
        descricao.querySelector("label").textContent = "Descrição (opcional)";
      } else {
        simplesFields.style.display = "none";
        transferenciaFields.style.display = "block";
        placeholders.transferencia.conta_id.appendChild(contaId);
        placeholders.transferencia.data_movimento.appendChild(dataMovimento);
        placeholders.transferencia.valor.appendChild(valor);
        placeholders.transferencia.descricao.appendChild(descricao);
        contaId.querySelector("label").textContent = "Conta Origem";
        descricao.querySelector("label").textContent =
          "Descrição da Transferência (opcional)";
      }
    }
    formMovimentacao
      .querySelectorAll('input[name="tipo_operacao"]')
      .forEach((radio) => {
        radio.addEventListener("change", moverCampos);
      });
    moverCampos();
  }

  // --- 9. Lógica para o formulário de transferência ---
  const contaOrigemSelect = document.querySelector("#conta_id select");
  const contaDestinoSelect = document.querySelector(
    "#transferencia_fields select[name='conta_destino_id']"
  );
  if (contaOrigemSelect && contaDestinoSelect) {
    const atualizarContaDestino = () => {
      const selectedOrigemId = contaOrigemSelect.value;
      for (const option of contaDestinoSelect.options) {
        option.style.display =
          option.value === selectedOrigemId && option.value !== ""
            ? "none"
            : "block";
      }
      if (contaDestinoSelect.value === selectedOrigemId) {
        contaDestinoSelect.value = "";
      }
    };
    contaOrigemSelect.addEventListener("change", atualizarContaDestino);
    atualizarContaDestino();
  }

  // --- 10. Lógica para filtros dinâmicos do Extrato Desp/Rec ---
  const tipoRelatorioSelect = document.getElementById("tipo_relatorio");
  if (tipoRelatorioSelect) {
    const filtroMensal = document.getElementById("filtro_mensal");
    const filtroConta = document.getElementById("filtro_conta");
    const filtroDataInicio = document.getElementById("filtro_data_inicio");
    const filtroDataFim = document.getElementById("filtro_data_fim");
    function toggleFilters() {
      if (tipoRelatorioSelect.value === "mensal") {
        filtroMensal.style.display = "block";
        filtroConta.style.display = "none";
        filtroDataInicio.style.display = "none";
        filtroDataFim.style.display = "none";
      } else {
        filtroMensal.style.display = "none";
        filtroConta.style.display = "block";
        filtroDataInicio.style.display = "block";
        filtroDataFim.style.display = "block";
      }
    }
    tipoRelatorioSelect.addEventListener("change", toggleFilters);
    toggleFilters();
  }

  // --- 11. Lógica AJAX para Gerenciar Folha de Pagamento ---
  const formAdicionarVerba = document.getElementById("form-adicionar-verba");
  const tabelaVerbasCorpo = document.getElementById("tabela-verbas-corpo");
  if (formAdicionarVerba) {
    formAdicionarVerba.addEventListener("submit", function (event) {
      event.preventDefault();
      const formData = new FormData(this);
      fetch(this.action, {
        method: "POST",
        body: formData,
        headers: { "X-Requested-With": "XMLHttpRequest" },
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            const novaLinha = document.createElement("tr");
            novaLinha.id = `verba-${data.item.id}`;
            novaLinha.innerHTML = `<td>${data.item.nome}</td><td><span class="badge bg-secondary">${data.item.tipo}</span></td><td class="text-end">R$ ${data.item.valor.toFixed(2)}</td><td class="text-center"><button type="button" class="btn-excluir-verba p-0 border-0 bg-transparent text-danger" data-url="/salario/lancamento/item/excluir/${data.item.id}" data-id="${data.item.id}" title="Excluir"><i class="fas fa-trash-alt"></i></button></td>`;
            const linhaVazia =
              tabelaVerbasCorpo.querySelector('td[colspan="4"]');
            if (linhaVazia) {
              linhaVazia.parentElement.remove();
            }
            tabelaVerbasCorpo.appendChild(novaLinha);
            formAdicionarVerba.reset();
          } else {
            alert("Erro: " + data.message);
          }
        })
        .catch((error) => console.error("Erro na requisição AJAX:", error));
    });
  }
  if (tabelaVerbasCorpo) {
    tabelaVerbasCorpo.addEventListener("click", function (event) {
      const target = event.target.closest(".btn-excluir-verba");
      if (!target) return;
      if (confirm("Tem certeza que deseja remover esta verba?")) {
        const csrfToken = document.querySelector(
          'input[name="csrf_token"]'
        ).value;
        fetch(target.dataset.url, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": csrfToken,
          },
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              document.getElementById(`verba-${data.deleted_item_id}`).remove();
            } else {
              alert("Erro: " + data.message);
            }
          })
          .catch((error) => console.error("Erro na requisição AJAX:", error));
      }
    });
  }

  // --- 12. Lógica para preenchimento automático da data de vencimento no Lançamento Único ---
  const formLancamentoUnico = document.getElementById("form-lancamento-unico");
  if (formLancamentoUnico) {
    const vencimentosDataElement = document.getElementById("vencimentos-data");
    if (!vencimentosDataElement) {
      console.error("Contêiner de dados #vencimentos-data não encontrado!");
      return;
    }
    const vencimentosMap = JSON.parse(
      vencimentosDataElement.textContent || "{}"
    );
    const despRecSelect = document.getElementById("desp_rec_id");
    const dataVencimentoInput = document.getElementById("data_vencimento");

    if (despRecSelect && dataVencimentoInput) {
      despRecSelect.addEventListener("change", function () {
        const selectedId = this.value;
        const diaVencimento = vencimentosMap[selectedId];

        if (diaVencimento) {
          const hoje = new Date();
          const dataAtualNoCampo = dataVencimentoInput.value
            ? new Date(dataVencimentoInput.value + "T00:00:00")
            : hoje;
          let ano = dataAtualNoCampo.getFullYear();
          let mes = dataAtualNoCampo.getMonth() + 1;
          let ultimoDiaDoMes = new Date(ano, mes, 0).getDate();
          let diaFinal = Math.min(diaVencimento, ultimoDiaDoMes);
          const mesFormatado = String(mes).padStart(2, "0");
          const diaFormatado = String(diaFinal).padStart(2, "0");
          dataVencimentoInput.value = `${ano}-${mesFormatado}-${diaFormatado}`;
        }
      });
    }
  }

  // --- 13. Lógica para preenchimento automático da data na Geração de Previsão ---
  const formGerarPrevisao = document.getElementById("form-gerar-previsao");
  if (formGerarPrevisao) {
    const vencimentosDataElement = document.getElementById(
      "vencimentos-previsao-data"
    );
    if (!vencimentosDataElement) {
      console.error(
        "Contêiner de dados #vencimentos-previsao-data não encontrado!"
      );
      return;
    }
    const vencimentosMap = JSON.parse(
      vencimentosDataElement.textContent || "{}"
    );
    const despRecSelect = document.getElementById("desp_rec_id_previsao");
    const dataInicioInput = document.getElementById("data_inicio_previsao");

    if (despRecSelect && dataInicioInput) {
      despRecSelect.addEventListener("change", function () {
        const selectedId = this.value;
        const diaVencimento = vencimentosMap[selectedId];

        if (diaVencimento) {
          const hoje = new Date();
          const dataAtualNoCampo = dataInicioInput.value
            ? new Date(dataInicioInput.value + "T00:00:00")
            : hoje;
          let ano = dataAtualNoCampo.getFullYear();
          let mes = dataAtualNoCampo.getMonth() + 1;
          let ultimoDiaDoMes = new Date(ano, mes, 0).getDate();
          let diaFinal = Math.min(diaVencimento, ultimoDiaDoMes);
          const mesFormatado = String(mes).padStart(2, "0");
          const diaFormatado = String(diaFinal).padStart(2, "0");
          dataInicioInput.value = `${ano}-${mesFormatado}-${diaFormatado}`;
        }
      });
    }
  }
});
