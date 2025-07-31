# app/forms/crediario_movimento_forms.py

from datetime import date

from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (
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
            Length(max=255, message="A descrição não pode exceder 255 caracteres."),
            Optional(),
        ],
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
        super().__init__(*args, **kwargs)
        self.crediario_id.choices = [("", "Selecione...")] + [
            (
                str(c.id),
                f"{c.nome_crediario} ({c.tipo_crediario})",
            )
            for c in Crediario.query.filter_by(usuario_id=current_user.id, ativa=True)
            .order_by(Crediario.nome_crediario.asc())
            .all()
        ]
        self.crediario_grupo_id.choices = [("", "Nenhum")] + [
            (
                str(cg.id),
                f"{cg.grupo_crediario} ({cg.tipo_grupo_crediario})",
            )
            for cg in CrediarioGrupo.query.filter_by(usuario_id=current_user.id)
            .order_by(CrediarioGrupo.grupo_crediario.asc())
            .all()
        ]


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
        super().__init__(*args, **kwargs)
        self.crediario_id.choices = [("", "Selecione...")] + [
            (
                str(c.id),
                f"{c.nome_crediario} ({c.tipo_crediario})",
            )
            for c in Crediario.query.filter_by(usuario_id=current_user.id)
            .order_by(Crediario.nome_crediario.asc())
            .all()
        ]
        self.crediario_grupo_id.choices = [("", "Nenhum")] + [
            (
                str(cg.id),
                f"{cg.grupo_crediario} ({cg.tipo_grupo_crediario})",
            )
            for cg in CrediarioGrupo.query.filter_by(usuario_id=current_user.id)
            .order_by(CrediarioGrupo.grupo_crediario.asc())
            .all()
        ]
