// app\static\js\crediario.js

document.addEventListener("DOMContentLoaded", function () {
  const urlParams = new URLSearchParams(window.location.search);

  if (urlParams.has("trigger_sync")) {
    const modalElement = document.getElementById("modalSugestaoSync");

    if (modalElement) {
      var myModal = new bootstrap.Modal(modalElement);
      myModal.show();

      const newUrl = window.location.pathname;
      window.history.replaceState({}, document.title, newUrl);
    }
  }
});
