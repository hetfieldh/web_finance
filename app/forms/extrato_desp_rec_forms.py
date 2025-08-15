# app/forms/extrato_desp_rec_forms.py

from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, SubmitField
from wtforms.validators import Optional

from app.models.desp_rec_model import DespRec
from app.utils import gerar_opcoes_mes_ano


class ExtratoDespRecForm(FlaskForm):
    tipo_relatorio = SelectField(
        "Tipo de Relatório",
        choices=[("mensal", "Visão Mensal"), ("periodo", "Análise por Período")],
        default="mensal",
    )

    mes_ano = SelectField("Mês/Ano", validators=[Optional()])

    desp_rec_id = SelectField(
        "Conta Específica",
        validators=[Optional()],
        coerce=lambda x: int(x) if x else None,
    )
    data_inicio = DateField(
        "Data de Início", format="%Y-%m-%d", validators=[Optional()]
    )
    data_fim = DateField("Data de Fim", format="%Y-%m-%d", validators=[Optional()])

    submit = SubmitField("Filtrar")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mes_ano.choices = gerar_opcoes_mes_ano(
            meses_passados=12, meses_futuros=12, incluir_selecione=False
        )

        self.desp_rec_id.choices = [("", "Todas")] + [
            (c.id, f"{c.nome} ({c.natureza})")
            for c in DespRec.query.filter_by(usuario_id=current_user.id, ativo=True)
            .order_by(DespRec.nome.asc())
            .all()
        ]
