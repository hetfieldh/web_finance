# app/forms/fluxo_caixa_forms.py

from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired

from app.utils import gerar_opcoes_mes_ano


class FluxoCaixaForm(FlaskForm):
    mes_ano = SelectField(
        "Mês/Ano de Referência",
        validators=[DataRequired("O mês e ano são obrigatórios.")],
    )
    submit = SubmitField("Filtrar")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mes_ano.choices = gerar_opcoes_mes_ano(
            meses_passados=12, meses_futuros=12, incluir_selecione=False
        )
