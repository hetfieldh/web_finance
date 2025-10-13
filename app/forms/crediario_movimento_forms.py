# app/forms/crediario_movimento_forms.py

from datetime import date, datetime

from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    InputRequired,
    Length,
    NumberRange,
    Optional,
    ValidationError,
)

from app import db
from app.models.crediario_grupo_model import CrediarioGrupo
from app.models.crediario_model import Crediario
from app.models.crediario_movimento_model import CrediarioMovimento
from app.utils import FormChoices


def coerce_month_year_to_date(value):
    if isinstance(value, date):
        return value
    if value:
        try:
            year, month = map(int, value.split("-"))
            return date(year, month, 1)
        except ValueError:
            raise ValidationError("Formato de mês/ano inválido. Use AAAA-MM.")
    return None


class CadastroCrediarioMovimentoForm(FlaskForm):
    crediario_id = SelectField(
        "Crediário",
        validators=[DataRequired("O crediário é obrigatório.")],
        coerce=lambda x: int(x) if x else None,
    )

    crediario_grupo_id = SelectField(
        "Grupo de Crediário",
        validators=[DataRequired("O grupo de crediário é obrigatório.")],
        coerce=lambda x: int(x) if x else None,
    )

    destino = SelectField(
        "Destino",
        choices=FormChoices.get_choices(FormChoices.DestinoCrediario),
        validators=[DataRequired("O destino é obrigatório.")],
        default=FormChoices.DestinoCrediario.PROPRIO.value,
    )

    data_compra = DateField(
        "Data da Compra",
        format="%Y-%m-%d",
        validators=[DataRequired("A data da compra é obrigatória.")],
        default=date.today(),
    )

    valor_total_compra = DecimalField(
        "Valor Total da Compra",
        validators=[
            InputRequired("O valor total da compra é obrigatório."),
            NumberRange(min=0.01, message="O valor deve ser maior que zero."),
        ],
        places=2,
    )

    descricao = TextAreaField(
        "Descrição",
        validators=[
            DataRequired("A descrição é obrigatória."),
            Length(max=255, message="A descrição não pode exceder 255 caracteres."),
        ],
    )

    data_primeira_parcela = SelectField(
        "Mês/Ano da 1ª Parcela",
        validators=[DataRequired("O mês/ano da primeira parcela é obrigatório.")],
        coerce=coerce_month_year_to_date,
    )

    numero_parcelas = IntegerField(
        "Número de Parcelas",
        validators=[
            DataRequired("O número de parcelas é obrigatório."),
            NumberRange(min=1, message="O número de parcelas deve ser no mínimo 1."),
        ],
        default=1,
    )

    submit = SubmitField("Adicionar")

    def __init__(self, *args, **kwargs):
        crediario_choices = kwargs.pop("crediario_choices", [])
        grupo_choices = kwargs.pop("grupo_choices", [])

        super().__init__(*args, **kwargs)

        self.crediario_id.choices = crediario_choices
        self.crediario_grupo_id.choices = grupo_choices

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

        for i in range(2):
            mes = hoje.month + i
            ano = hoje.year
            while mes > 12:
                mes -= 12
                ano += 1

            mes_formatado = f"{mes:02d}"
            value = f"{ano}-{mes_formatado}"
            label = f"{nomes_meses_ptbr[mes]}/{ano}"

            meses_anos.append((value, label))

        self.data_primeira_parcela.choices = [("", "Selecione...")] + meses_anos


class EditarCrediarioMovimentoForm(FlaskForm):
    crediario_id = SelectField(
        "Crediário",
        validators=[Optional()],
        coerce=lambda x: int(x) if x else None,
        render_kw={"disabled": True},
    )

    crediario_grupo_id = SelectField(
        "Grupo de Crediário (opcional)",
        validators=[Optional()],
        coerce=lambda x: int(x) if x else None,
        render_kw={"disabled": True},
    )

    data_compra = DateField(
        "Data da Compra",
        format="%Y-%m-%d",
        validators=[DataRequired("A data da compra é obrigatória.")],
        render_kw={"readonly": True},
    )

    valor_total_compra = DecimalField(
        "Valor Total da Compra",
        validators=[
            InputRequired("O valor total da compra é obrigatório."),
            NumberRange(min=0.01, message="O valor deve ser maior que zero."),
        ],
        places=2,
        render_kw={"readonly": True},
    )

    descricao = TextAreaField(
        "Descrição",
        validators=[
            DataRequired("A descrição é obrigatória."),
            Length(max=255, message="A descrição não pode exceder 255 caracteres."),
        ],
    )

    destino = SelectField(
        "Destino",
        choices=FormChoices.get_choices(FormChoices.DestinoCrediario),
        validators=[DataRequired("O destino é obrigatório.")],
        render_kw={"disabled": True},
    )

    data_primeira_parcela = SelectField(
        "Mês/Ano da 1ª Parcela",
        validators=[DataRequired("A data da primeira parcela é obrigatória.")],
        coerce=coerce_month_year_to_date,
        render_kw={"disabled": True},
    )

    numero_parcelas = IntegerField(
        "Número de Parcelas",
        validators=[
            DataRequired("O número de parcelas é obrigatório."),
            NumberRange(min=1, message="O número de parcelas deve ser no mínimo 1."),
        ],
        render_kw={"readonly": True},
    )

    submit = SubmitField("Atualizar")

    def __init__(self, *args, **kwargs):
        crediario_choices = kwargs.pop("crediario_choices", [])
        grupo_choices = kwargs.pop("grupo_choices", [])

        super().__init__(*args, **kwargs)

        self.crediario_id.choices = crediario_choices
        self.crediario_grupo_id.choices = grupo_choices

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
            mes = hoje.month + i
            ano = hoje.year
            while mes > 12:
                mes -= 12
                ano += 1

            mes_formatado = f"{mes:02d}"
            value = f"{ano}-{mes_formatado}"
            label = f"{nomes_meses_ptbr[mes]}/{ano}"

            meses_anos.append((value, label))

        self.data_primeira_parcela.choices = [("", "Selecione...")] + meses_anos
