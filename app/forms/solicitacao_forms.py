# app\forms\solicitacao_forms.py

from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, ValidationError

from app.models.solicitacao_acesso_model import SolicitacaoAcesso
from app.models.usuario_model import Usuario


class SolicitacaoAcessoForm(FlaskForm):
    email = StringField(
        "Seu E-mail",
        validators=[
            DataRequired("O e-mail é obrigatório."),
            Email("Formato de e-mail inválido."),
        ],
    )
    nome = StringField(
        "Nome",
        validators=[
            DataRequired("O nome é obrigatório."),
            Length(min=2, max=100, message="O nome deve ter entre 2 e 100 caracteres."),
        ],
    )
    sobrenome = StringField(
        "Sobrenome",
        validators=[
            DataRequired("O sobrenome é obrigatório."),
            Length(
                min=2, max=100, message="O sobrenome deve ter entre 2 e 100 caracteres."
            ),
        ],
    )
    justificativa = TextAreaField(
        "Justificativa (Opcional)",
        validators=[Length(max=500)],
        render_kw={
            "rows": 4,
            "placeholder": "Ex: Motivo pelo qual precisa de acesso ao sistema.",
        },
    )
    submit = SubmitField("Enviar")


class VerificarStatusForm(FlaskForm):
    email = StringField(
        "Seu E-mail de Solicitação",
        validators=[
            DataRequired("O e-mail é obrigatório."),
            Email("Formato de e-mail inválido."),
        ],
    )
    submit = SubmitField("Verificar")


class RejeicaoForm(FlaskForm):
    motivo = TextAreaField(
        "Motivo da Rejeição",
        validators=[DataRequired("O motivo é obrigatório."), Length(min=10, max=500)],
        render_kw={"rows": 4},
    )
    solicitacao_id = HiddenField()
    submit = SubmitField("Confirmar Rejeição")


class AprovacaoForm(FlaskForm):
    motivo = TextAreaField(
        "Mensagem Adicional (Opcional)",
        validators=[Length(max=500)],
        render_kw={
            "rows": 4,
            "placeholder": "Ex: O login criado foi 'douglas.f'. A senha inicial é 'mudar123'.",
        },
    )
    solicitacao_id = HiddenField()
    submit = SubmitField("Confirmar Aprovação e Criar Usuário")
