# app/forms/recebimentos_forms.py

from datetime import date

from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, HiddenField, SelectField, SubmitField
from wtforms.validators import DataRequired, InputRequired, NumberRange

from app.models.conta_model import Conta
from app.utils import gerar_opcoes_mes_ano


class PainelRecebimentosForm(FlaskForm):
    mes_ano = SelectField(
        "Mês/Ano de Referência",
        validators=[DataRequired("O mês e ano são obrigatórios.")],
    )
    submit = SubmitField("Filtrar")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mes_ano.choices = gerar_opcoes_mes_ano(
            meses_passados=12, meses_futuros=12, incluir_selecione=False
        )


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
            (c.id, f"{c.nome_banco} - {c.tipo} (Saldo: R$ {c.saldo_atual:.2f})")
            for c in Conta.query.filter_by(usuario_id=current_user.id, ativa=True)
            .order_by(Conta.nome_banco.asc())
            .all()
        ]
