# app/forms/fluxo_caixa_forms.py

from datetime import date

from dateutil.relativedelta import relativedelta
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired


class FluxoCaixaForm(FlaskForm):
    mes_ano = SelectField(
        "Mês/Ano de Referência",
        validators=[DataRequired("O mês e ano são obrigatórios.")],
    )
    submit = SubmitField("")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        meses_anos = []
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

        for i in range(-12, 13):
            data_ref = hoje + relativedelta(months=i)
            value = data_ref.strftime("%Y-%m")
            label = f"{nomes_meses_ptbr[data_ref.month]}/{data_ref.year}"
            meses_anos.append((value, label))

        self.mes_ano.choices = sorted(meses_anos, key=lambda x: x[0], reverse=True)
