# app/forms/crediario_subgrupo_forms.py

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class CadastroCrediarioSubgrupoForm(FlaskForm):
    grupo_id = SelectField(
        "Grupo",
        validators=[DataRequired("O grupo pai é obrigatório.")],
        coerce=lambda x: int(x) if x else None,
    )
    nome = StringField(
        "Nome do Subgrupo",
        validators=[
            DataRequired("O nome é obrigatório."),
            Length(min=2, max=100),
        ],
    )
    submit = SubmitField("Adicionar")

    def __init__(self, *args, **kwargs):
        grupo_choices = kwargs.pop("grupo_choices", [])
        super().__init__(*args, **kwargs)
        self.grupo_id.choices = grupo_choices


class EditarCrediarioSubgrupoForm(CadastroCrediarioSubgrupoForm):
    grupo_id = SelectField(
        "Grupo",
        validators=[Optional()],
        coerce=lambda x: int(x) if x else None,
        render_kw={"disabled": True},
    )

    nome = StringField(
        "Nome do Subgrupo",
        validators=[Optional()],
        render_kw={"disabled": True},
    )

    submit = SubmitField("Atualizar", render_kw={"style": "display: none;"})
