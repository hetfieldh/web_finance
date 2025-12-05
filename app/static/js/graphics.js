// app/static/js/graphics.js

window.addEventListener("load", function () {
  // Pequeno delay apenas para garantir que o layout HTML/CSS finalizou
  setTimeout(initCharts, 100);
});

function initCharts() {
  if (typeof Chart !== "undefined") {
    // CONFIGURAÇÕES GLOBAIS
    Chart.defaults.font.family = "'Inter', 'Segoe UI', sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.color = "#6c757d";

    // --- DESATIVA TODAS AS ANIMAÇÕES ---
    Chart.defaults.animation = false;
    Chart.defaults.animations = false;

    Chart.defaults.responsive = true;
    Chart.defaults.maintainAspectRatio = false;

    // Plugin Texto no Centro
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
          ctx.font = `bold ${centerConfig.fontSize || "16px"} ${centerConfig.fontFamily || "Arial"}`;
          ctx.fillStyle = centerConfig.color || "#495057";
          const text = centerConfig.text;
          const textX = (chartArea.left + chartArea.right) / 2;
          const textY = (chartArea.top + chartArea.bottom) / 2;
          ctx.fillText(text, textX, textY);
          if (centerConfig.subText) {
            ctx.font = `${centerConfig.subFontSize || "9px"} ${centerConfig.subFontFamily || "Arial"}`;
            ctx.fillStyle = centerConfig.subColor || "#6c757d";
            ctx.fillText(centerConfig.subText, textX, textY + 15);
          }
          ctx.restore();
        }
      }
    };
    Chart.register(ChartDataLabels, centerTextPlugin);
  }

  /* --- 1. GRÁFICOS GERAIS (graphics.html) --- */
  const graphicsDataElement = document.getElementById("graphics-data");
  if (graphicsDataElement) {
    const chartData = JSON.parse(graphicsDataElement.textContent);

    // A. Progresso
    const progressoCanvas = document.getElementById("progressoChart");
    if (progressoCanvas && chartData.dados_progresso_valores) {
      const dados = chartData.dados_progresso_valores;
      const totalFormatted = new Intl.NumberFormat("pt-BR").format(dados.total);

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
                "rgba(220, 53, 69, 0.7)"
              ],
              borderColor: ["#ffffff"],
              borderWidth: 2
            }
          ]
        },
        options: {
          cutout: "70%",
          plugins: {
            legend: { display: true, position: "left" },
            centerText: { text: totalFormatted, subText: "Obrigações do Mês" },
            datalabels: { display: false }
          }
        }
      });
    }

    // B. Saídas
    const saidasCanvas = document.getElementById("saidasChart");
    if (saidasCanvas && chartData.dados_saidas) {
      new Chart(saidasCanvas, {
        type: "bar",
        data: {
          labels: chartData.dados_saidas.labels,
          datasets: [
            {
              label: "Valor Gasto ",
              data: chartData.dados_saidas.valores,
              backgroundColor: [
                "rgba(255, 99, 132, 0.5)",
                "rgba(54, 162, 235, 0.5)",
                "rgba(255, 206, 86, 0.5)",
                "rgba(75, 192, 192, 0.5)"
              ],
              borderColor: [
                "rgba(255, 99, 132, 0.6)",
                "rgba(54, 162, 235, 0.6)",
                "rgba(255, 206, 86, 0.6)",
                "rgba(75, 192, 192, 0.6)"
              ],
              borderWidth: 1
            }
          ]
        },
        options: {
          indexAxis: "y",
          scales: { x: { beginAtZero: true, ticks: { display: false } } },
          plugins: {
            legend: { display: false },
            datalabels: {
              anchor: "start",
              align: "end",
              color: "#495057",
              font: { weight: "bold" },
              formatter: (value) => (value === 0 ? "" : new Intl.NumberFormat("pt-BR").format(value))
            }
          }
        }
      });
    }

    // C. Evolução
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
              label: "Balanço ",
              data: dadosEvolucao.balanco,
              borderColor: "rgba(75, 192, 192, 0.8)",
              backgroundColor: "rgba(75, 192, 192, 0.2)",
              fill: true,
              tension: 0.3,
              yAxisID: "yBalan"
            },
            {
              type: "bar",
              label: "Receitas ",
              data: dadosEvolucao.receitas,
              backgroundColor: "rgba(40, 167, 69, 0.5)",
              yAxisID: "yPrincipal"
            },
            {
              type: "bar",
              label: "Despesas ",
              data: dadosEvolucao.despesas,
              backgroundColor: "rgba(220, 53, 69, 0.5)",
              yAxisID: "yPrincipal"
            }
          ]
        },
        options: {
          layout: { padding: { top: 20 } },
          scales: {
            yPrincipal: { beginAtZero: true, position: "left" },
            yBalan: {
              beginAtZero: true,
              position: "right",
              grid: { drawOnChartArea: false }
            }
          },
          plugins: {
            legend: { position: "top" },
            datalabels: { display: false }
          }
        }
      });
    }

    // D. Entradas
    const entradasCanvas = document.getElementById("entradasChart");
    if (entradasCanvas && chartData.dados_entradas) {
      new Chart(entradasCanvas, {
        type: "bar",
        data: {
          labels: chartData.dados_entradas.labels,
          datasets: [
            {
              label: "Valor Recebido ",
              data: chartData.dados_entradas.valores,
              backgroundColor: ["rgba(40, 167, 69, 0.5)", "rgba(23, 162, 184, 0.5)", "rgba(108, 117, 125, 0.5)"],
              borderColor: ["rgba(40, 167, 69, 0.6)", "rgba(23, 162, 184, 0.6)", "rgba(108, 117, 125, 0.6)"],
              borderWidth: 1
            }
          ]
        },
        options: {
          indexAxis: "y",
          scales: { x: { beginAtZero: true, ticks: { display: false } } },
          plugins: {
            legend: { display: false },
            datalabels: {
              anchor: "start",
              align: "end",
              color: "#495057",
              font: { weight: "bold" },
              formatter: (value) => (value === 0 ? "" : new Intl.NumberFormat("pt-BR").format(value))
            }
          }
        }
      });
    }

    // E. Financiamento
    const financiamentoCanvas = document.getElementById("financiamentoProgressChart");
    if (financiamentoCanvas && chartData.progresso_financiamento) {
      const dadosFinanc = chartData.progresso_financiamento;
      new Chart(financiamentoCanvas, {
        type: "bar",
        data: {
          labels: dadosFinanc.labels,
          datasets: [
            {
              label: "Valor Previsto ",
              data: dadosFinanc.previsto,
              backgroundColor: "rgba(255, 159, 64, 0.5)",
              borderColor: "rgba(255, 159, 64, 0.6)",
              borderWidth: 1
            },
            {
              label: "Valor Realizado ",
              data: dadosFinanc.realizado,
              backgroundColor: "rgba(75, 192, 192, 0.5)",
              borderColor: "rgba(75, 192, 192, 0.6)",
              borderWidth: 1
            }
          ]
        },
        options: {
          scales: { y: { beginAtZero: true } },
          plugins: { datalabels: { display: false } }
        }
      });
    }
  }

  /* --- 2. GRÁFICO RESUMO (graphics_2.html) --- */
  const summaryDataElement = document.getElementById("summary-data");
  if (summaryDataElement) {
    const summaryCanvas = document.getElementById("financiamentoSummaryChart");
    if (summaryCanvas) {
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
                  "rgba(220, 53, 69, 0.7)"
                ],
                borderColor: "#fff",
                borderWidth: 2
              }
            ]
          },
          options: {
            plugins: {
              legend: { position: "bottom" },
              title: {
                display: true,
                text: "Distribuição de " + summaryData.total + " Parcelas por Status",
                font: { size: 16, weight: "bold" },
                position: "top"
              },
              datalabels: {
                color: "#fff",
                font: { weight: "bold" },
                formatter: (value, ctx) => {
                  const total = ctx.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                  const percentage = ((value / total) * 100).toFixed(1) + "%";
                  return `${value}\n(${percentage})`;
                }
              }
            }
          }
        });
      }
    }
  }

  /* --- 3. GRÁFICO EVOLUÇÃO (graphics_3.html) --- */
  const chartDataElement = document.getElementById("evolucao-chart-data");
  if (chartDataElement) {
    const chartData = JSON.parse(chartDataElement.textContent);
    const evolucaoParcelasCanvas = document.getElementById("evolucaoParcelasChart");

    if (evolucaoParcelasCanvas && chartData.datasets && chartData.datasets.length > 0) {
      chartData.datasets.forEach((dataset) => {
        const r = Math.floor(Math.random() * 200);
        const g = Math.floor(Math.random() * 200);
        const b = Math.floor(Math.random() * 200);
        dataset.fill = true;
        dataset.backgroundColor = `rgba(${r}, ${g}, ${b}, 0.1)`;
        dataset.borderColor = `rgba(${r}, ${g}, ${b}, 1)`;
        dataset.tension = 0.3;
        dataset.borderWidth = 2;
        dataset.pointRadius = 2;
        dataset.pointHoverRadius = 5;
      });

      new Chart(evolucaoParcelasCanvas, {
        type: "line",
        data: { labels: chartData.labels, datasets: chartData.datasets },
        options: {
          scales: {
            y: {
              beginAtZero: true,
              stacked: true,
              ticks: {
                callback: (value) => new Intl.NumberFormat("pt-BR").format(value)
              }
            },
            x: { grid: { display: false } }
          },
          plugins: {
            legend: { position: "bottom", align: "start" },
            datalabels: { display: false }
          },
          interaction: { mode: "index", intersect: false }
        }
      });
    }
  }

  // Listeners para Selects
  const inputsComAutoSubmit = ["financiamento_id", "grouping_by"];
  inputsComAutoSubmit.forEach((id) => {
    const element = document.getElementById(id);
    if (element) {
      element.addEventListener("change", function () {
        this.closest("form").submit();
      });
    }
  });
}

// Controle de Zoom de Fonte
let currentChartFontSize = 12;
function updateChartFont(delta) {
  let newSize = currentChartFontSize + delta;
  if (newSize < 8) newSize = 8;
  if (newSize > 24) newSize = 24;
  currentChartFontSize = newSize;
  const labelSpan = document.getElementById("current-font-size");
  if (labelSpan) labelSpan.textContent = newSize + "px";

  if (window.Chart) {
    if (window.Chart.defaults) window.Chart.defaults.font.size = newSize;
    if (window.Chart.instances) {
      Object.values(window.Chart.instances).forEach((chart) => {
        if (chart.options.plugins.legend.labels) chart.options.plugins.legend.labels.font = { size: newSize };
        if (chart.options.plugins.tooltip) {
          chart.options.plugins.tooltip.bodyFont = { size: newSize };
          chart.options.plugins.tooltip.titleFont = { size: newSize + 2 };
        }
        if (chart.options.scales) {
          Object.keys(chart.options.scales).forEach((key) => {
            if (chart.options.scales[key].ticks) chart.options.scales[key].ticks.font = { size: newSize };
          });
        }
        chart.update();
      });
    }
  }
}
