// app/static/js/form-spinner.js

document.addEventListener("DOMContentLoaded", () => {
  const forms = document.querySelectorAll(".form-with-spinner");

  forms.forEach((form) => {
    form.addEventListener("submit", function () {
      const submitButton = form.querySelector('button[type="submit"]');
      if (submitButton) {
        const buttonSpinner = submitButton.querySelector(".spinner-border");
        const buttonIcon = submitButton.querySelector(".button-icon");

        submitButton.disabled = true;

        if (buttonIcon) buttonIcon.classList.add("d-none");
        if (buttonSpinner) buttonSpinner.classList.remove("d-none");
      }
    });
  });
});
