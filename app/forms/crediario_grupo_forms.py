# app/forms/crediario_grupo_forms.py

from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, Regexp, ValidationError

from app import db
from app.models.crediario_grupo_model import CrediarioGrupo

TIPOS_GRUPO_CREDIARIO = [
    ("", "Selecione..."),
    ("Compra", "Compra"),
    ("Estorno", "Estorno"),
    ("Ajuste", "Ajuste"),
]


class CadastroCrediarioGrupoForm(FlaskForm):
    grupo_crediario = StringField(
        "Grupo",
        validators=[
            DataRequired("O nome do grupo é obrigatório."),
            Length(
                min=3,
                max=100,
                message="O nome do grupo deve ter entre 3 e 100 caracteres.",
            ),
            Regexp(
                r"^(?!.*\s\s)[a-zA-ZÀ-ÿ\s'\-]+$",
                message="O nome do grupo contém caracteres inválidos ou múltiplos espaços. Use apenas letras, espaços, hífens ou apóstrofos.",
            ),
        ],
    )
    tipo_grupo_crediario = SelectField(
        "Tipo",
        choices=TIPOS_GRUPO_CREDIARIO,
        validators=[DataRequired("O tipo de grupo é obrigatório.")],
    )
    descricao = TextAreaField(
        "Descrição (opcional)",
        validators=[
            Length(max=255, message="A descrição não pode exceder 255 caracteres."),
            Optional(),
        ],
    )
    submit = SubmitField("Adicionar")

    def validate(self, extra_validators=None):
        initial_validation = super().validate(extra_validators)
        if not initial_validation:
            return False

        grupo_crediario_data = self.grupo_crediario.data.strip()
        tipo_grupo_crediario_data = self.tipo_grupo_crediario.data

        existing_grupo = CrediarioGrupo.query.filter_by(
            usuario_id=current_user.id,
            grupo_crediario=grupo_crediario_data,
            tipo_grupo_crediario=tipo_grupo_crediario_data,
        ).first()

        if existing_grupo:
            raise ValidationError("Você já possui um grupo com este nome e tipo.")

        return True


class EditarCrediarioGrupoForm(FlaskForm):
    grupo_crediario = StringField(
        "Grupo",
        validators=[
            DataRequired("O nome do grupo é obrigatório."),
            Length(
                min=3,
                max=100,
                message="O nome do grupo deve ter entre 3 e 100 caracteres.",
            ),
            Regexp(
                r"^(?!.*\s\s)[a-zA-ZÀ-ÿ\s'\-]+$",
                message="O nome do grupo contém caracteres inválidos ou múltiplos espaços. Use apenas letras, espaços, hífens ou apóstrofos.",
            ),
        ],
        render_kw={"readonly": True},
    )
    tipo_grupo_crediario = SelectField(
        "Tipo",
        choices=TIPOS_GRUPO_CREDIARIO,
        validators=[Optional()],
        render_kw={"disabled": True},
    )
    descricao = TextAreaField(
        "Descrição (opcional)",
        validators=[
            Length(max=255, message="A descrição não pode exceder 255 caracteres."),
            Optional(),
        ],
    )
    submit = SubmitField("Atualizar")

    def __init__(
        self, original_grupo_crediario, original_tipo_grupo_crediario, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.original_grupo_crediario = original_grupo_crediario
        self.original_tipo_grupo_crediario = original_tipo_grupo_crediario

    def validate(self, extra_validators=None):
        initial_validation = super().validate(extra_validators)
        if not initial_validation:
            return False

        grupo_crediario_data = self.grupo_crediario.data.strip()
        tipo_grupo_crediario_data = self.tipo_grupo_crediario.data

        if (
            grupo_crediario_data != self.original_grupo_crediario.strip()
            or tipo_grupo_crediario_data != self.original_tipo_grupo_crediario
        ):

            existing_grupo = CrediarioGrupo.query.filter_by(
                usuario_id=current_user.id,
                grupo_crediario=grupo_crediario_data,
                tipo_grupo_crediario=tipo_grupo_crediario_data,
            ).first()

            if existing_grupo and (
                existing_grupo.grupo_crediario != self.original_grupo_crediario.strip()
                or existing_grupo.tipo_grupo_crediario
                != self.original_tipo_grupo_crediario
            ):
                raise ValidationError(
                    "Você já possui outro grupo com este nome e tipo."
                )

        return True
