# app/forms/conta_movimento_forms.py

from datetime import date

from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
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
    ValidationError,
)

from app import db
from app.models.conta_model import Conta
from app.models.conta_movimento_model import ContaMovimento
from app.models.conta_transacao_model import ContaTransacao


class CadastroContaMovimentoForm(FlaskForm):
    conta_id = SelectField(
        "Conta Bancária (Origem)",
        validators=[DataRequired("A conta bancária é obrigatória.")],
        coerce=lambda x: int(x) if x else None,
    )

    conta_transacao_id = SelectField(
        "Tipo de Transação",
        validators=[DataRequired("O tipo de transação é obrigatória.")],
        coerce=lambda x: int(x) if x else None,
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
            NumberRange(min=0.01, message="O valor deve ser maior que zero."),
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

    is_transferencia = BooleanField("Transferência entre contas?")

    conta_destino_id = SelectField(
        "Conta de Destino",
        validators=[Optional()],
        coerce=lambda x: int(x) if x else None,
    )

    submit = SubmitField("Registrar Movimentação")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conta_id.choices = [("", "Selecione...")] + [
            (str(c.id), f"{c.nome_banco} - {c.conta} ({c.tipo})")
            for c in Conta.query.filter_by(usuario_id=current_user.id, ativa=True)
            .order_by(Conta.nome_banco.asc())
            .all()
        ]
        self.conta_transacao_id.choices = [("", "Selecione...")] + [
            (str(ct.id), f"{ct.transacao_tipo} ({ct.tipo})")
            for ct in ContaTransacao.query.filter_by(usuario_id=current_user.id)
            .order_by(ContaTransacao.transacao_tipo.asc())
            .all()
        ]

        self.conta_destino_id.choices = [("", "Selecione...")] + [
            (str(c.id), f"{c.nome_banco} - {c.conta} ({c.tipo})")
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

            if self.conta_id.data == self.conta_destino_id.data:
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
        coerce=lambda x: int(x) if x else None,
        render_kw={"disabled": True},
    )

    conta_transacao_id = SelectField(
        "Tipo de Transação",
        validators=[Optional()],
        coerce=lambda x: int(x) if x else None,
        render_kw={"disabled": True},
    )

    data_movimento = DateField(
        "Data da Movimentação",
        format="%Y-%m-%d",
        validators=[Optional()],
        render_kw={"readonly": True},
    )

    valor = DecimalField(
        "Valor",
        validators=[Optional()],
        places=2,
        render_kw={"readonly": True},
    )

    descricao = TextAreaField(
        "Descrição",
        validators=[
            DataRequired("A descrição é obrigatória."),
            Length(max=255, message="A descrição não pode exceder 255 caracteres."),
        ],
    )

    submit = SubmitField("Atualizar Movimentação")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conta_id.choices = [("", "Selecione...")] + [
            (str(c.id), f"{c.nome_banco} - {c.conta} ({c.tipo})")
            for c in Conta.query.filter_by(usuario_id=current_user.id)
            .order_by(Conta.nome_banco.asc())
            .all()
        ]
        self.conta_transacao_id.choices = [("", "Selecione...")] + [
            (str(ct.id), f"{ct.transacao_tipo} ({ct.tipo})")
            for ct in ContaTransacao.query.filter_by(usuario_id=current_user.id)
            .order_by(ContaTransacao.transacao_tipo.asc())
            .all()
        ]
