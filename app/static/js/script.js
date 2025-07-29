// app/static/js/script.js

// Adiciona um listener para quando o DOM estiver completamente carregado
document.addEventListener('DOMContentLoaded', () => {
    const sidebarToggle = document.getElementById("sidebarToggle");
    if (sidebarToggle) {
        sidebarToggle.addEventListener("click", () => {
            document.getElementById("wrapper").classList.toggle("toggled");
        });
    }

    // --- Scripts para conta_movimentos/add.html (visibilidade de campos de transferência) ---
    const isTransferenciaCheckboxContainer = document.getElementById('is_transferencia_field_container');
    const isTransferenciaCheckbox = document.getElementById('is_transferencia');
    const contaDestinoField = document.getElementById('conta_destino_field');
    const contaTransacaoSelect = document.getElementById('conta_transacao_id');

    if (contaTransacaoSelect && isTransferenciaCheckbox && contaDestinoField && isTransferenciaCheckboxContainer) {
        const tipoMovimentoMap = {};
        Array.from(contaTransacaoSelect.options).forEach(option => {
            const match = option.textContent.match(/\((Crédito|Débito)\)/);
            if (match) {
                tipoMovimentoMap[option.value] = match[1];
            }
        });

        function updateTransferenciaFieldsVisibility() {
            const selectedTransacaoId = contaTransacaoSelect.value;
            const tipoMovimento = tipoMovimentoMap[selectedTransacaoId];

            if (tipoMovimento === 'Débito') {
                isTransferenciaCheckboxContainer.style.display = 'block';
                if (isTransferenciaCheckbox.checked) {
                    contaDestinoField.style.display = 'block';
                } else {
                    contaDestinoField.style.display = 'none';
                }
            } else {
                isTransferenciaCheckboxContainer.style.display = 'none';
                contaDestinoField.style.display = 'none';
                isTransferenciaCheckbox.checked = false; 
            }
        }

        contaTransacaoSelect.addEventListener('change', updateTransferenciaFieldsVisibility);
        isTransferenciaCheckbox.addEventListener('change', updateTransferenciaFieldsVisibility); 
        
        updateTransferenciaFieldsVisibility();
    }

    // --- Scripts para inicializar tooltips do Bootstrap (usado em várias telas) ---
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })

    // --- Exibe a data atual (funcionalidade existente do seu código) ---
    const dataAtual = new Date();

    const opcoes = {
        weekday: 'long', 
        day: 'numeric',
        month: 'long', 
        year: 'numeric'
    };

    const formatoElegante = new Intl.DateTimeFormat('pt-BR', opcoes).format(dataAtual);

    const elementoDataAtual = document.getElementById("data-atual"); 

    if (elementoDataAtual) {
        const frase = formatoElegante.charAt(0).toUpperCase() + formatoElegante.slice(1);
        elementoDataAtual.innerText = frase;
    }
});
