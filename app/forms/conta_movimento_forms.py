# app/forms/conta_movimento_forms.py

from datetime import date

from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    HiddenField,
    RadioField,
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
from app.utils import (
    TIPO_DEBITO,
    TIPO_MOVIMENTACAO_SIMPLES,
    TIPO_MOVIMENTACAO_TRANSFERENCIA,
    TIPO_PIX,
    TIPO_TRANSFERENCIA,
    FormChoices,
)


class CadastroContaMovimentoForm(FlaskForm):
    tipo_operacao = RadioField(
        "Tipo de Operação",
        choices=[
            (FormChoices.TiposMovimentacaoBancaria.SIMPLES.value, "Tradicional"),
            (
                FormChoices.TiposMovimentacaoBancaria.TRANSFERENCIA.value,
                "Transferência Inter Contas",
            ),
        ],
        default=FormChoices.TiposMovimentacaoBancaria.SIMPLES.value,
        validators=[DataRequired()],
    )

    conta_id = SelectField(
        "Conta Bancária",
        validators=[DataRequired("A conta é obrigatória.")],
        coerce=lambda x: int(x) if x else None,
    )
    data_movimento = DateField(
        "Data",
        format="%Y-%m-%d",
        validators=[DataRequired("A data é obrigatória.")],
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

    conta_transacao_id = SelectField(
        "Tipo de Transação",
        validators=[Optional()],
        coerce=lambda x: int(x) if x else None,
    )

    conta_destino_id = SelectField(
        "Conta Destino",
        validators=[Optional()],
        coerce=lambda x: int(x) if x else None,
    )
    transferencia_tipo_id = SelectField(
        "Tipo de Transferência",
        validators=[Optional()],
        coerce=lambda x: int(x) if x else None,
    )

    submit = SubmitField("Adicionar")

    def __init__(self, *args, **kwargs):
        account_choices = kwargs.pop("account_choices", [])
        transaction_choices = kwargs.pop("transaction_choices", [])
        transfer_choices = kwargs.pop("transfer_choices", [])

        super().__init__(*args, **kwargs)

        self.conta_id.choices = account_choices
        self.conta_destino_id.choices = account_choices
        self.conta_transacao_id.choices = transaction_choices
        self.transferencia_tipo_id.choices = transfer_choices
        self.conta_destino_id.choices = self.conta_id.choices

        self.conta_transacao_id.choices = [("", "Selecione...")] + [
            (ct.id, f"{ct.transacao_tipo} ({'+' if ct.tipo == 'Crédito' else '-'})")
            for ct in ContaTransacao.query.filter_by(usuario_id=current_user.id)
            .order_by(ContaTransacao.transacao_tipo.asc())
            .order_by(ContaTransacao.tipo.desc())
            .all()
        ]

# --- INÍCIO DA MODIFICAÇÃO ---
        # Filtra a lista de tipos de transferência para incluir apenas "PIX" e "TRANSFERÊNCIA"

        tipos_desejados = [TIPO_PIX, TIPO_TRANSFERENCIA]

        query_transferencia = ContaTransacao.query.filter(
            ContaTransacao.usuario_id == current_user.id,
            ContaTransacao.tipo == TIPO_DEBITO,
            ContaTransacao.transacao_tipo.in_(tipos_desejados)
        ).order_by(ContaTransacao.transacao_tipo.asc())

        self.transferencia_tipo_id.choices = [("", "Selecione...")] + [
            (ct.id, f"{ct.transacao_tipo}")
            for ct in query_transferencia.all()
        ]

        # --- FIM DA MODIFICAÇÃO ---

        # self.transferencia_tipo_id.choices = [("", "Selecione...")] + [
        #     (ct.id, f"{ct.transacao_tipo}")
        #     for ct in ContaTransacao.query.filter_by(
        #         usuario_id=current_user.id, tipo=TIPO_DEBITO
        #     )
        #     .order_by(ContaTransacao.transacao_tipo.asc())
        #     .all()
        # ]

    def validate(self, extra_validators=None):
        initial_validation = super().validate(extra_validators)
        if not initial_validation:
            return False

        if self.tipo_operacao.data == TIPO_MOVIMENTACAO_SIMPLES:
            if not self.conta_transacao_id.data:
                self.conta_transacao_id.errors.append(
                    "O tipo de transação é obrigatório."
                )
                return False

        elif self.tipo_operacao.data == TIPO_MOVIMENTACAO_TRANSFERENCIA:
            if not self.conta_destino_id.data:
                self.conta_destino_id.errors.append("A conta de destino é obrigatória.")
                return False
            if not self.transferencia_tipo_id.data:
                self.transferencia_tipo_id.errors.append(
                    "O tipo de transferência é obrigatório."
                )
                return False
            if self.conta_id.data == self.conta_destino_id.data:
                self.conta_destino_id.errors.append(
                    "A conta de destino não pode ser a mesma que a de origem."
                )
                return False

        return True


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
        "Data",
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
        "Descrição (opcional)",
        validators=[
            Length(max=255, message="A descrição não pode exceder 255 caracteres."),
            Optional(),
        ],
    )
    submit = SubmitField("Atualizar")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conta_id.choices = [("", "Selecione...")] + [
            (str(c.id), f"{c.nome_banco} - {c.conta} ({c.tipo})")
            for c in Conta.query.filter_by(usuario_id=current_user.id)
            .order_by(Conta.nome_banco.asc())
            .all()
        ]
        self.conta_transacao_id.choices = [("", "Selecione...")] + [
            (ct.id, f"{ct.transacao_tipo} ({'+' if ct.tipo == 'Crédito' else '-'})")
            for ct in ContaTransacao.query.filter_by(usuario_id=current_user.id)
            .order_by(ContaTransacao.transacao_tipo.asc())
            .all()
        ]
