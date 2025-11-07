# app/forms/fornecedor_forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class CadastroFornecedorForm(FlaskForm):
    nome = StringField(
        "Nome da Loja ou Serviço",
        validators=[
            DataRequired("O nome é obrigatório."),
            Length(min=2, max=100),
        ],
    )
    descricao = TextAreaField(
        "Descrição (Opcional)", validators=[Optional(), Length(max=255)]
    )
    submit = SubmitField("Adicionar")


class EditarFornecedorForm(CadastroFornecedorForm):
    nome = StringField(
        "Nome da Loja ou Serviço",
        validators=[Optional()],
        render_kw={"disabled": True},
    )

    descricao = TextAreaField(
        "Descrição (Opcional)",
        validators=[Optional()],
        render_kw={"disabled": True},
    )

    submit = SubmitField("Atualizar", render_kw={"style": "display: none;"})
