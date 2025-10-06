# app/forms/pagamentos_forms.py

from datetime import date

from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    DecimalField,
    HiddenField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, InputRequired, NumberRange

from app.models.conta_model import Conta


class PainelPagamentosForm(FlaskForm):
    mes_ano = StringField(
        "Mês/Ano de Referência",
        validators=[DataRequired("O mês e ano são obrigatórios.")],
        render_kw={
            "readonly": True,
            "style": "background-color: white; cursor: pointer;",
        },
    )
    submit = SubmitField("Filtrar")


class PagamentoForm(FlaskForm):
    conta_id = SelectField(
        "Selecione a conta para pagamento",
        coerce=lambda x: int(x) if x else None,
        validators=[DataRequired("Selecione a conta para o pagamento.")],
    )
    data_pagamento = DateField(
        "Data do Pagamento",
        format="%Y-%m-%d",
        validators=[DataRequired("A data do pagamento é obrigatória.")],
        default=date.today,
    )
    valor_pago = DecimalField(
        "Valor a Pagar",
        places=2,
        validators=[
            InputRequired("O valor é obrigatório."),
            NumberRange(min=0.01, message="O valor pago deve ser maior que zero."),
        ],
    )
    item_id = HiddenField()
    item_tipo = HiddenField()
    item_descricao = HiddenField()

    submit = SubmitField("Confirmar Pagamento")

    def __init__(self, *args, **kwargs):
        account_choices = kwargs.pop("account_choices", [])
        super().__init__(*args, **kwargs)
        self.conta_id.choices = account_choices
