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
        coerce=int,
    )

    mes_ano = SelectField(
        "Mês/Ano", validators=[DataRequired("O mês e ano são obrigatórios.")]
    )

    submit = SubmitField("Gerar Extrato")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conta_id.choices = [
            (c.id, f"{c.nome_banco} - {c.conta} ({c.tipo})")
            for c in Conta.query.filter_by(usuario_id=current_user.id).all()
        ]

        meses_anos = []
        hoje = date.today()

        # Mapeamento de números de mês para nomes em PT-BR
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

        for i in range(12):  # Gerar para os últimos 12 meses
            mes = hoje.month - i
            ano = hoje.year
            while mes <= 0:
                mes += 12
                ano -= 1

            mes_formatado = f"{mes:02d}"

            value = f"{ano}-{mes_formatado}"
            label = f"{nomes_meses_ptbr[mes]}/{ano}"  # Usa o nome do mês em PT-BR

            meses_anos.append((value, label))

        self.mes_ano.choices = sorted(meses_anos, key=lambda x: x[0], reverse=True)
