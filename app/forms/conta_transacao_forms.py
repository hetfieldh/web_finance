# app/forms/conta_transacao_forms.py

from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Optional, Regexp

from app import db
from app.models.conta_transacao_model import ContaTransacao
from app.utils import TIPO_CORRENTE, TIPO_DIGITAL, FormChoices


class CadastroContaTransacaoForm(FlaskForm):
    transacao_tipo = StringField(
        "Tipo de Transação",
        validators=[
            DataRequired("O tipo de transação é obrigatório."),
            Length(
                min=3,
                max=100,
                message="O tipo de transação deve ter entre 3 e 100 caracteres.",
            ),
            Regexp(
                r"^(?!.*\s\s)[a-zA-ZÀ-ÿ\s'\-]+$",
                message="O tipo de transação contém caracteres inválidos ou múltiplos espaços. Use apenas letras, espaços, hífens ou apóstrofos.",
            ),
        ],
    )
    tipo = SelectField(
        "Tipo de Movimento",
        choices=FormChoices.get_choices(FormChoices.TipoTransacao),
        validators=[DataRequired("O tipo de movimento é obrigatório.")],
    )
    submit = SubmitField("Adicionar")

    def validate_transacao_tipo(self, field):
        existing_transacao_tipo = ContaTransacao.query.filter_by(
            usuario_id=current_user.id,
            transacao_tipo=field.data.strip().upper(),
            tipo=self.tipo.data,
        ).first()

        if existing_transacao_tipo:
            raise ValidationError(
                "Você já possui um tipo de transação com este nome e tipo de movimento."
            )

    def validate(self, extra_validators=None):
        return super().validate(extra_validators)

    def validate_limite(self, field):
        tipos_com_limite = [TIPO_CORRENTE, TIPO_DIGITAL]

        if self.tipo.data not in tipos_com_limite:
            if field.data is not None and field.data > 0:
                raise ValidationError(
                    f'Contas do tipo "{self.tipo.data}" não podem ter limite maior que zero.'
                )


class EditarContaTransacaoForm(FlaskForm):
    transacao_tipo = StringField(
        "Tipo de Transação",
        validators=[
            DataRequired("O tipo de transação é obrigatório."),
            Length(
                min=3,
                max=100,
                message="O tipo de transação deve ter entre 3 e 100 caracteres.",
            ),
            Regexp(
                r"^(?!.*\s\s)[a-zA-ZÀ-ÿ\s'\-]+$",
                message="O tipo de transação contém caracteres inválidos ou múltiplos espaços. Use apenas letras, espaços, hífens ou apóstrofos.",
            ),
        ],
        render_kw={"readonly": True},
    )
    tipo = SelectField(
        "Tipo de Movimento",
        choices=FormChoices.get_choices(FormChoices.TipoTransacao),
        validators=[Optional()],
        render_kw={"disabled": True},
    )
    submit = SubmitField("Atualizar")

    def __init__(self, original_transacao_tipo, original_tipo, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_transacao_tipo = original_transacao_tipo
        self.original_tipo = original_tipo

    def validate(self, extra_validators=None):
        initial_validation = super().validate(extra_validators)
        if not initial_validation:
            return False

        if (
            self.transacao_tipo.data.strip().upper()
            != self.original_transacao_tipo.strip().upper()
            or self.tipo.data != self.original_tipo
        ):

            existing_transacao_tipo = ContaTransacao.query.filter(
                ContaTransacao.usuario_id == current_user.id,
                ContaTransacao.transacao_tipo
                == self.transacao_tipo.data.strip().upper(),
                ContaTransacao.tipo == self.tipo.data,
            ).first()

            if existing_transacao_tipo and (
                existing_transacao_tipo.transacao_tipo
                != self.original_transacao_tipo.strip().upper()
                or existing_transacao_tipo.tipo != self.original_tipo
            ):
                raise ValidationError(
                    "Você já possui outro tipo de transação com este nome e tipo de movimento."
                )

        return True

    def validate_limite(self, field):
        tipos_com_limite = [TIPO_CORRENTE, TIPO_DIGITAL]

        tipo_da_conta = self.tipo.data if self.tipo.data else self.original_tipo

        if tipo_da_conta not in tipos_com_limite:
            if field.data is not None and field.data > 0:
                raise ValidationError(
                    f'Contas do tipo "{tipo_da_conta}" não podem ter limite maior que zero.'
                )
