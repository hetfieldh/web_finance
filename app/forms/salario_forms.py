# app/forms/salario_forms.py

from datetime import date

from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
    ValidationError,
)
from wtforms.validators import (
    DataRequired,
    InputRequired,
    Length,
    NumberRange,
    Optional,
    Regexp,
)

from app.models.salario_item_model import SalarioItem
from app.utils import gerar_opcoes_mes_ano

TIPOS_SALARIO_ITEM = [
    ("", "Selecione..."),
    ("Provento", "Provento"),
    ("Benefício", "Benefício"),
    ("Imposto", "Imposto"),
    ("Desconto", "Desconto"),
]


class CadastroSalarioItemForm(FlaskForm):
    nome = StringField(
        "Verba",
        validators=[
            DataRequired("O nome é obrigatório."),
            Length(min=3, max=100, message="O nome deve ter entre 3 e 100 caracteres."),
            Regexp(
                r"^(?!.*\s\s)[a-zA-ZÀ-ÿ0-9\s'\-]+$",
                message="O nome contém caracteres inválidos ou múltiplos espaços.",
            ),
        ],
    )
    tipo = SelectField(
        "Tipo",
        choices=TIPOS_SALARIO_ITEM,
        validators=[DataRequired("O tipo é obrigatório.")],
    )
    descricao = TextAreaField(
        "Descrição (opcional)",
        validators=[
            Length(max=255, message="A descrição não pode exceder 255 caracteres."),
            Optional(),
        ],
    )
    ativo = BooleanField("Ativo", default=True)
    submit = SubmitField("Adicionar")

    def validate_nome(self, field):
        existing_item = SalarioItem.query.filter_by(
            usuario_id=current_user.id,
            nome=field.data.strip(),
            tipo=self.tipo.data,
        ).first()
        if existing_item:
            raise ValidationError("Já existe uma verba com este nome e tipo.")


class EditarSalarioItemForm(FlaskForm):
    nome = StringField("Verba", render_kw={"readonly": True})
    tipo = SelectField("Tipo", choices=TIPOS_SALARIO_ITEM, render_kw={"disabled": True})

    descricao = TextAreaField(
        "Descrição (opcional)",
        validators=[
            Length(max=255, message="A descrição não pode exceder 255 caracteres."),
            Optional(),
        ],
    )
    ativo = BooleanField("Ativo")
    submit = SubmitField("Atualizar")


class CabecalhoFolhaForm(FlaskForm):
    mes_referencia = SelectField(
        "Mês de Referência",
        validators=[DataRequired("O mês de referência é obrigatório.")],
    )
    data_recebimento = DateField(
        "Data de Recebimento",
        format="%Y-%m-%d",
        validators=[DataRequired("A data de recebimento é obrigatória.")],
        default=date.today,
    )
    submit = SubmitField("Adicionar Verbas")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mes_referencia.choices = gerar_opcoes_mes_ano(
            meses_passados=12, meses_futuros=12
        )


class AdicionarItemFolhaForm(FlaskForm):
    salario_item_id = SelectField(
        "Verba",
        coerce=lambda x: int(x) if x else None,
        validators=[DataRequired("Selecione uma verba.")],
    )
    valor = DecimalField(
        "Valor",
        validators=[
            InputRequired("O valor é obrigatório."),
            NumberRange(min=0.01, message="O valor deve ser maior que zero."),
        ],
        places=2,
    )
    submit = SubmitField("Adicionar")

    def __init__(self, *args, **kwargs):
        salario_item_choices = kwargs.pop("salario_item_choices", [])
        super().__init__(*args, **kwargs)
        self.salario_item_id.choices = salario_item_choices
