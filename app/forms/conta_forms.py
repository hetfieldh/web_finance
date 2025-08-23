# app/forms/conta_forms.py

from flask_wtf import FlaskForm
from wtforms import BooleanField, DecimalField, SelectField, StringField, SubmitField
from wtforms.validators import (
    DataRequired,
    InputRequired,
    Length,
    NumberRange,
    Optional,
    Regexp,
    ValidationError,
)

from app.models.conta_model import Conta

TIPOS_CONTA = [
    ("", "Selecione..."),
    ("Corrente", "Corrente"),
    ("Poupança", "Poupança"),
    ("Digital", "Digital"),
    ("Investimento", "Investimento"),
    ("Caixinha", "Caixinha"),
    ("Dinheiro", "Dinheiro"),
    ("Benefício", "Benefício"),
    ("FGTS", "FGTS"),
]


class CadastroContaForm(FlaskForm):
    nome_banco = StringField(
        "Nome do Banco",
        validators=[
            DataRequired("O nome do banco é obrigatório."),
            Length(
                min=3,
                max=100,
                message="O nome do banco deve ter entre 3 e 100 caracteres.",
            ),
            Regexp(
                r"^(?!.*\s\s)[a-zA-ZÀ-ÿ\s'\-]+$",
                message="O nome do banco contém caracteres inválidos ou múltiplos espaços. Use apenas letras, espaços, hífens ou apóstrofos.",
            ),
        ],
    )
    agencia = StringField(
        "Agência",
        validators=[
            DataRequired("A agência é obrigatória."),
            Length(min=4, max=4, message="A agência deve ter exatamente 4 números."),
            Regexp(r"^[0-9]+$", message="A agência deve conter apenas números."),
        ],
    )
    conta = StringField(
        "Número da Conta",
        validators=[
            DataRequired("O número da conta é obrigatório."),
            Length(
                min=6, max=50, message="O número da conta deve ter no mínimo 6 números."
            ),
            Regexp(
                r"^[0-9]+$", message="O número da conta deve conter apenas números."
            ),
        ],
    )
    tipo = SelectField(
        "Tipo de Conta",
        choices=TIPOS_CONTA,
        validators=[DataRequired("O tipo de conta é obrigatório.")],
    )
    saldo_inicial = DecimalField(
        "Saldo Inicial",
        validators=[
            InputRequired("O saldo inicial é obrigatório."),
            NumberRange(
                min=0.00,
                max=9999999999.99,
                message="Saldo inicial fora do limite permitido.",
            ),
        ],
        places=2,
        default=0.00,
    )
    limite = DecimalField(
        "Limite (opcional)",
        validators=[
            Optional(),
            NumberRange(
                min=0.00, max=9999999999.99, message="Limite fora do limite permitido."
            ),
        ],
        places=2,
        default=0.00,
    )
    ativa = BooleanField("Conta Ativa", default=True)
    submit = SubmitField("Adicionar")

    def validate_limite(self, field):
        tipos_com_limite = ["Corrente", "Digital"]

        if self.tipo.data not in tipos_com_limite:
            if field.data is not None and field.data > 0:
                raise ValidationError(
                    f'Contas do tipo "{self.tipo.data}" não podem ter limite maior que zero.'
                )


class EditarContaForm(FlaskForm):
    nome_banco = StringField(
        "Nome do Banco",
        validators=[Optional()],
        render_kw={"readonly": True},
    )
    agencia = StringField(
        "Agência",
        validators=[Optional()],
        render_kw={"readonly": True},
    )
    conta = StringField(
        "Número da Conta",
        validators=[Optional()],
        render_kw={"readonly": True},
    )
    tipo = SelectField(
        "Tipo de Conta",
        choices=TIPOS_CONTA,
        validators=[Optional()],
        render_kw={"disabled": True},
    )
    saldo_inicial = DecimalField(
        "Saldo Inicial",
        validators=[Optional()],
        places=2,
        render_kw={"readonly": True},
    )

    limite = DecimalField(
        "Limite (opcional)",
        validators=[
            Optional(),
            NumberRange(
                min=0.00, max=9999999999.99, message="Limite fora do limite permitido."
            ),
        ],
        places=2,
    )
    ativa = BooleanField("Conta Ativa")
    submit = SubmitField("Atualizar")

    def __init__(
        self,
        original_nome_banco,
        original_agencia,
        original_conta,
        original_tipo,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.original_nome_banco = original_nome_banco
        self.original_agencia = original_agencia
        self.original_conta = original_conta
        self.original_tipo = original_tipo

    def validate_limite(self, field):
        tipos_com_limite = ["Corrente", "Digital"]
        tipo_da_conta = self.tipo.data if self.tipo.data else self.original_tipo

        if tipo_da_conta not in tipos_com_limite:
            if field.data is not None and field.data > 0:
                raise ValidationError(
                    f'Contas do tipo "{tipo_da_conta}" não podem ter limite maior que zero.'
                )
