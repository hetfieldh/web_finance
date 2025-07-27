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
