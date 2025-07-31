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
        "Grupo de Crediário (opcional)",
        validators=[Optional()],
        coerce=lambda x: int(x) if x else None,
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
        "Descrição (opcional)",
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

    submit = SubmitField("Registrar Compra")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crediario_id.choices = [("", "Selecione...")] + [
            (str(c.id), f"{c.nome_crediario} ({c.tipo_crediario})")
            for c in Crediario.query.filter_by(usuario_id=current_user.id, ativa=True)
            .order_by(Crediario.nome_crediario.asc())
            .all()
        ]
        self.crediario_grupo_id.choices = [("", "Nenhum")] + [
            (str(cg.id), f"{cg.grupo_crediario} ({cg.tipo_grupo_crediario})")
            for cg in CrediarioGrupo.query.filter_by(usuario_id=current_user.id)
            .order_by(CrediarioGrupo.grupo_crediario.asc())
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

        self.data_primeira_parcela.choices = [
            ("", "Selecione um mês/ano...")
        ] + meses_anos


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
        validators=[DataRequired("A data da primeira parcela é obrigatória.")],
        coerce=coerce_month_year_to_date,
    )

    numero_parcelas = IntegerField(
        "Número de Parcelas",
        validators=[
            DataRequired("O número de parcelas é obrigatório."),
            NumberRange(min=1, message="O número de parcelas deve ser no mínimo 1."),
        ],
    )

    submit = SubmitField("Atualizar Compra")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crediario_id.choices = [("", "Selecione...")] + [
            (str(c.id), f"{c.nome_crediario} ({c.tipo_crediario})")
            for c in Crediario.query.filter_by(usuario_id=current_user.id)
            .order_by(Crediario.nome_crediario.asc())
            .all()
        ]
        self.crediario_grupo_id.choices = [("", "Nenhum")] + [
            (str(cg.id), f"{cg.grupo_crediario} ({cg.tipo_grupo_crediario})")
            for cg in CrediarioGrupo.query.filter_by(usuario_id=current_user.id)
            .order_by(CrediarioGrupo.grupo_crediario.asc())
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
            mes = hoje.month + i
            ano = hoje.year
            while mes > 12:
                mes -= 12
                ano += 1

            mes_formatado = f"{mes:02d}"
            value = f"{ano}-{mes_formatado}"
            label = f"{nomes_meses_ptbr[mes]}/{ano}"

            meses_anos.append((value, label))

        self.data_primeira_parcela.choices = [
            ("", "Selecione um mês/ano...")
        ] + meses_anos
