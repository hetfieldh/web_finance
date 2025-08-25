// app/static/js/graphics.js

document.addEventListener("DOMContentLoaded", function () {
  console.log("graphics.js carregado com sucesso!");

  // --- PLUGIN CUSTOMIZADO PARA TEXTO NO CENTRO ---
  const centerTextPlugin = {
    id: "centerText",
    afterDraw: function (chart) {
      if (chart.config.options.plugins.centerText) {
        const centerConfig = chart.config.options.plugins.centerText;
        const ctx = chart.ctx;
        const chartArea = chart.chartArea;
        ctx.save();
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.font = `bold ${centerConfig.fontSize || "16px"} ${
          centerConfig.fontFamily || "Arial"
        }`;
        ctx.fillStyle = centerConfig.color || "#495057";
        const text = centerConfig.text;
        const textX = (chartArea.left + chartArea.right) / 2;
        const textY = (chartArea.top + chartArea.bottom) / 2;
        ctx.fillText(text, textX, textY);
        if (centerConfig.subText) {
          ctx.font = `${centerConfig.subFontSize || "9px"} ${
            centerConfig.subFontFamily || "Arial"
          }`;
          ctx.fillStyle = centerConfig.subColor || "#6c757d";
          ctx.fillText(centerConfig.subText, textX, textY + 15);
        }
        ctx.restore();
      }
    },
  };
  Chart.register(ChartDataLabels, centerTextPlugin);

  // --- LÓGICA PARA A PÁGINA PRINCIPAL DE GRÁFICOS (graphics.html) ---
  const graphicsDataElement = document.getElementById("graphics-data");
  if (graphicsDataElement) {
    const chartData = JSON.parse(graphicsDataElement.textContent);

    // GRÁFICO 1: Progresso das Obrigações (Rosca)
    const progressoCanvas = document.getElementById("progressoChart");
    if (progressoCanvas && chartData.dados_progresso_valores) {
      const dados = chartData.dados_progresso_valores;
      const totalFormatted = new Intl.NumberFormat("pt-BR", {
        style: "currency",
        currency: "BRL",
      }).format(dados.total);
      new Chart(progressoCanvas, {
        type: "doughnut",
        data: {
          labels: dados.labels,
          datasets: [
            {
              data: dados.valores,
              backgroundColor: [
                "rgba(40, 167, 69, 0.7)",
                "rgba(23, 162, 184, 0.7)",
                "rgba(255, 193, 7, 0.7)",
                "rgba(220, 53, 69, 0.7)",
              ],
              borderColor: ["#ffffff"],
              borderWidth: 2,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: "70%",
          plugins: {
            legend: { display: true, position: "left" },
            centerText: { text: totalFormatted, subText: "Obrigações do Mês" },
            datalabels: { display: false },
          },
        },
      });
    }

    // GRÁFICO 2: Composição das Saídas (Barras Horizontais)
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
                "rgba(255, 99, 132, 0.5)",
                "rgba(54, 162, 235, 0.5)",
                "rgba(255, 206, 86, 0.5)",
                "rgba(75, 192, 192, 0.5)",
              ],
              borderColor: [
                "rgba(255, 99, 132, 0.6)",
                "rgba(54, 162, 235, 0.6)",
                "rgba(255, 206, 86, 0.6)",
                "rgba(75, 192, 192, 0.6)",
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
              font: { weight: "bold" },
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

    // GRÁFICO 3: Evolução Anual (Barras e Linha)
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
              borderColor: "rgba(75, 192, 192, 0.8)",
              backgroundColor: "rgba(75, 192, 192, 0.2)",
              fill: true,
              tension: 0.1,
              yAxisID: "yBalan",
            },
            {
              type: "bar",
              label: "Receitas (R$)",
              data: dadosEvolucao.receitas,
              backgroundColor: "rgba(40, 167, 69, 0.5)",
              yAxisID: "yPrincipal",
            },
            {
              type: "bar",
              label: "Despesas (R$)",
              data: dadosEvolucao.despesas,
              backgroundColor: "rgba(220, 53, 69, 0.5)",
              yAxisID: "yPrincipal",
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          layout: { padding: { top: 20 } },
          scales: {
            yPrincipal: { beginAtZero: true, position: "left" },
            yBalan: {
              beginAtZero: true,
              position: "right",
              grid: { drawOnChartArea: false },
            },
          },
          plugins: {
            legend: { position: "top" },
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
            datalabels: { display: false },
          },
        },
      });
    }

    // GRÁFICO 4: Composição das Entradas (Barras Horizontais)
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
                "rgba(40, 167, 69, 0.5)",
                "rgba(23, 162, 184, 0.5)",
                "rgba(108, 117, 125, 0.5)",
              ],
              borderColor: [
                "rgba(40, 167, 69, 0.6)",
                "rgba(23, 162, 184, 0.6)",
                "rgba(108, 117, 125, 0.6)",
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
          scales: { x: { beginAtZero: true, ticks: { display: false } } },
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
              font: { weight: "bold" },
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

    // GRÁFICO 5: Progresso do Financiamento (Barras)
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
              borderColor: "rgba(255, 159, 64, 0.6)",
              borderWidth: 1,
            },
            {
              label: "Valor Realizado (R$)",
              data: dadosFinanc.realizado,
              backgroundColor: "rgba(75, 192, 192, 0.5)",
              borderColor: "rgba(75, 192, 192, 0.6)",
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: { y: { beginAtZero: true } },
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
            datalabels: { display: false },
          },
        },
      });
    }

    // Lógica do seletor de financiamento para graphics.html
    const selectFinan = document.getElementById("financiamento_id");
    if (selectFinan) {
      selectFinan.addEventListener("change", function () {
        this.form.submit();
      });
    }
  }

  // --- GRÁFICO 6: Pizza para status do financiamento ---
  const summaryCanvas = document.getElementById("financiamentoSummaryChart");
  if (summaryCanvas) {
    const summaryDataElement = document.getElementById("summary-data");
    if (summaryDataElement) {
      const summaryData = JSON.parse(summaryDataElement.textContent);
      if (summaryData && summaryData.labels && summaryData.labels.length > 0) {
        new Chart(summaryCanvas, {
          type: "pie",
          data: {
            labels: summaryData.labels,
            datasets: [
              {
                label: "Quantidade de Parcelas",
                data: summaryData.valores,
                backgroundColor: [
                  "rgba(108, 117, 125, 0.7)",
                  "rgba(40, 167, 69, 0.7)",
                  "rgba(23, 162, 184, 0.7)",
                  "rgba(220, 53, 69, 0.7)",
                ],
                borderColor: "#fff",
                borderWidth: 2,
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: "top" },
              tooltip: {
                callbacks: {
                  label: function (context) {
                    let label = context.dataset.label || "";
                    if (label) {
                      label += ": ";
                    }
                    if (context.parsed !== null) {
                      label += context.parsed;
                    }
                    return label;
                  },
                },
              },
              datalabels: {
                color: "#fff",
                font: { weight: "bold" },
                formatter: (value, ctx) => {
                  const total = ctx.chart.data.datasets[0].data.reduce(
                    (a, b) => a + b,
                    0
                  );
                  const percentage = ((value / total) * 100).toFixed(1) + "%";
                  return `${value}\n(${percentage})`;
                },
              },
            },
          },
        });
      }
    }
  }
});
