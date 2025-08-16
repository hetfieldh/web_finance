// app/static/js/graphics.js

document.addEventListener("DOMContentLoaded", function () {
  console.log("graphics.js carregado com sucesso!");

  // NÃO registraremos o plugin globalmente. Faremos isso por gráfico.
  // Chart.register(ChartDataLabels);

  const dataElement = document.getElementById("graphics-data");
  if (!dataElement) {
    console.error(
      "O contêiner de dados do gráfico (#graphics-data) não foi encontrado."
    );
    return;
  }

  const chartData = JSON.parse(dataElement.textContent);

  // --- GRÁFICO 1: Progresso das Obrigações ---
  const progressoCanvas = document.getElementById("progressoChart");
  if (progressoCanvas && chartData.dados_progresso) {
    new Chart(progressoCanvas, {
      type: "doughnut",
      data: {
        labels: ["Concluídas", "Pendentes"],
        datasets: [
          {
            label: "Obrigações",
            data: [
              chartData.dados_progresso.concluidas,
              chartData.dados_progresso.pendentes,
            ],
            backgroundColor: [
              "rgba(40, 167, 69, 0.8)",
              "rgba(220, 53, 69, 0.8)",
            ],
            borderColor: ["#ffffff"],
            borderWidth: 2,
          },
        ],
      },
      // <-- ALTERAÇÃO: Adiciona o plugin localmente
      plugins: [ChartDataLabels],
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "60%",
        plugins: {
          legend: {
            position: "bottom",
          },
          title: {
            display: true,
            text: `${chartData.dados_progresso.percentual}% Concluído (${chartData.dados_progresso.concluidas}/${chartData.dados_progresso.concluidas + chartData.dados_progresso.pendentes})`,
            font: {
              size: 14,
            },
          },
          datalabels: {
            anchor: "end",
            align: "end",
            offset: 8,
            color: "#6c757d",
            font: {
              weight: "bold",
              size: 11,
            },
            formatter: (value, ctx) => {
              const total = ctx.chart.data.datasets[0].data.reduce(
                (a, b) => a + b,
                0
              );
              const percentage = ((value / total) * 100).toFixed(0) + "%";
              return percentage;
            },
          },
        },
      },
    });
  }

  // --- GRÁFICO 2: Composição das Saídas ---
  const saidasCanvas = document.getElementById("saidasChart");
  if (saidasCanvas && chartData.dados_saidas) {
    new Chart(saidasCanvas, {
      type: "bar",
      data: {
        labels: chartData.dados_saidas.labels,
        datasets: [
          {
            label: "Valor Gasto (R$)",
            data: chartData.dados_saidas.valores,
            backgroundColor: [
              "rgba(255, 99, 132, 0.7)",
              "rgba(54, 162, 235, 0.7)",
              "rgba(255, 206, 86, 0.7)",
              "rgba(75, 192, 192, 0.7)",
            ],
            borderColor: [
              "rgba(255, 99, 132, 1)",
              "rgba(54, 162, 235, 1)",
              "rgba(255, 206, 86, 1)",
              "rgba(75, 192, 192, 1)",
            ],
            borderWidth: 1,
          },
        ],
      },
      // <-- ALTERAÇÃO: Registra o plugin apenas para este gráfico
      plugins: [ChartDataLabels],
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { beginAtZero: true, ticks: { display: false } },
          y: { beginAtZero: true },
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (context) {
                let label = context.dataset.label || "";
                if (label) {
                  label += ": ";
                }
                if (context.parsed.x !== null) {
                  label += new Intl.NumberFormat("pt-BR", {
                    style: "currency",
                    currency: "BRL",
                  }).format(context.parsed.x);
                }
                return label;
              },
            },
          },
          datalabels: {
            anchor: "start",
            align: "end",
            color: "#495057",
            font: {
              weight: "bold",
            },
            formatter: function (value, context) {
              if (value === 0) return "";
              return new Intl.NumberFormat("pt-BR", {
                style: "currency",
                currency: "BRL",
              }).format(value);
            },
          },
        },
      },
    });
  }

  // --- GRÁFICO 3: Evolução Anual ---
  const evolucaoCanvas = document.getElementById("evolucaoAnualChart");
  if (evolucaoCanvas && chartData.evolucao_anual) {
    const dadosEvolucao = chartData.evolucao_anual;
    new Chart(evolucaoCanvas, {
      type: "bar",
      data: {
        labels: dadosEvolucao.labels,
        datasets: [
          {
            type: "line",
            label: "Balanço (R$)",
            data: dadosEvolucao.balanco,
            borderColor: "rgba(75, 192, 192, 1)",
            backgroundColor: "rgba(75, 192, 192, 0.2)",
            fill: true,
            tension: 0.1,
            yAxisID: "yBalan",
          },
          {
            type: "bar",
            label: "Receitas (R$)",
            data: dadosEvolucao.receitas,
            backgroundColor: "rgba(40, 167, 69, 0.7)",
            yAxisID: "yPrincipal",
          },
          {
            type: "bar",
            label: "Despesas (R$)",
            data: dadosEvolucao.despesas,
            backgroundColor: "rgba(220, 53, 69, 0.7)",
            yAxisID: "yPrincipal",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          yPrincipal: {
            beginAtZero: true,
            position: "left",
          },
          yBalan: {
            beginAtZero: true,
            position: "right",
            grid: {
              drawOnChartArea: false,
            },
          },
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: function (context) {
                let label = context.dataset.label || "";
                if (label) {
                  label += ": ";
                }
                if (context.parsed.y !== null) {
                  label += new Intl.NumberFormat("pt-BR", {
                    style: "currency",
                    currency: "BRL",
                  }).format(context.parsed.y);
                }
                return label;
              },
            },
          },
        },
      },
    });
  }

  // --- GRÁFICO 4: Composição das Entradas ---
  const entradasCanvas = document.getElementById("entradasChart");
  if (entradasCanvas && chartData.dados_entradas) {
    new Chart(entradasCanvas, {
      type: "bar",
      data: {
        labels: chartData.dados_entradas.labels,
        datasets: [
          {
            label: "Valor Recebido (R$)",
            data: chartData.dados_entradas.valores,
            backgroundColor: [
              "rgba(40, 167, 69, 0.7)",
              "rgba(23, 162, 184, 0.7)",
              "rgba(108, 117, 125, 0.7)",
            ],
            borderColor: [
              "rgba(40, 167, 69, 1)",
              "rgba(23, 162, 184, 1)",
              "rgba(108, 117, 125, 1)",
            ],
            borderWidth: 1,
          },
        ],
      },
      plugins: [ChartDataLabels],
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { beginAtZero: true, ticks: { display: false } },
          y: { beginAtZero: true },
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (context) {
                let label = context.dataset.label || "";
                if (label) {
                  label += ": ";
                }
                if (context.parsed.x !== null) {
                  label += new Intl.NumberFormat("pt-BR", {
                    style: "currency",
                    currency: "BRL",
                  }).format(context.parsed.x);
                }
                return label;
              },
            },
          },
          datalabels: {
            anchor: "start",
            align: "end",
            color: "#495057",
            font: {
              weight: "bold",
            },
            formatter: function (value, context) {
              if (value === 0) return "";
              return new Intl.NumberFormat("pt-BR", {
                style: "currency",
                currency: "BRL",
              }).format(value);
            },
          },
        },
      },
    });
  }

  // --- GRÁFICO 5: Progresso do Financiamento ---
  const financiamentoCanvas = document.getElementById(
    "financiamentoProgressChart"
  );
  if (financiamentoCanvas && chartData.progresso_financiamento) {
    const dadosFinanc = chartData.progresso_financiamento;
    new Chart(financiamentoCanvas, {
      type: "bar",
      data: {
        labels: dadosFinanc.labels,
        datasets: [
          {
            label: "Valor Previsto (R$)",
            data: dadosFinanc.previsto,
            backgroundColor: "rgba(255, 159, 64, 0.5)",
            borderColor: "rgba(255, 159, 64, 1)",
            borderWidth: 1,
          },
          {
            label: "Valor Realizado (R$)",
            data: dadosFinanc.realizado,
            backgroundColor: "rgba(75, 192, 192, 0.5)",
            borderColor: "rgba(75, 192, 192, 1)",
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
          },
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: function (context) {
                let label = context.dataset.label || "";
                if (label) {
                  label += ": ";
                }
                if (context.parsed.y !== null) {
                  label += new Intl.NumberFormat("pt-BR", {
                    style: "currency",
                    currency: "BRL",
                  }).format(context.parsed.y);
                }
                return label;
              },
            },
          },
        },
      },
    });
  }
});
