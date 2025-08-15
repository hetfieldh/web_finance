# app/utils.py

from datetime import date

from dateutil.relativedelta import relativedelta


def gerar_opcoes_mes_ano(meses_passados=12, meses_futuros=12, incluir_selecione=True):
    hoje = date.today()
    nomes_meses_ptbr = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro",
    }

    opcoes = []
    # Gera meses desde o passado até o futuro
    for i in range(-meses_passados, meses_futuros + 1):
        data_ref = hoje + relativedelta(months=i)
        value = data_ref.strftime("%Y-%m")
        label = f"{nomes_meses_ptbr[data_ref.month]}/{data_ref.year}"
        opcoes.append((value, label))

    # Ordena as opções em ordem decrescente (mais recente primeiro)
    opcoes_ordenadas = sorted(opcoes, key=lambda x: x[0], reverse=True)

    if incluir_selecione:
        return [("", "Selecione um período...")] + opcoes_ordenadas

    return opcoes_ordenadas
