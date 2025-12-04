# app/forms/financiamento_forms.py

from datetime import date
from decimal import Decimal

from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (
    DateField,
    DecimalField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    InputRequired,
    Length,
    NumberRange,
    Optional,
    Regexp,
    ValidationError,
)

from app import db
from app.models.conta_model import Conta
from app.models.financiamento_model import Financiamento
from app.utils import FormChoices


class CadastroFinanciamentoForm(FlaskForm):
    nome_financiamento = StringField(
        "Nome do Financiamento",
        validators=[
            DataRequired("O nome do financiamento é obrigatório."),
            Length(min=3, max=100, message="O nome deve ter entre 3 e 100 caracteres."),
            Regexp(
                r"^(?!.*\s\s)[a-zA-ZÀ-ÿ0-9\s'\-]+$",
                message="O nome contém caracteres inválidos ou múltiplos espaços.",
            ),
        ],
    )
    conta_id = SelectField(
        "Conta Bancária",
        validators=[DataRequired("A conta bancária é obrigatória.")],
        coerce=lambda x: int(x) if x else None,
    )

    valor_total_financiado = DecimalField(
        "Valor Total",
        validators=[
            InputRequired("O valor total financiado é obrigatório."),
            NumberRange(min=Decimal("0.01"), message="O valor deve ser maior que zero."),
        ],
        places=2,
    )

    taxa_juros_anual = DecimalField(
        "% Juros Anual",
        validators=[
            InputRequired("A taxa de juros é obrigatória."),
            NumberRange(
                min=0.0001,
                max=100.00,
                message="A taxa de juros deve estar entre 0.0001% e 100%.",
            ),
        ],
        places=4,
    )

    data_inicio = DateField(
        "Data de Início",
        format="%Y-%m-%d",
        validators=[DataRequired("A data de início é obrigatória.")],
        default=date.today,
    )

    prazo_meses = IntegerField(
        "Prazo (em meses)",
        validators=[
            DataRequired("O prazo é obrigatório."),
            NumberRange(min=1, message="O prazo deve ser no mínimo 1 mês."),
        ],
    )

    tipo_amortizacao = SelectField(
        "Amortização",
        choices=FormChoices.get_choices(FormChoices.TipoAmortizacao),
        validators=[DataRequired("O tipo de amortização é obrigatório.")],
    )

    descricao = TextAreaField(
        "Descrição (opcional)",
        validators=[
            Length(max=255, message="A descrição não pode exceder 255 caracteres."),
            Optional(),
        ],
    )

    submit = SubmitField("Adicionar")

    def __init__(self, *args, **kwargs):
        account_choices = kwargs.pop("account_choices", [])
        super().__init__(*args, **kwargs)
        self.conta_id.choices = account_choices

    def validate(self, extra_validators=None):
        initial_validation = super().validate(extra_validators)
        if not initial_validation:
            return False

        nome_financiamento_data = self.nome_financiamento.data.strip()

        existing_financiamento = Financiamento.query.filter_by(
            usuario_id=current_user.id, nome_financiamento=nome_financiamento_data
        ).first()

        if existing_financiamento:
            self.nome_financiamento.errors.append(
                "Você já possui um financiamento com este nome."
            )
            return False
        return True


class EditarFinanciamentoForm(FlaskForm):
    nome_financiamento = StringField(
        "Nome do Financiamento",
        validators=[DataRequired()],
        render_kw={"readonly": True},
    )
    valor_total_financiado = DecimalField(
        "Valor Total Financiado", validators=[Optional()], render_kw={"readonly": True}
    )
    taxa_juros_anual = DecimalField(
        "Taxa de Juros Anual (%)", validators=[Optional()], render_kw={"readonly": True}
    )
    data_inicio = DateField(
        "Data de Início", validators=[Optional()], render_kw={"readonly": True}
    )
    prazo_meses = IntegerField(
        "Prazo (em meses)", validators=[Optional()], render_kw={"readonly": True}
    )
    tipo_amortizacao = SelectField(
        "Tipo de Amortização",
        choices=FormChoices.get_choices(FormChoices.TipoAmortizacao),
        validators=[Optional()],
        render_kw={"disabled": True},
    )

    conta_id = SelectField(
        "Conta Bancária Associada",
        coerce=lambda x: int(x) if x is not None and x != "" else None,
        validators=[DataRequired("Por favor, selecione uma conta.")],
        render_kw={"disabled": True},
    )
    descricao = TextAreaField(
        "Descrição (opcional)",
        validators=[
            Optional(),
            Length(max=255, message="A descrição não pode exceder 255 caracteres."),
        ],
    )
    submit = SubmitField("Atualizar")

    def __init__(self, *args, **kwargs):
        self.original_nome_financiamento = kwargs.pop(
            "original_nome_financiamento", None
        )
        account_choices = kwargs.pop("account_choices", [])

        super(EditarFinanciamentoForm, self).__init__(*args, **kwargs)

        self.conta_id.choices = account_choices


class ImportarParcelasForm(FlaskForm):
    csv_file = FileField(
        "Arquivo CSV das Parcelas",
        validators=[
            FileRequired("Por favor, selecione um arquivo."),
            FileAllowed(["csv"], "Apenas arquivos .csv são permitidos!"),
        ],
    )
    submit = SubmitField("Importar")


class AmortizacaoForm(FlaskForm):
    valor_amortizacao = DecimalField(
        "Valor Total",
        places=2,
        validators=[
            InputRequired("O valor é obrigatório."),
            NumberRange(min=Decimal("0.01"), message="O valor deve ser maior que zero."),
        ],
    )
    conta_id = SelectField(
        "Conta para débito",
        coerce=lambda x: int(x) if x is not None and x != "" else None,
        validators=[DataRequired("Selecione a conta para o débito.")],
    )
    data_pagamento = DateField(
        "Data do Pagamento",
        format="%Y-%m-%d",
        validators=[DataRequired("A data do pagamento é obrigatória.")],
        default=date.today,
    )
    estrategia = SelectField(
        "Selecione uma estratégia",
        choices=[
            ("prazo", "1. Reduzir o prazo (quitar as últimas parcelas)"),
            ("parcela", "2. Reduzir o valor das próximas parcelas"),
        ],
        default="prazo",
        validators=[DataRequired("Selecione...")],
    )
    submit = SubmitField("Amortizar")

    def __init__(self, *args, **kwargs):
        account_choices_with_balance = kwargs.pop("account_choices_with_balance", [])
        super().__init__(*args, **kwargs)
        self.conta_id.choices = account_choices_with_balance
