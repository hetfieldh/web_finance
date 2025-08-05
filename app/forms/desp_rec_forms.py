# app/forms/desp_rec_forms.py

from datetime import date

# A importação desnecessária de 'salario_movimento_model' foi removida daqui.
import dateutil.relativedelta
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    Form,
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

from app.models.desp_rec_model import DespRec


# --- Formulário para o Cadastro Principal (Molde) ---
class CadastroDespRecForm(FlaskForm):
    nome = StringField(
        "Nome da Despesa/Receita",
        validators=[
            DataRequired("O nome é obrigatório."),
            Length(min=2, max=100, message="O nome deve ter entre 2 e 100 caracteres."),
            Regexp(
                r"^(?!.*\s\s)[a-zA-ZÀ-ÿ0-9\s'\-]+$",
                message="O nome contém caracteres inválidos ou múltiplos espaços.",
            ),
        ],
    )
    natureza = SelectField(
        "Natureza",
        choices=[("", "Selecione..."), ("Despesa", "Despesa"), ("Receita", "Receita")],
        validators=[DataRequired("A natureza é obrigatória.")],
    )
    tipo = SelectField(
        "Tipo",
        choices=[("", "Selecione..."), ("Fixa", "Fixa"), ("Variável", "Variável")],
        validators=[DataRequired("O tipo é obrigatório.")],
    )
    dia_vencimento = IntegerField(
        "Dia Padrão de Vencimento (1-31)",
        validators=[
            Optional(),
            NumberRange(min=1, max=31, message="O dia deve ser entre 1 e 31."),
        ],
    )
    ativo = BooleanField("Ativo", default=True)
    submit = SubmitField("Salvar")

    def __init__(self, original_nome=None, original_tipo=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_nome = original_nome
        self.original_tipo = original_tipo

    def validate_nome(self, field):
        if field.data == self.original_nome and self.tipo.data == self.original_tipo:
            return

        existing = DespRec.query.filter_by(
            usuario_id=current_user.id,
            nome=field.data,
            tipo=self.tipo.data,
            natureza=self.natureza.data,
        ).first()

        if existing:
            raise ValidationError(
                "Já existe um cadastro com este nome, natureza e tipo."
            )


# --- Formulário para Editar um Cadastro Existente ---
class EditarDespRecForm(FlaskForm):
    nome = StringField(
        "Nome da Despesa/Receita",
        render_kw={"readonly": True, "class": "form-control-plaintext"},
    )
    tipo = SelectField(
        "Tipo",
        choices=[("Fixa", "Fixa"), ("Variável", "Variável")],
        render_kw={"disabled": True, "class": "form-select"},
    )
    natureza = SelectField(
        "Natureza",
        choices=[("Despesa", "Despesa"), ("Receita", "Receita")],
        render_kw={"disabled": True, "class": "form-select"},
    )
    dia_vencimento = IntegerField(
        "Dia Padrão de Vencimento (1-31)",
        validators=[
            Optional(),
            NumberRange(min=1, max=31, message="O dia deve ser entre 1 e 31."),
        ],
    )
    ativo = BooleanField("Ativo")
    submit = SubmitField("Salvar Alterações")


# --- Formulário para Gerar Previsões (Lançamento em Lote) ---
class GerarPrevisaoForm(FlaskForm):
    desp_rec_id = SelectField(
        "Conta Fixa",
        validators=[DataRequired("Selecione uma conta fixa.")],
        coerce=int,
    )
    valor_previsto = DecimalField(
        "Valor Previsto Mensal",
        validators=[
            InputRequired("O valor previsto é obrigatório."),
            NumberRange(min=0.01, message="O valor deve ser maior que zero."),
        ],
        places=2,
    )
    data_inicio = DateField(
        "Mês/Ano da Primeira Parcela",
        format="%Y-%m-%d",
        validators=[DataRequired("A data de início é obrigatória.")],
        default=date.today,
    )
    numero_meses = IntegerField(
        "Gerar por Quantos Meses?",
        validators=[
            InputRequired("O número de meses é obrigatório."),
            NumberRange(
                min=1, max=60, message="O número de meses deve ser entre 1 e 60."
            ),
        ],
        default=12,
    )
    descricao = StringField(
        "Descrição (opcional)",
        validators=[
            Optional(),
            Length(max=255, message="A descrição não pode exceder 255 caracteres."),
        ],
    )
    submit = SubmitField("Gerar Previsão")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.desp_rec_id.choices = [
            (c.id, f"{c.nome} ({c.natureza})")
            for c in DespRec.query.filter_by(
                usuario_id=current_user.id, tipo="Fixa", ativo=True
            )
            .order_by(DespRec.nome.asc())
            .all()
        ]


# --- Formulário para Editar um Lançamento Individual ---
class EditarMovimentoForm(FlaskForm):
    data_vencimento = DateField(
        "Data de Vencimento",
        format="%Y-%m-%d",
        validators=[DataRequired("A data de vencimento é obrigatória.")],
    )
    valor_previsto = DecimalField(
        "Valor Previsto",
        validators=[
            InputRequired("O valor previsto é obrigatório."),
            NumberRange(min=0.00),
        ],
        places=2,
    )
    descricao = TextAreaField(
        "Descrição",
        validators=[
            Optional(),
            Length(max=255, message="A descrição não pode exceder 255 caracteres."),
        ],
    )
    submit = SubmitField("Salvar Alterações")


# --- Formulário para Lançamento Único ---
class LancamentoUnicoForm(FlaskForm):
    desp_rec_id = SelectField(
        "Conta",
        validators=[DataRequired("Selecione uma conta.")],
        coerce=lambda x: int(x) if x else None,
    )
    data_vencimento = DateField(
        "Data de Vencimento",
        format="%Y-%m-%d",
        validators=[DataRequired("A data de vencimento é obrigatória.")],
        default=date.today,
    )
    valor_previsto = DecimalField(
        "Valor",
        validators=[
            InputRequired("O valor é obrigatório."),
            NumberRange(min=0.01, message="O valor deve ser maior que zero."),
        ],
        places=2,
    )
    descricao = TextAreaField(
        "Descrição (opcional)",
        validators=[
            Optional(),
            Length(max=255, message="A descrição não pode exceder 255 caracteres."),
        ],
    )
    submit = SubmitField("Adicionar Lançamento")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.desp_rec_id.choices = [("", "Selecione...")] + [
            (c.id, f"{c.nome} ({c.natureza})")
            for c in DespRec.query.filter_by(usuario_id=current_user.id, ativo=True)
            .order_by(DespRec.nome.asc())
            .all()
        ]
