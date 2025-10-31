// app/static/js/forms.js (VERSÃO COMPLETA E FINAL)

document.addEventListener("DOMContentLoaded", () => {
  const tipoContaSelect = document.getElementById("tipo-conta-select");
  const limiteContainer = document.getElementById("limite-container");

  if (tipoContaSelect && limiteContainer) {
    const limiteInput = limiteContainer.querySelector("input");
    const toggleLimiteField = () => {
      const tipoSelecionado = tipoContaSelect.value;
      const tiposComLimite = ["Corrente", "Digital"];
      if (tiposComLimite.includes(tipoSelecionado)) {
        limiteContainer.style.display = "block";
      } else {
        limiteContainer.style.display = "none";
        if (limiteInput) {
          limiteInput.value = "0.00";
        }
      }
    };
    tipoContaSelect.addEventListener("change", toggleLimiteField);
    toggleLimiteField();
  }

  const tipoContaSelectEdit = document.getElementById("tipo-conta-select-edit");
  const limiteContainerEdit = document.getElementById("limite-container-edit");

  if (tipoContaSelectEdit && limiteContainerEdit) {
    const tipoSelecionado = tipoContaSelectEdit.value;
    const tiposComLimite = ["Corrente", "Digital"];
    if (!tiposComLimite.includes(tipoSelecionado)) {
      limiteContainerEdit.style.display = "none";
    }
  }

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

  const contaOrigemSelect = document.querySelector("select#conta_id");
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

  const formLancamentoUnico = document.getElementById("form-lancamento-unico");
  if (formLancamentoUnico) {
    const vencimentosDataElement = document.getElementById("vencimentos-data");
    if (vencimentosDataElement) {
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
  }

  const formGerarPrevisao = document.getElementById("form-gerar-previsao");
  if (formGerarPrevisao) {
    const vencimentosDataElement = document.getElementById(
      "vencimentos-previsao-data"
    );
    if (vencimentosDataElement) {
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
  }

  const senhaInput = document.getElementById("senha");
  if (senhaInput) {
    const confirmarSenhaInput = document.getElementById("confirmar_senha");
    const toggleSenhaBtn = document.getElementById("toggleSenha");
    const toggleConfirmarSenhaBtn = document.getElementById(
      "toggleConfirmarSenha"
    );
    const strengthBar = document.getElementById("password-strength-bar");
    const strengthText = document.getElementById("password-strength-text");

    const togglePasswordVisibility = (input, iconId) => {
      const icon = document.getElementById(iconId);
      if (input.type === "password") {
        input.type = "text";
        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");
      } else {
        input.type = "password";
        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");
      }
    };

    if (toggleSenhaBtn) {
      toggleSenhaBtn.addEventListener("click", () => {
        togglePasswordVisibility(senhaInput, "toggleSenhaIcon");
      });
    }

    if (toggleConfirmarSenhaBtn && confirmarSenhaInput) {
      toggleConfirmarSenhaBtn.addEventListener("click", () => {
        togglePasswordVisibility(
          confirmarSenhaInput,
          "toggleConfirmarSenhaIcon"
        );
      });
    }

    if (strengthBar && strengthText) {
      senhaInput.addEventListener("input", () => {
        const password = senhaInput.value;
        let score = 0;
        let text = "";
        let color = "";
        if (password.length >= 8) score++;
        if (/[A-Z]/.test(password)) score++;
        if (/[a-z]/.test(password)) score++;
        if (/[0-9]/.test(password)) score++;
        if (/[^A-Za-z0-9]/.test(password)) score++;
        switch (score) {
          case 0:
          case 1:
          case 2:
            text = "Fraca";
            color = "bg-danger";
            break;
          case 3:
            text = "Média";
            color = "bg-warning";
            break;
          case 4:
          case 5:
            text = "Forte";
            color = "bg-success";
            break;
        }
        if (password.length === 0) {
          strengthBar.style.width = "0%";
          strengthText.textContent = "";
        } else {
          strengthBar.style.width = (score / 5) * 100 + "%";
          strengthBar.className = "progress-bar " + color;
          strengthText.textContent = `Força da senha: ${text}`;
        }
      });
    }
  }

  const formAmortizacao = document.getElementById("form-amortizacao");
  if (formAmortizacao) {
    const valorAmortizacaoInput = document.getElementById("valor_amortizacao");
    const checkboxes = document.querySelectorAll(".parcela-checkbox");
    const resumoValor = document.getElementById("resumo-valor");
    const resumoParcelas = document.getElementById("resumo-parcelas");
    const resumoValorParcela = document.getElementById("resumo-valor-parcela");

    function atualizarResumo() {
      const valorTotal = parseFloat(valorAmortizacaoInput.value) || 0;
      const parcelasSelecionadas = document.querySelectorAll(
        ".parcela-checkbox:checked"
      ).length;
      resumoValor.textContent = valorTotal.toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL",
      });
      resumoParcelas.textContent = parcelasSelecionadas;
      if (parcelasSelecionadas > 0 && valorTotal > 0) {
        const valorPorParcela = valorTotal / parcelasSelecionadas;
        resumoValorParcela.textContent = valorPorParcela.toLocaleString(
          "pt-BR",
          { style: "currency", currency: "BRL" }
        );
      } else {
        resumoValorParcela.textContent = "R$ 0,00";
      }
    }

    valorAmortizacaoInput.addEventListener("input", atualizarResumo);
    checkboxes.forEach((cb) => cb.addEventListener("change", atualizarResumo));
    atualizarResumo();
  }

  const transacaoSelect = document.getElementById("conta_transacao_id");
  function styleSelectedTransacao() {
    if (!transacaoSelect) return;

    const selectedOption =
      transacaoSelect.options[transacaoSelect.selectedIndex];

    resetSelectStyle();

    if (selectedOption && selectedOption.value) {
      const text = selectedOption.textContent;

      if (text.includes("(+)")) {
        transacaoSelect.style.backgroundColor = "var(--wf-box-positivo)";
        transacaoSelect.style.color = "var(--wf-texto-positivo)";
        transacaoSelect.style.fontWeight = "bold";
      } else if (text.includes("(-)")) {
        transacaoSelect.style.backgroundColor = "var(--wf-box-negativo)";
        transacaoSelect.style.color = "var(--wf-texto-negativo)";
        transacaoSelect.style.fontWeight = "bold";
      }
    }
  }

  function resetSelectStyle() {
    if (!transacaoSelect) return;
    transacaoSelect.style.backgroundColor = "";
    transacaoSelect.style.color = "";
    transacaoSelect.style.fontWeight = "";
  }

  if (transacaoSelect) {
    styleSelectedTransacao();
    transacaoSelect.addEventListener("mousedown", resetSelectStyle);
    transacaoSelect.addEventListener("change", styleSelectedTransacao);
  }
});
