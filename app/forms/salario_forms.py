# app/forms/salario_forms.py

from datetime import date, datetime
from decimal import Decimal

from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    HiddenField,
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
from app.utils import FormChoices


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
        choices=FormChoices.get_choices(FormChoices.TipoSalarioItem),
        validators=[DataRequired("O tipo é obrigatório.")],
    )
    conta_destino_id = SelectField(
        "Conta de Destino (para Benefícios)",
        coerce=lambda x: int(x) if x else None,
        validators=[Optional()],
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
    tipo = StringField("Tipo", render_kw={"readonly": True})
    conta_destino_id = SelectField(
        "Conta de Destino (para Benefícios)",
        coerce=lambda x: int(x) if x else None,
        validators=[Optional()],
    )
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
    _choices_raw = FormChoices.get_choices(FormChoices.TipoFolha)
    _choices_clean = [c for c in _choices_raw if c[0]]

    tipo = SelectField(
        "Tipo de Folha",
        choices=[("", "Selecione...")] + _choices_clean,
        validators=[DataRequired("Selecione o tipo de folha.")],
    )

    mes_referencia = StringField(
        "Mês de Referência",
        validators=[DataRequired("O mês de referência é obrigatório.")],
        render_kw={"placeholder": "Selecione...", "autocomplete": "off"},
    )

    data_recebimento = StringField(
        "Data de Recebimento",
        validators=[Optional()],
        render_kw={"placeholder": "dd/mm/aaaa", "autocomplete": "off"},
    )

    submit = SubmitField("Criar Folha")

    def validate_data_recebimento(self, field):
        if self.tipo.data != "Mensal" and self.tipo.data != "":
            if not field.data:
                raise ValidationError(
                    "A data de recebimento é obrigatória para este tipo de folha."
                )

            try:
                datetime.strptime(field.data, "%d/%m/%Y")
            except ValueError:
                raise ValidationError("Data inválida. Use o formato dd/mm/aaaa.")


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
           NumberRange(min=Decimal("0.01"), message="O valor deve ser maior que zero."),
        ],
        places=2,
    )
    submit = SubmitField("Adicionar")

    def __init__(self, *args, **kwargs):
        salario_item_choices = kwargs.pop("salario_item_choices", [])
        super().__init__(*args, **kwargs)
        self.salario_item_id.choices = salario_item_choices
