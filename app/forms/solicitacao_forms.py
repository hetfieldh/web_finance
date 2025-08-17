# app\forms\solicitacao_forms.py

from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, ValidationError

from app.models.solicitacao_acesso_model import SolicitacaoAcesso
from app.models.usuario_model import Usuario


class SolicitacaoAcessoForm(FlaskForm):
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
    email = StringField(
        "E-mail",
        validators=[
            DataRequired("O e-mail é obrigatório."),
            Email("Formato de e-mail inválido."),
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
    submit = SubmitField("Enviar Solicitação")

    def validate_email(self, email):
        email_limpo = email.data.strip()
        if Usuario.query.filter_by(email=email_limpo).first():
            raise ValidationError("Este e-mail já está cadastrado no sistema.")

        if SolicitacaoAcesso.query.filter_by(email=email_limpo).first():
            raise ValidationError(
                "Já existe uma solicitação de acesso (aprovada ou rejeitada) para este e-mail."
            )


class VerificarStatusForm(FlaskForm):
    email = StringField(
        "Seu E-mail de Solicitação",
        validators=[
            DataRequired("O e-mail é obrigatório."),
            Email("Formato de e-mail inválido."),
        ],
    )
    submit = SubmitField("Verificar Status")


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
