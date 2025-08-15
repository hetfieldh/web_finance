# app/forms/crediario_fatura_forms.py 

from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    DecimalField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import (
    DataRequired,
    InputRequired,
    NumberRange,
    Optional,
    ValidationError,
)

from app.models.crediario_model import Crediario
from app.utils import gerar_opcoes_mes_ano

STATUS_FATURA = [
    ("Aberta", "Aberta"),
    ("Fechada", "Fechada"),
    ("Paga", "Paga"),
    ("Atrasada", "Atrasada"),
    ("Parcialmente Paga", "Parcialmente Paga"),
]


class GerarFaturaForm(FlaskForm):
    crediario_id = SelectField(
        "Crediário",
        validators=[DataRequired("O crediário é obrigatório.")],
        coerce=lambda x: int(x) if x else None,
    )

    mes_ano = SelectField(
        "Mês/Ano de Referência",
        validators=[DataRequired("O mês e ano são obrigatórios.")],
    )

    submit = SubmitField("Gerar Fatura")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.crediario_id.choices = [("", "Selecione...")] + [
            (str(c.id), f"{c.nome_crediario} ({c.tipo_crediario})")
            for c in Crediario.query.filter_by(usuario_id=current_user.id, ativa=True)
            .order_by(Crediario.nome_crediario.asc())
            .all()
        ]

        self.mes_ano.choices = gerar_opcoes_mes_ano(meses_passados=11, meses_futuros=1)


class EditarFaturaForm(FlaskForm):
    crediario_id = SelectField(
        "Crediário",
        validators=[Optional()],
        coerce=lambda x: int(x) if x else None,
        render_kw={"disabled": True},
    )

    mes_referencia = StringField(
        "Mês/Ano de Referência",
        validators=[DataRequired("O mês/ano é obrigatório.")],
        render_kw={"readonly": True},
    )

    valor_total_fatura = DecimalField(
        "Valor Total da Fatura",
        validators=[
            InputRequired("O valor total é obrigatório."),
            NumberRange(min=0.00),
        ],
        places=2,
        render_kw={"readonly": True},
    )

    valor_pago_fatura = DecimalField(
        "Valor Pago",
        validators=[
            InputRequired("O valor pago é obrigatório."),
            NumberRange(min=0.00),
        ],
        places=2,
        render_kw={"readonly": True},
    )

    data_fechamento = DateField(
        "Data de Fechamento",
        format="%Y-%m-%d",
        validators=[Optional()],
        render_kw={"readonly": True},
    )

    data_vencimento_fatura = DateField(
        "Data de Vencimento",
        format="%Y-%m-%d",
        validators=[DataRequired("O data de vencimento é obrigatória.")],
        render_kw={"readonly": True},
    )

    status = SelectField(
        "Status da Fatura",
        choices=STATUS_FATURA,
        validators=[DataRequired("O status é obrigatório.")],
    )

    data_pagamento = DateField(
        "Data de Pagamento", format="%Y-%m-%d", validators=[Optional()]
    )

    submit = SubmitField("Atualizar Fatura")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crediario_id.choices = [("", "Selecione...")] + [
            (str(c.id), f"{c.nome_crediario} ({c.tipo_crediario})")
            for c in Crediario.query.filter_by(usuario_id=current_user.id).all()
        ]

    def validate_status(self, field):
        if field.data == "Paga" and not self.data_pagamento.data:
            raise ValidationError(
                'A data de pagamento é obrigatória se o status for "Paga".'
            )
        if field.data != "Paga" and self.data_pagamento.data:
            self.data_pagamento.data = None
