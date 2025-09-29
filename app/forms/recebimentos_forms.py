# app/forms/recebimentos_forms.py

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


class PainelRecebimentosForm(FlaskForm):
    mes_ano = StringField(
        "Mês/Ano de Referência",
        validators=[DataRequired("O mês e ano são obrigatórios.")],
        render_kw={
            "readonly": True,
            "style": "background-color: white; cursor: pointer;",
        },
    )
    submit = SubmitField("Filtrar")


class RecebimentoForm(FlaskForm):
    conta_id = SelectField(
        "Selecione a conta para recebimento",
        coerce=lambda x: int(x) if x else None,
        validators=[DataRequired("Selecione a conta para o recebimento.")],
    )
    data_recebimento = DateField(
        "Data do Recebimento",
        format="%Y-%m-%d",
        validators=[DataRequired("A data do recebimento é obrigatória.")],
        default=date.today,
    )
    valor_recebido = DecimalField(
        "Valor a Receber",
        places=2,
        render_kw={
            'readonly': True,
            'style': 'color: var(--wf-texto-positivo); font-weight: bold; background-color: var(--wf-box-positivo);'
        },
        validators=[
            InputRequired("O valor é obrigatório."),
            NumberRange(min=0.01, message="O valor recebido deve ser maior que zero."),
        ],
    )
    item_id = HiddenField()
    item_tipo = HiddenField()
    item_descricao = HiddenField()

    submit = SubmitField("Confirmar Recebimento")

    def __init__(self, *args, **kwargs):
        account_choices = kwargs.pop("account_choices", [])
        super().__init__(*args, **kwargs)
        self.conta_id.choices = account_choices
