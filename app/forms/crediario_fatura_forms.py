# app/forms/crediario_fatura_forms.py

from datetime import date

from dateutil.relativedelta import relativedelta
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import (
    DataRequired,
    InputRequired,
    Length,
    NumberRange,
    Optional,
    ValidationError,
)

from app.models.crediario_fatura_model import CrediarioFatura
from app.models.crediario_model import Crediario

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

        inicio = hoje + relativedelta(months=1)

        for i in range(12):
            data_ref = inicio - relativedelta(months=i)
            mes = data_ref.month
            ano = data_ref.year
            value = f"{ano}-{mes:02d}"
            label = f"{nomes_meses_ptbr[mes]}/{ano}"
            meses_anos.append((value, label))

        self.mes_ano.choices = [("", "Selecione um período...")] + meses_anos


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
