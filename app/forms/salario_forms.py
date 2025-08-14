# app/forms/salario_forms.py

from datetime import date

from dateutil.relativedelta import relativedelta
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    Form,
    FormField,
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
        for i in range(-12, 13):
            data_ref = hoje + relativedelta(months=i)
            value = data_ref.strftime("%Y-%m")
            label = f"{nomes_meses_ptbr[data_ref.month]}/{data_ref.year}"
            meses_anos.append((value, label))

        self.mes_referencia.choices = [("", "Selecione...")] + sorted(
            meses_anos, key=lambda x: x[0], reverse=True
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
    submit = SubmitField("")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.salario_item_id.choices = [("", "Selecione...")] + [
            (item.id, f"{item.nome} ({item.tipo})")
            for item in SalarioItem.query.filter_by(
                usuario_id=current_user.id, ativo=True
            )
            .order_by(SalarioItem.tipo, SalarioItem.nome)
            .all()
        ]
