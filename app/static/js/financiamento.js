// app/static/js/financiamento.js

console.log("financiamento.js carregado com sucesso!");

document.addEventListener("DOMContentLoaded", () => {

    const formImportar = document.getElementById("form-importar-csv");
    if (formImportar) {
        formImportar.addEventListener("submit", function () {
            const submitButton = formImportar.querySelector('button[type="submit"]');
            const buttonSpinner = submitButton.querySelector(".spinner-border");
            const buttonText = submitButton.querySelector(".button-text");
            const fileInput = document.getElementById("csv_file");
            if (fileInput && fileInput.files.length > 0) {
                submitButton.disabled = true;
                if (buttonText) buttonText.classList.add("d-none");
                if (buttonSpinner) buttonSpinner.classList.remove("d-none");
            }
        });
    }

    const formAmortizacao = document.getElementById("form-amortizacao");
    if (formAmortizacao) {
        const valorAmortizacaoInput = document.getElementById("valor_amortizacao");
        const checkboxes = document.querySelectorAll(".parcela-checkbox");
        const checkboxSelecionarTodas = document.getElementById("selecionar-todas");
        const resumoValor = document.getElementById("resumo-valor");
        const resumoParcelas = document.getElementById("resumo-parcelas");
        const resumoValorParcela = document.getElementById("resumo-valor-parcela");

        function atualizarResumo() {
            const valorTotal = parseFloat(valorAmortizacaoInput.value) || 0;
            const parcelasSelecionadas = document.querySelectorAll(".parcela-checkbox:checked").length;

            resumoValor.textContent = valorTotal.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
            resumoParcelas.textContent = parcelasSelecionadas;

            if (parcelasSelecionadas > 0 && valorTotal > 0) {
                const valorPorParcela = valorTotal / parcelasSelecionadas;
                resumoValorParcela.textContent = valorPorParcela.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
            } else {
                resumoValorParcela.textContent = "R$ 0,00";
            }
        }

        if (valorAmortizacaoInput) {
            valorAmortizacaoInput.addEventListener("input", atualizarResumo);
        }

        checkboxes.forEach(cb => cb.addEventListener("change", atualizarResumo));

        if (checkboxSelecionarTodas) {
            checkboxSelecionarTodas.addEventListener('change', function() {
                checkboxes.forEach(checkbox => {
                    checkbox.checked = this.checked;
                });
                atualizarResumo();
            });
        }

        atualizarResumo();
    }
});
