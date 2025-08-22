# app/forms/extrato_forms.py

from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired

from app.models.conta_model import Conta
from app.utils import gerar_opcoes_mes_ano


class ExtratoBancarioForm(FlaskForm):
    conta_id = SelectField(
        "Conta Bancária",
        validators=[DataRequired("A conta bancária é obrigatória.")],
    )
    mes_ano = SelectField(
        "Mês/Ano", validators=[DataRequired("O mês e ano são obrigatórios.")]
    )
    submit = SubmitField("Filtrar")

    def __init__(self, *args, **kwargs):
        account_choices = kwargs.pop("account_choices", [])
        super().__init__(*args, **kwargs)
        self.conta_id.choices = account_choices
        self.mes_ano.choices = gerar_opcoes_mes_ano(meses_passados=11, meses_futuros=0)
