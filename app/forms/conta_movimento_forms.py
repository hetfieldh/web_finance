# app/forms/conta_movimento_forms.py

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    DecimalField,
    SubmitField,
    SelectField,
    DateField,
    TextAreaField,
    BooleanField,
)
from wtforms.validators import (
    DataRequired,
    Length,
    NumberRange,
    Optional,
    InputRequired,
    ValidationError,
)
from app.models.conta_movimento_model import ContaMovimento
from app.models.conta_model import Conta
from app.models.conta_transacao_model import ContaTransacao
from flask_login import current_user
from app import db
from datetime import date


class CadastroContaMovimentoForm(FlaskForm):
    conta_id = SelectField(
        "Conta Bancária (Origem)",
        validators=[DataRequired("A conta bancária é obrigatória.")],
    )

    conta_transacao_id = SelectField(
        "Tipo de Transação",
        validators=[DataRequired("O tipo de transação é obrigatória.")],
    )

    data_movimento = DateField(
        "Data da Movimentação",
        format="%Y-%m-%d",
        validators=[DataRequired("A data da movimentação é obrigatória.")],
        default=date.today(),
    )

    valor = DecimalField(
        "Valor",
        validators=[
            InputRequired("O valor é obrigatório."),
            NumberRange(
                min=0.01,
                max=9999999999.99,
                message="O valor deve ser maior que zero e dentro do limite permitido.",
            ),
        ],
        places=2,
    )

    descricao = TextAreaField(
        "Descrição (opcional)",
        validators=[
            Length(max=255, message="A descrição não pode exceder 255 caracteres."),
            Optional(),
        ],
    )

    is_transferencia = BooleanField("Transferência inter contas?")

    conta_destino_id = SelectField(
        "Conta de Destino",
        validators=[Optional()],
    )

    submit = SubmitField("Adicionar")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conta_id.choices = [("", "Selecione...")] + [
            (c.id, f"{c.nome_banco} - {c.conta} ({c.tipo})")
            for c in Conta.query.filter_by(usuario_id=current_user.id, ativa=True)
            .order_by(Conta.nome_banco.asc())
            .all()
        ]

        self.conta_transacao_id.choices = [("", "Selecione...")] + [
            (ct.id, f"{ct.transacao_tipo} ({ct.tipo})")
            for ct in ContaTransacao.query.filter_by(usuario_id=current_user.id)
            .order_by(ContaTransacao.transacao_tipo.desc())
            .all()
        ]

        self.conta_destino_id.choices = [("", "Selecione...")] + [
            (c.id, f"{c.nome_banco} - {c.conta} ({c.tipo})")
            for c in Conta.query.filter_by(usuario_id=current_user.id, ativa=True)
            .order_by(Conta.nome_banco.asc())
            .all()
        ]

    def validate_is_transferencia(self, field):
        if field.data:
            if not self.conta_destino_id.data:
                raise ValidationError(
                    "A conta de destino é obrigatória para transferências."
                )

            if int(self.conta_id.data) == int(self.conta_destino_id.data):
                raise ValidationError(
                    "A conta de origem e a conta de destino não podem ser a mesma."
                )

            tipo_transacao_selecionado = ContaTransacao.query.get(
                self.conta_transacao_id.data
            )
            if (
                tipo_transacao_selecionado
                and tipo_transacao_selecionado.tipo != "Débito"
            ):
                raise ValidationError(
                    'Para transferências, o tipo de movimento da transação deve ser "Débito".'
                )


class EditarContaMovimentoForm(FlaskForm):
    conta_id = SelectField(
        "Conta Bancária",
        validators=[Optional()],
        render_kw={"disabled": True},
    )

    conta_transacao_id = SelectField(
        "Tipo de Transação",
        validators=[Optional()],
        render_kw={"disabled": True},
    )

    data_movimento = DateField(
        "Data da Movimentação",
        format="%Y-%m-%d",
        validators=[DataRequired("A data da movimentação é obrigatória.")],
        render_kw={"readonly": True},
    )

    valor = DecimalField(
        "Valor",
        validators=[
            InputRequired("O valor é obrigatório."),
            NumberRange(
                min=0.01,
                max=9999999999.99,
                message="O valor deve ser maior que zero e dentro do limite permitido.",
            ),
        ],
        places=2,
        render_kw={"readonly": True},
    )

    descricao = TextAreaField(
        "Descrição (opcional)",
        validators=[
            Length(max=255, message="A descrição não pode exceder 255 caracteres."),
            Optional(),
        ],
    )

    submit = SubmitField("Atualizar")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conta_id.choices = [
            (c.id, f"{c.nome_banco} - {c.conta} ({c.tipo})")
            for c in Conta.query.filter_by(usuario_id=current_user.id).all()
        ]
        self.conta_transacao_id.choices = [
            (ct.id, f"{ct.transacao_tipo} ({ct.tipo})")
            for ct in ContaTransacao.query.filter_by(usuario_id=current_user.id).all()
        ]
