# app/forms/financiamento_forms.py

from datetime import date

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

TIPOS_AMORTIZACAO = [("SAC", "SAC"), ("PRICE", "PRICE"), ("Outro", "Outro")]


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
        "Valor Total Financiado",
        validators=[
            InputRequired("O valor total financiado é obrigatório."),
            NumberRange(min=0.01, message="O valor deve ser maior que zero."),
        ],
        places=2,
    )

    taxa_juros_anual = DecimalField(
        "Taxa de Juros Anual (%)",
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
        default=date.today(),
    )

    prazo_meses = IntegerField(
        "Prazo (em meses)",
        validators=[
            DataRequired("O prazo é obrigatório."),
            NumberRange(min=1, message="O prazo deve ser no mínimo 1 mês."),
        ],
    )

    tipo_amortizacao = SelectField(
        "Tipo de Amortização",
        choices=TIPOS_AMORTIZACAO,
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
        super().__init__(*args, **kwargs)
        self.conta_id.choices = [("", "Selecione...")] + [
            (str(c.id), f"{c.nome_banco} - {c.conta} ({c.tipo})")
            for c in Conta.query.filter_by(usuario_id=current_user.id, ativa=True)
            .order_by(Conta.nome_banco.asc())
            .all()
        ]

    def validate(self, extra_validators=None):
        initial_validation = super().validate(extra_validators)
        if not initial_validation:
            return False

        nome_financiamento_data = self.nome_financiamento.data.strip()

        existing_financiamento = Financiamento.query.filter_by(
            usuario_id=current_user.id, nome_financiamento=nome_financiamento_data
        ).first()

        if existing_financiamento:
            raise ValidationError("Você já possui um financiamento com este nome.")

        return True


class EditarFinanciamentoForm(FlaskForm):
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
        render_kw={"readonly": True},
    )

    conta_id = SelectField(
        "Conta Bancária",
        validators=[Optional()],
        coerce=lambda x: int(x) if x else None,
        render_kw={"disabled": True},
    )

    valor_total_financiado = DecimalField(
        "Valor Total Financiado",
        validators=[Optional()],
        places=2,
        render_kw={"readonly": True},
    )

    taxa_juros_anual = DecimalField(
        "Taxa de Juros Anual (%)",
        validators=[Optional()],
        places=4,
        render_kw={"readonly": True},
    )

    data_inicio = DateField(
        "Data de Início",
        format="%Y-%m-%d",
        validators=[Optional()],
        render_kw={"readonly": True},
    )

    prazo_meses = IntegerField(
        "Prazo (em meses)", validators=[Optional()], render_kw={"readonly": True}
    )

    tipo_amortizacao = SelectField(
        "Tipo de Amortização",
        choices=TIPOS_AMORTIZACAO,
        validators=[Optional()],
        render_kw={"disabled": True},
    )

    descricao = TextAreaField(
        "Descrição",
        validators=[
            Length(max=255, message="A descrição não pode exceder 255 caracteres."),
            Optional(),
        ],
    )

    submit = SubmitField("Atualizar")

    def __init__(self, original_nome_financiamento, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_nome_financiamento = original_nome_financiamento
        self.conta_id.choices = [("", "Selecione...")] + [
            (str(c.id), f"{c.nome_banco} - {c.conta} ({c.tipo})")
            for c in Conta.query.filter_by(usuario_id=current_user.id)
            .order_by(Conta.nome_banco.asc())
            .all()
        ]

    def validate(self, extra_validators=None):
        initial_validation = super().validate(extra_validators)
        if not initial_validation:
            return False

        nome_financiamento_data = self.nome_financiamento.data.strip()

        if nome_financiamento_data != self.original_nome_financiamento:
            existing_financiamento = Financiamento.query.filter_by(
                usuario_id=current_user.id, nome_financiamento=nome_financiamento_data
            ).first()

            if existing_financiamento:
                raise ValidationError(
                    "Você já possui outro financiamento com este nome."
                )

        return True


class ImportarParcelasForm(FlaskForm):
    csv_file = FileField(
        "Arquivo CSV das Parcelas",
        validators=[
            FileRequired("Por favor, selecione um arquivo."),
            FileAllowed(["csv"], "Apenas arquivos .csv são permitidos!"),
        ],
    )
    submit = SubmitField("Importar")
