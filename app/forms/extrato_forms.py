# app/forms/extrato_forms.py

from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired
from app.models.conta_model import Conta
from flask_login import current_user
from datetime import datetime, date


class ExtratoBancarioForm(FlaskForm):
    conta_id = SelectField(
        "Conta Bancária",
        validators=[DataRequired("A conta bancária é obrigatória.")],
    )

    mes_ano = SelectField(
        "Mês/Ano", validators=[DataRequired("O mês e ano são obrigatórios.")]
    )

    submit = SubmitField("Gerar Extrato")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.conta_id.choices = [("", "Selecione...")] + [
            (c.id, f"{c.nome_banco} - {c.conta} ({c.tipo})")
            for c in Conta.query.filter_by(usuario_id=current_user.id, ativa=True)
            .order_by(Conta.nome_banco)
            .all()
        ]

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

        for i in range(12):
            mes = hoje.month - i
            ano = hoje.year
            while mes <= 0:
                mes += 12
                ano -= 1

            mes_formatado = f"{mes:02d}"

            value = f"{ano}-{mes_formatado}"
            label = f"{nomes_meses_ptbr[mes]}/{ano}"

            meses_anos.append((value, label))

        self.mes_ano.choices = [("", "Selecione um período...")] + sorted(
            meses_anos, key=lambda x: x[0], reverse=True
        )
