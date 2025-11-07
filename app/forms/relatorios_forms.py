# app/forms/relatorios_forms.py

from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField


class ResumoAnualForm(FlaskForm):
    ano = SelectField("Ano", coerce=int)
    submit = SubmitField("Buscar")

class GastosCrediarioForm(FlaskForm):
    ano = SelectField("Ano", coerce=int)
    visualizacao = SelectField(
        "Visualizar Gastos por",
        choices=[
            ("grupo", "Grupo"),
            ("subgrupo", "Subgrupo"),
            ("fornecedor", "Loja/Serviço"),
        ],
        default="grupo",
    )
    submit = SubmitField("Filtrar")
