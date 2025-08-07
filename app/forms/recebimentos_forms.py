# app/forms/recebimentos_forms.py

from datetime import date

from dateutil.relativedelta import relativedelta
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, HiddenField, SelectField, SubmitField
from wtforms.validators import DataRequired, InputRequired, NumberRange

from app.models.conta_model import Conta


class PainelRecebimentosForm(FlaskForm):

    mes_ano = SelectField(
        "Mês/Ano de Referência",
        validators=[DataRequired("O mês e ano são obrigatórios.")],
    )
    submit = SubmitField("Filtrar")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

        self.mes_ano.choices = sorted(meses_anos, key=lambda x: x[0], reverse=True)


class RecebimentoForm(FlaskForm):

    conta_id = SelectField(
        "Receber na Conta",
        coerce=lambda x: int(x) if x else None,
        validators=[DataRequired("Selecione a conta para o recebimento.")],
    )
    data_recebimento = DateField(
        "Data do Recebimento",
        format="%Y-%m-%d",
        validators=[DataRequired("A data do recebimento é obrigatória.")],
        default=date.today,
    )
    valor_recebido = DecimalField(
        "Valor Recebido",
        places=2,
        validators=[
            InputRequired("O valor é obrigatório."),
            NumberRange(min=0.01, message="O valor recebido deve ser maior que zero."),
        ],
    )
    item_id = HiddenField()
    item_tipo = HiddenField()
    item_descricao = HiddenField()

    submit = SubmitField("Confirmar Recebimento")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conta_id.choices = [("", "Selecione...")] + [
            (c.id, f"{c.nome_banco} - {c.conta} (Saldo: R$ {c.saldo_atual:.2f})")
            for c in Conta.query.filter_by(usuario_id=current_user.id, ativa=True)
            .order_by(Conta.nome_banco.asc())
            .all()
        ]
