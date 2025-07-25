console.log("script.js carregado com sucesso!");

// Script para toggler da sidebar
document.addEventListener('DOMContentLoaded', () => {
    const sidebarToggle = document.getElementById("sidebarToggle");
    if (sidebarToggle) {
        sidebarToggle.addEventListener("click", () => {
            document.getElementById("wrapper").classList.toggle("toggled");
        });
    }
});