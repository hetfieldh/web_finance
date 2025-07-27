// app/static/js/script.js

// Exibe uma mensagem no console para confirmar que o script foi carregado
console.log("script.js carregado com sucesso!");

// Adiciona um listener para quando o DOM estiver completamente carregado
document.addEventListener('DOMContentLoaded', () => {
    // Obtém o botão de alternar a sidebar
    const sidebarToggle = document.getElementById("sidebarToggle");
    // Verifica se o botão existe
    if (sidebarToggle) {
        // Adiciona um evento de clique para alternar a classe 'toggled' no wrapper
        sidebarToggle.addEventListener("click", () => {
            document.getElementById("wrapper").classList.toggle("toggled");
        });
    }
});

// Exibe a data atual
document.addEventListener("DOMContentLoaded", function () {
    const dataAtual = new Date();

    const opcoes = {
        weekday: 'long', // dia da semana por extenso
        day: 'numeric',
        month: 'long',   // mês por extenso
        year: 'numeric'
    };

    const formatoElegante = new Intl.DateTimeFormat('pt-BR', opcoes).format(dataAtual);

    const elemento = document.getElementById("data-atual");

    if (elemento) {
        // Capitaliza a primeira letra do dia da semana (opcional, por estética)
        const frase = formatoElegante.charAt(0).toUpperCase() + formatoElegante.slice(1);
        elemento.innerText = frase;
    }
});
