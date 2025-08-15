# app/forms/usuario_forms.py

import re

from email_validator import EmailNotValidError
from email_validator import validate_email as validate_email_strict
from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    Optional,
    Regexp,
    ValidationError,
)

from app.models.usuario_model import Usuario


def validar_senha_forte_custom(form, field):
    senha = field.data
    if len(senha) < 8:
        raise ValidationError("A senha deve ter pelo menos 8 caracteres.")
    if not re.search(r"[A-Z]", senha):
        raise ValidationError("A senha deve conter pelo menos uma letra maiúscula.")
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:\'",<.>/?`~]', senha):
        raise ValidationError("A senha deve conter pelo menos um caractere especial.")


def validar_email_strict_custom(form, field):
    try:
        validate_email_strict(field.data)
    except EmailNotValidError:
        raise ValidationError("Formato de e-mail inválido ou domínio inexistente.")


class CadastroUsuarioForm(FlaskForm):
    nome = StringField(
        "Nome",
        validators=[
            DataRequired("O campo nome é obrigatório."),
            Length(min=3, max=50, message="O nome deve ter entre 3 e 50 caracteres."),
            Regexp(
                r"^(?!.*\s\s)[a-zA-ZÀ-ÿ\s'\-]+$",
                message="O nome contém caracteres inválidos ou múltiplos espaços. Use apenas letras, espaços, hífens ou apóstrofos.",
            ),
        ],
    )
    sobrenome = StringField(
        "Sobrenome",
        validators=[
            DataRequired("O campo sobrenome é obrigatório."),
            Length(
                min=3, max=50, message="O sobrenome deve ter entre 3 e 50 caracteres."
            ),
            Regexp(
                r"^(?!.*\s\s)[a-zA-ZÀ-ÿ\s'\-]+$",
                message="O sobrenome contém caracteres inválidos ou múltiplos espaços. Use apenas letras, espaços, hífens ou apóstrofos.",
            ),
        ],
    )
    email = StringField(
        "E-mail",
        validators=[
            DataRequired("O campo e-mail é obrigatório."),
            validar_email_strict_custom,
            Length(max=120),
        ],
    )
    login = StringField(
        "Login/Usuário",
        validators=[
            DataRequired("O campo login é obrigatório."),
            Length(min=4, max=20, message="O login deve ter entre 4 e 20 caracteres."),
            Regexp(
                r"^[a-z0-9._]+$",
                message="O login contém caracteres inválidos. Use apenas letras minúsculas, números, pontos ou sublinhados.",
            ),
        ],
    )
    senha = PasswordField(
        "Senha",
        validators=[
            DataRequired("O campo senha é obrigatório."),
            validar_senha_forte_custom,
        ],
    )
    confirmar_senha = PasswordField(
        "Confirmar Senha",
        validators=[
            DataRequired("Confirmação de senha é obrigatória."),
            EqualTo("senha", message="A senha e a confirmação de senha não coincidem."),
        ],
    )
    is_admin = BooleanField("Administrador")
    submit = SubmitField("Adicionar")

    def validate_email(self, email):
        usuario = Usuario.query.filter_by(email=email.data).first()
        if usuario:
            raise ValidationError("Este e-mail já está cadastrado.")

    def validate_login(self, login):
        palavras_reservadas = ["admin", "root", "suporte", "teste", "webmaster"]
        if login.data.lower() in palavras_reservadas:
            raise ValidationError("Este login é reservado e não pode ser utilizado.")
        usuario = Usuario.query.filter_by(login=login.data).first()
        if usuario:
            raise ValidationError("Este login já está em uso.")


class EditarUsuarioForm(FlaskForm):
    nome = StringField(
        "Nome",
        validators=[
            DataRequired("O campo nome é obrigatório."),
            Length(min=3, max=50, message="O nome deve ter entre 3 e 50 caracteres."),
            Regexp(
                r"^(?!.*\s\s)[a-zA-ZÀ-ÿ\s'\-]+$",
                message="O nome contém caracteres inválidos ou múltiplos espaços. Use apenas letras, espaços, hífens ou apóstrofos.",
            ),
        ],
    )
    sobrenome = StringField(
        "Sobrenome",
        validators=[
            DataRequired("O campo sobrenome é obrigatório."),
            Length(
                min=3, max=50, message="O sobrenome deve ter entre 3 e 50 caracteres."
            ),
            Regexp(
                r"^(?!.*\s\s)[a-zA-ZÀ-ÿ\s'\-]+$",
                message="O sobrenome contém caracteres inválidos ou múltiplos espaços. Use apenas letras, espaços, hífens ou apóstrofos.",
            ),
        ],
    )
    email = StringField(
        "E-mail",
        validators=[
            DataRequired("O campo e-mail é obrigatório."),
            validar_email_strict_custom,
            Length(max=120),
        ],
    )
    login = StringField(
        "Login/Usuário",
        validators=[
            DataRequired("O campo login é obrigatório."),
            Length(min=4, max=20, message="O login deve ter entre 4 e 20 caracteres."),
            Regexp(
                r"^[a-z0-9._]+$",
                message="O login contém caracteres inválidos. Use apenas letras minúsculas, números, pontos ou sublinhados.",
            ),
        ],
    )
    senha = PasswordField(
        "Nova Senha (opcional)",
        validators=[
            Optional(),
            validar_senha_forte_custom,
        ],
    )
    confirmar_senha = PasswordField(
        "Confirmar Nova Senha",
        validators=[
            Optional(),
            EqualTo(
                "senha", message="A nova senha e a confirmação de senha não coincidem."
            ),
        ],
    )
    is_active = BooleanField("Ativo?")
    is_admin = BooleanField("Administrador")
    submit = SubmitField("Atualizar")

    def __init__(self, original_email, original_login, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_email = original_email
        self.original_login = original_login

    def validate_email(self, email):
        if email.data != self.original_email:
            usuario = Usuario.query.filter_by(email=email.data).first()
            if usuario:
                raise ValidationError(
                    "Este e-mail já está cadastrado por outro usuário."
                )

    def validate_login(self, login):
        palavras_reservadas = ["admin", "root", "suporte", "teste", "webmaster"]
        if (
            login.data.lower() in palavras_reservadas
            and login.data.lower() != self.original_login.lower()
        ):
            raise ValidationError("Este login é reservado e não pode ser utilizado.")
        if login.data != self.original_login:
            usuario = Usuario.query.filter_by(login=login.data).first()
            if usuario:
                raise ValidationError("Este login já está em uso por outro usuário.")
