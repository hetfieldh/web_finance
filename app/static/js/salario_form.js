// app/static/js/salario_form.js

console.log("salario_form.js carregado com sucesso!");

document.addEventListener("DOMContentLoaded", function () {
  const mesReferenciaInput = document.getElementById("mes_referencia");

  if (!mesReferenciaInput) {
    return;
  }

  function getFifthBusinessDay(year, month) {
    let date = new Date(year, month, 1);
    let businessDays = 0;

    while (businessDays < 5) {
      let dayOfWeek = date.getDay();
      if (dayOfWeek !== 0 && dayOfWeek !== 6) {
        businessDays++;
      }
      if (businessDays < 5) {
        date.setDate(date.getDate() + 1);
      }
    }
    return date;
  }

  $("#mes_referencia")
    .datepicker({
      format: "mm-yyyy",
      startView: "months",
      minViewMode: "months",
      language: "pt-BR",
      autoclose: true,
    })
    .on("changeDate", function (e) {
      const selectedDate = e.date;
      if (selectedDate) {
        const year = selectedDate.getFullYear();
        const month = selectedDate.getMonth();

        const receiptDate = getFifthBusinessDay(year, month + 1);

        const receiptYear = receiptDate.getFullYear();
        const receiptMonth = String(receiptDate.getMonth() + 1).padStart(
          2,
          "0"
        );
        const receiptDay = String(receiptDate.getDate()).padStart(2, "0");
        const formattedReceiptDate = `${receiptYear}-${receiptMonth}-${receiptDay}`;

        const dataRecebimentoInput =
          document.getElementById("data_recebimento");
        if (dataRecebimentoInput) {
          dataRecebimentoInput.value = formattedReceiptDate;
        }
      }
    });
});
