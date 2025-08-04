# app/forms/extrato_desp_rec_forms.py

from datetime import date

from dateutil.relativedelta import relativedelta
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, SubmitField
from wtforms.validators import Optional

from app.models.desp_rec_model import DespRec


class ExtratoDespRecForm(FlaskForm):
    tipo_relatorio = SelectField(
        "Tipo de Relatório",
        choices=[("mensal", "Visão Mensal"), ("periodo", "Análise por Período")],
        default="mensal",
    )

    # Filtros para Visão Mensal
    mes_ano = SelectField("Mês/Ano", validators=[Optional()])

    # Filtros para Análise por Período
    desp_rec_id = SelectField(
        "Conta Específica",
        validators=[Optional()],
        # CORREÇÃO: Lida com o valor vazio da opção "Todas"
        coerce=lambda x: int(x) if x else None,
    )
    data_inicio = DateField(
        "Data de Início", format="%Y-%m-%d", validators=[Optional()]
    )
    data_fim = DateField("Data de Fim", format="%Y-%m-%d", validators=[Optional()])

    submit = SubmitField("Filtrar")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Popula o dropdown de Mês/Ano (últimos 12 meses + próximos 12)
        meses_anos = []
        hoje = date.today()
        nomes_meses_ptbr = {
            1: "Janeiro",
            2: "Fevereiro",
            3: "Março",
            4: "Abril",
            5: "Maio",
            6: "Junho",
            7: "Julho",
            8: "Agosto",
            9: "Setembro",
            10: "Outubro",
            11: "Novembro",
            12: "Dezembro",
        }
        for i in range(-12, 13):
            data_ref = hoje + relativedelta(months=i)
            value = data_ref.strftime("%Y-%m")
            label = f"{nomes_meses_ptbr[data_ref.month]}/{data_ref.year}"
            meses_anos.append((value, label))

        # Ordena pela data, do mais recente para o mais antigo
        self.mes_ano.choices = sorted(meses_anos, key=lambda x: x[0], reverse=True)

        # Popula o dropdown de Contas
        self.desp_rec_id.choices = [("", "Todas")] + [
            (c.id, f"{c.nome} ({c.natureza})")
            for c in DespRec.query.filter_by(usuario_id=current_user.id, ativo=True)
            .order_by(DespRec.nome.asc())
            .all()
        ]
