// app/static/js/form-spinner.js

console.log("form-spinner.js carregado!");

document.addEventListener("DOMContentLoaded", () => {
  // Procura todos os formulários que devem ter um spinner no submit
  const forms = document.querySelectorAll(".form-with-spinner");

  forms.forEach((form) => {
    form.addEventListener("submit", function () {
      const submitButton = form.querySelector('button[type="submit"]');
      if (submitButton) {
        const buttonSpinner = submitButton.querySelector(".spinner-border");
        const buttonIcon = submitButton.querySelector(".button-icon");

        // Desativa o botão para prevenir múltiplos cliques
        submitButton.disabled = true;

        // Esconde o ícone e mostra o spinner
        if (buttonIcon) buttonIcon.classList.add("d-none");
        if (buttonSpinner) buttonSpinner.classList.remove("d-none");
      }
    });
  });
});
