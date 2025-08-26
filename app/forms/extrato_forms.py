# app/forms/extrato_forms.py

from datetime import date

from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Optional

from app.models.desp_rec_model import DespRec
from app.utils import gerar_opcoes_mes_ano


class ExtratoBancarioForm(FlaskForm):
    """Formulário para filtrar o extrato bancário por conta e mês/ano."""

    conta_id = SelectField(
        "Conta Bancária",
        validators=[DataRequired("Selecione uma conta.")],
    )
    mes_ano = StringField(
        "Mês/Ano de Referência",
        validators=[DataRequired("O mês e ano são obrigatórios.")],
        render_kw={
            "readonly": True,
            "style": "background-color: white; cursor: pointer;",
        },
    )
    submit = SubmitField("Filtrar")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models.conta_model import Conta

        self.conta_id.choices = [("", "Selecione...")] + [
            (c.id, f"{c.nome_banco} - {c.tipo}")
            for c in Conta.query.filter_by(usuario_id=current_user.id, ativa=True)
            .order_by(Conta.nome_banco.asc())
            .all()
        ]


class ExtratoConsolidadoForm(FlaskForm):
    """Formulário para filtrar o extrato consolidado por mês/ano."""

    mes_ano = StringField(
        "Mês/Ano de Referência",
        validators=[DataRequired("O mês e ano são obrigatórios.")],
        render_kw={
            "readonly": True,
            "style": "background-color: white; cursor: pointer;",
        },
    )
    submit = SubmitField("Filtrar")
