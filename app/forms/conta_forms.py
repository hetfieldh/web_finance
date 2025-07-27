# app/forms/conta_forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, BooleanField, SubmitField, SelectField
from wtforms.validators import (
    DataRequired,
    Length,
    NumberRange,
    ValidationError,
    Optional,
    InputRequired,
    Regexp,
)
from app.models.conta_model import Conta
from app.models.usuario_model import Usuario
from flask_login import current_user
from app import db

TIPOS_CONTA = [
    ("Corrente", "Corrente"),
    ("Poupança", "Poupança"),
    ("Digital", "Digital"),
    ("Investimento", "Investimento"),
    ("Caixinha", "Caixinha"),
    ("Dinheiro", "Dinheiro"),
]


class CadastroContaForm(FlaskForm):
    nome_banco = StringField(
        "Nome do Banco",
        validators=[
            DataRequired("O nome do banco é obrigatório."),
            Length(
                min=2,
                max=100,
                message="O nome do banco deve ter entre 2 e 100 caracteres.",
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

    def validate(self, extra_validators=None):
        initial_validation = super().validate(extra_validators)
        if not initial_validation:
            return False

        existing_account = Conta.query.filter_by(
            usuario_id=current_user.id,
            nome_banco=self.nome_banco.data.strip().upper(),
            agencia=self.agencia.data.strip(),
            conta=self.conta.data.strip(),
        ).first()

        if existing_account:
            raise ValidationError(
                "Você já possui uma conta com este banco, agência e número de conta."
            )

        return True

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
        validators=[
            DataRequired("O nome do banco é obrigatório."),
            Length(
                min=2,
                max=100,
                message="O nome do banco deve ter entre 2 e 100 caracteres.",
            ),
            Regexp(
                r"^(?!.*\s\s)[a-zA-ZÀ-ÿ\s'\-]+$",
                message="O nome do banco contém caracteres inválidos ou múltiplos espaços. Use apenas letras, espaços, hífens ou apóstrofos.",
            ),
        ],
        render_kw={"readonly": True},
    )
    agencia = StringField(
        "Agência",
        validators=[
            DataRequired("A agência é obrigatória."),
            Length(min=4, max=4, message="A agência deve ter exatamente 4 números."),
            Regexp(r"^[0-9]+$", message="A agência deve conter apenas números."),
        ],
        render_kw={"readonly": True},
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
        validators=[
            InputRequired("O saldo inicial é obrigatório."),
            NumberRange(
                min=0.00,
                max=9999999999.99,
                message="Saldo inicial fora do limite permitido.",
            ),
        ],
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

    def validate(self, extra_validators=None):
        initial_validation = super().validate(extra_validators)
        if not initial_validation:
            return False

        if (
            self.nome_banco.data.strip().upper()
            != self.original_nome_banco.strip().upper()
            or self.agencia.data.strip() != self.original_agencia.strip()
            or self.conta.data.strip() != self.original_conta.strip()
        ):

            existing_account = Conta.query.filter(
                Conta.usuario_id == current_user.id,
                Conta.nome_banco == self.nome_banco.data.strip().upper(),
                Conta.agencia == self.agencia.data.strip(),
                Conta.conta == self.conta.data.strip(),
            ).first()

            if existing_account and (
                existing_account.nome_banco != self.original_nome_banco.strip().upper()
                or existing_account.agencia != self.original_agencia.strip()
                or existing_account.conta != self.original_conta.strip()
            ):
                raise ValidationError(
                    "Você já possui outra conta com este banco, agência e número de conta."
                )

        return True

    def validate_limite(self, field):
        tipos_com_limite = ["Corrente", "Digital"]

        tipo_da_conta = self.tipo.data if self.tipo.data else self.original_tipo

        if tipo_da_conta not in tipos_com_limite:
            if field.data is not None and field.data > 0:
                raise ValidationError(
                    f'Contas do tipo "{tipo_da_conta}" não podem ter limite maior que zero.'
                )
