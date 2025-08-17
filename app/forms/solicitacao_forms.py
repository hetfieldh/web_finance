# app\forms\solicitacao_forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
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
        if Usuario.query.filter_by(email=email.data).first():
            raise ValidationError("Este e-mail já está cadastrado no sistema.")

        if SolicitacaoAcesso.query.filter_by(
            email=email.data, status="Pendente"
        ).first():
            raise ValidationError(
                "Já existe uma solicitação de acesso pendente para este e-mail."
            )
