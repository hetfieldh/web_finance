# app/forms/fluxo_caixa_forms.py

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired


class FluxoCaixaForm(FlaskForm):
    mes_ano = StringField(
        "Mês/Ano de Referência",
        validators=[DataRequired("O mês e ano são obrigatórios.")],
        render_kw={
            "readonly": True,
            "style": "background-color: white; cursor: pointer;",
        },
    )
    submit = SubmitField("Filtrar")
