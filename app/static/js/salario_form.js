// app/static/js/salario_form.js

console.log("salario_form.js carregado com sucesso!");

document.addEventListener("DOMContentLoaded", function () {
  const mesReferenciaInput = document.getElementById("mes_referencia");

  // Verifica se o elemento do seletor de mês existe na página atual
  if (!mesReferenciaInput) {
    return;
  }

  // Função para calcular o 5º dia útil do mês seguinte
  function getFifthBusinessDay(year, month) {
    // O mês no JS é 0-11, então o mês seguinte é 'month' (que já virá como 1-12 e subtrairemos 1)
    let date = new Date(year, month, 1); // JS usa 0-11 para meses, então month+1 vira o mês correto
    let businessDays = 0;

    while (businessDays < 5) {
      let dayOfWeek = date.getDay(); // 0=Domingo, 6=Sábado
      if (dayOfWeek !== 0 && dayOfWeek !== 6) {
        businessDays++;
      }
      if (businessDays < 5) {
        date.setDate(date.getDate() + 1);
      }
    }
    return date;
  }

  // Inicializa o Datepicker usando jQuery
  $("#mes_referencia")
    .datepicker({
      format: "mm-yyyy",
      startView: "months",
      minViewMode: "months",
      language: "pt-BR", // Se tiver o locale do datepicker, senão pode remover
      autoclose: true,
    })
    .on("changeDate", function (e) {
      const selectedDate = e.date;
      if (selectedDate) {
        const year = selectedDate.getFullYear();
        const month = selectedDate.getMonth(); // Mês no JS é 0-11

        // Calcula o 5º dia útil do mês seguinte (mês + 1)
        const receiptDate = getFifthBusinessDay(year, month + 1);

        // Formata a data para AAAA-MM-DD
        const receiptYear = receiptDate.getFullYear();
        const receiptMonth = String(receiptDate.getMonth() + 1).padStart(
          2,
          "0"
        );
        const receiptDay = String(receiptDate.getDate()).padStart(2, "0");
        const formattedReceiptDate = `${receiptYear}-${receiptMonth}-${receiptDay}`;

        // Atualiza o valor do campo escondido
        const dataRecebimentoInput =
          document.getElementById("data_recebimento");
        if (dataRecebimentoInput) {
          dataRecebimentoInput.value = formattedReceiptDate;
        }
      }
    });
});
