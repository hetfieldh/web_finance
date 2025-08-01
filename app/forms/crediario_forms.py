# app/forms/crediario_forms.py

from flask_login import current_user
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

from app import db
from app.models.crediario_model import Crediario

TIPOS_CREDIARIO = [
    ("Cartão Físico", "Cartão Físico"),
    ("Cartão VR", "Cartão VR"),
    ("Cartão VT", "Cartão VT"),
    ("Boleto", "Boleto"),
    ("Cheque", "Cheque"),
    ("Outro", "Outro"),
]


class CadastroCrediarioForm(FlaskForm):
    nome_crediario = StringField(
        "Nome do Crediário",
        validators=[
            DataRequired("O nome do crediário é obrigatório."),
            Length(
                min=2,
                max=100,
                message="O nome do crediário deve ter entre 2 e 100 caracteres.",
            ),
            Regexp(
                r"^(?!.*\s\s)[a-zA-ZÀ-ÿ\s'\-]+$",
                message="O nome do crediário contém caracteres inválidos ou múltiplos espaços. Use apenas letras, espaços, hífens ou apóstrofos.",
            ),
        ],
    )
    tipo_crediario = SelectField(
        "Tipo de Crediário",
        choices=TIPOS_CREDIARIO,
        validators=[DataRequired("O tipo de crediário é obrigatório.")],
    )
    identificador_final = StringField(
        "Identificador Final (opcional)",
        validators=[
            Length(max=50, message="O identificador não pode exceder 50 caracteres."),
            Optional(),
        ],
    )
    limite_total = DecimalField(
        "Limite Total",
        validators=[
            InputRequired("O limite total é obrigatório."),
            NumberRange(
                min=0.00,
                max=9999999999.99,
                message="Limite total fora do limite permitido.",
            ),
        ],
        places=2,
        default=0.00,
    )
    ativa = BooleanField("Crediário Ativo", default=True)
    submit = SubmitField("Adicionar")

    def validate(self, extra_validators=None):
        initial_validation = super().validate(extra_validators)
        if not initial_validation:
            return False

        nome_crediario_data = self.nome_crediario.data.strip()
        tipo_crediario_data = self.tipo_crediario.data
        identificador_final_data = (
            self.identificador_final.data.strip()
            if self.identificador_final.data
            else None
        )

        existing_crediario = Crediario.query.filter_by(
            usuario_id=current_user.id,
            nome_crediario=nome_crediario_data,
            tipo_crediario=tipo_crediario_data,
            identificador_final=identificador_final_data,
        ).first()

        if existing_crediario:
            raise ValidationError(
                "Você já possui um crediário com este nome, tipo e identificador final."
            )

        return True


class EditarCrediarioForm(FlaskForm):
    nome_crediario = StringField(
        "Nome do Crediário",
        validators=[
            DataRequired("O nome do crediário é obrigatório."),
            Length(
                min=2,
                max=100,
                message="O nome do crediário deve ter entre 2 e 100 caracteres.",
            ),
            Regexp(
                r"^(?!.*\s\s)[a-zA-ZÀ-ÿ\s'\-]+$",
                message="O nome do crediário contém caracteres inválidos ou múltiplos espaços. Use apenas letras, espaços, hífens ou apóstrofos.",
            ),
        ],
        render_kw={"readonly": True},
    )
    tipo_crediario = SelectField(
        "Tipo de Crediário",
        choices=TIPOS_CREDIARIO,
        validators=[Optional()],
        render_kw={"disabled": True},
    )
    identificador_final = StringField(
        "Identificador Final (opcional)",
        validators=[
            Length(max=50, message="O identificador não pode exceder 50 caracteres."),
            Optional(),
        ],
        render_kw={"readonly": True},
    )
    limite_total = DecimalField(
        "Limite Total",
        validators=[
            InputRequired("O limite total é obrigatório."),
            NumberRange(
                min=0.00,
                max=9999999999.99,
                message="Limite total fora do limite permitido.",
            ),
        ],
        places=2,
    )
    ativa = BooleanField("Crediário Ativo")
    submit = SubmitField("Atualizar")

    def __init__(
        self,
        original_nome_crediario,
        original_tipo_crediario,
        original_identificador_final,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.original_nome_crediario = original_nome_crediario
        self.original_tipo_crediario = original_tipo_crediario
        self.original_identificador_final = original_identificador_final

    def validate(self, extra_validators=None):
        initial_validation = super().validate(extra_validators)
        if not initial_validation:
            return False

        nome_crediario_data = self.nome_crediario.data.strip()
        tipo_crediario_data = self.tipo_crediario.data
        identificador_final_data = (
            self.identificador_final.data.strip()
            if self.identificador_final.data
            else None
        )

        if (
            nome_crediario_data != self.original_nome_crediario.strip()
            or tipo_crediario_data != self.original_tipo_crediario
            or identificador_final_data
            != (
                self.original_identificador_final.strip().upper()
                if self.original_identificador_final
                else None
            )
        ):

            existing_crediario = Crediario.query.filter_by(
                usuario_id=current_user.id,
                nome_crediario=nome_crediario_data,
                tipo_crediario=tipo_crediario_data,
                identificador_final=identificador_final_data,
            ).first()

            if existing_crediario and (
                existing_crediario.nome_crediario
                != self.original_nome_crediario.strip()
                or existing_crediario.tipo_crediario != self.original_tipo_crediario
                or existing_crediario.identificador_final
                != (
                    self.original_identificador_final.strip().upper()
                    if self.original_identificador_final
                    else None
                )
            ):
                raise ValidationError(
                    "Você já possui outro crediário com este nome, tipo e identificador final."
                )

        return True
