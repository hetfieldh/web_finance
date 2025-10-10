// app/static/js/ajax-forms.js

document.addEventListener("DOMContentLoaded", () => {
  const formAdicionarVerba = document.getElementById("form-adicionar-verba");
  const tabelaVerbasCorpo = document.getElementById("tabela-verbas-corpo");

  // --- LÓGICA PARA ADICIONAR VERBA ---
  if (formAdicionarVerba) {
    formAdicionarVerba.addEventListener("submit", function (event) {
      event.preventDefault();
      const formData = new FormData(this);
      fetch(this.action, {
        method: "POST",
        body: formData,
        headers: { "X-Requested-With": "XMLHttpRequest" },
      })
        .then((response) => {
          if (!response.ok) {
            return response.json().then((err) => {
              throw err;
            });
          }
          return response.json();
        })
        .then((data) => {
          if (data.success) {
            location.reload();
          } else {
            alert("Erro: " + (data.message || "Ocorreu um erro desconhecido."));
          }
        })
        .catch((error) => {
          console.error("Erro na requisição AJAX:", error);
          alert(
            "Erro ao adicionar verba: " +
              (error.message || "Verifique os dados e tente novamente.")
          );
        });
    });
  }

  // --- LÓGICA PARA EXCLUIR VERBA ---
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
              location.reload();
            } else {
              alert("Erro: " + data.message);
            }
          })
          .catch((error) => console.error("Erro na requisição AJAX:", error));
      }
    });
  }

  const loginInput = document.getElementById("login");
  const emailInput = document.getElementById("email");

  const debounce = (func, delay) => {
    let timeout;
    return function (...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), delay);
    };
  };

  if (loginInput || emailInput) {
    const checkAvailability = async (inputElement, feedbackElement) => {
      const fieldName = inputElement.id;
      const value = inputElement.value.trim();
      feedbackElement.innerHTML = "";
      if (value.length < 4) return;

      const form = inputElement.closest("form");
      let userIdToExclude = null;
      if (form && form.action) {
        const actionUrl = form.action;
        const match =
          actionUrl.match(/\/editar\/(\d+)/) || actionUrl.match(/\/perfil/);
        if (match && match[1]) {
          userIdToExclude = match[1];
        } else if (match && actionUrl.includes("/perfil")) {
          userIdToExclude = form.dataset.userId;
        }
      }

      try {
        let url = `/usuarios/check-field?field_name=${fieldName}&value=${encodeURIComponent(
          value
        )}`;
        if (userIdToExclude) {
          url += `&user_id=${userIdToExclude}`;
        }
        const response = await fetch(url);
        const data = await response.json();

        if (data.available) {
          feedbackElement.innerHTML = `<i class="fas fa-check-circle text-success me-1"></i><small class="text-success">${data.message}</small>`;
        } else {
          feedbackElement.innerHTML = `<i class="fas fa-times-circle text-danger me-1"></i><small class="text-danger">${data.message}</small>`;
        }
      } catch (error) {
        console.error("Erro na verificação AJAX:", error);
        feedbackElement.innerHTML = `<small class="text-warning">Não foi possível verificar a disponibilidade.</small>`;
      }
    };

    if (loginInput) {
      const loginFeedback = document.getElementById("login-feedback");
      loginInput.addEventListener(
        "keyup",
        debounce(() => checkAvailability(loginInput, loginFeedback), 500)
      );
    }

    if (emailInput) {
      const emailFeedback = document.getElementById("email-feedback");
      if (window.location.pathname.includes("/solicitacao/acesso")) {
        const formFields = document.querySelectorAll(
          'input[name="nome"], input[name="sobrenome"], textarea[name="justificativa"]'
        );
        const submitButton = document.querySelector('button[type="submit"]');

        const disableFormFields = (disabled) => {
          formFields.forEach((field) => {
            field.disabled = disabled;
          });
          if (submitButton) {
            submitButton.disabled = disabled;
          }
        };

        const checkEmailSolicitacao = async () => {
          const email = emailInput.value.trim();
          if (email.length < 5 || !email.includes("@")) {
            emailFeedback.innerHTML = "";
            disableFormFields(false);
            return;
          }
          try {
            const response = await fetch(
              `/solicitacao/check-email?email=${encodeURIComponent(email)}`
            );
            const data = await response.json();

            if (data.exists) {
              emailFeedback.innerHTML = `
                <div class="alert alert-info p-2 small mt-2">
                  <i class="fas fa-info-circle me-1"></i>
                  Já existe uma solicitação para este e-mail.
                  <a href="${data.status_url}" class="alert-link">Acesse</a>.
                </div>
              `;
              disableFormFields(true);
            } else if (data.user_exists) {
              emailFeedback.innerHTML = `
                <div class="alert alert-warning p-2 small mt-2">
                  <i class="fas fa-exclamation-triangle me-1"></i>
                  Este e-mail já está cadastrado.
                  <a href="${data.login_url}" class="alert-link">Tente fazer login</a>.
                </div>
              `;
              disableFormFields(true);
            } else {
              emailFeedback.innerHTML = `
                <div class="text-success small mt-2">
                  <i class="fas fa-check-circle me-1"></i>
                  E-mail disponível para solicitação.
                </div>
              `;
              disableFormFields(false);
            }
          } catch (error) {
            console.error(
              "Erro na verificação de e-mail de solicitação:",
              error
            );
            emailFeedback.innerHTML = "";
            disableFormFields(false);
          }
        };

        emailInput.addEventListener(
          "input",
          debounce(checkEmailSolicitacao, 500)
        );
      } else {
        emailInput.addEventListener(
          "keyup",
          debounce(() => checkAvailability(emailInput, emailFeedback), 500)
        );
      }
    }
  }
});
