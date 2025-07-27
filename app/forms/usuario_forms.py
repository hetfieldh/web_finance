# app/forms/usuario_forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    EqualTo,
    Regexp,
    ValidationError,
    Optional,
)
from app.models.usuario_model import Usuario
import re
from email_validator import validate_email as validate_email_strict, EmailNotValidError


# Validador customizado para senha forte
def validar_senha_forte_custom(form, field):
    senha = field.data
    # Verifica o comprimento mínimo da senha
    if len(senha) < 8:
        raise ValidationError("A senha deve ter pelo menos 8 caracteres.")
    # Verifica a presença de pelo menos uma letra maiúscula
    if not re.search(r"[A-Z]", senha):
        raise ValidationError("A senha deve conter pelo menos uma letra maiúscula.")
    # Verifica a presença de pelo menos um caractere especial
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:\'",<.>/?`~]', senha):
        raise ValidationError("A senha deve conter pelo menos um caractere especial.")


# Validador customizado para e-mail mais estrito
def validar_email_strict_custom(form, field):
    try:
        # Tenta validar o e-mail usando a função rigorosa do email_validator
        validate_email_strict(field.data)
    except EmailNotValidError:
        # Lança um erro de validação se o formato ou domínio for inválido
        raise ValidationError("Formato de e-mail inválido ou domínio inexistente.")


class CadastroUsuarioForm(FlaskForm):
    # Campo para o nome do usuário com validações
    nome = StringField(
        "Nome",
        validators=[
            DataRequired("O campo nome é obrigatório."),
            Length(min=3, max=50, message="O nome deve ter entre 3 e 50 caracteres."),
            Regexp(
                r"^(?!.*\s\s)[a-zA-ZÀ-ÿ\s'\-]+$",  # Não permite múltiplos espaços
                message="O nome contém caracteres inválidos ou múltiplos espaços. Use apenas letras, espaços, hífens ou apóstrofos.",
            ),
        ],
    )
    # Campo para o sobrenome do usuário com validações
    sobrenome = StringField(
        "Sobrenome",
        validators=[
            DataRequired("O campo sobrenome é obrigatório."),
            Length(
                min=3, max=50, message="O sobrenome deve ter entre 3 e 50 caracteres."
            ),
            Regexp(
                r"^(?!.*\s\s)[a-zA-ZÀ-ÿ\s'\-]+$",  # Não permite múltiplos espaços
                message="O sobrenome contém caracteres inválidos ou múltiplos espaços. Use apenas letras, espaços, hífens ou apóstrofos.",
            ),
        ],
    )
    # Campo para o e-mail com validações estritas
    email = StringField(
        "E-mail",
        validators=[
            DataRequired("O campo e-mail é obrigatório."),
            validar_email_strict_custom,  # Usa o validador customizado mais rigoroso
            Length(max=120),
        ],
    )
    # Campo para o login (nome de usuário) com validações
    login = StringField(
        "Login (Nome de Usuário)",
        validators=[
            DataRequired("O campo login é obrigatório."),
            Length(min=4, max=20, message="O login deve ter entre 4 e 20 caracteres."),
            Regexp(
                r"^[a-z0-9._]+$",
                message="O login contém caracteres inválidos. Use apenas letras minúsculas, números, pontos ou sublinhados.",
            ),
        ],
    )
    # Campo para a senha com validação de força
    senha = PasswordField(
        "Senha",
        validators=[
            DataRequired("O campo senha é obrigatório."),
            validar_senha_forte_custom,  # Valida a força da senha
        ],
    )
    # Campo para confirmar a senha
    confirmar_senha = PasswordField(
        "Confirmar Senha",
        validators=[
            DataRequired("Confirmação de senha é obrigatória."),
            EqualTo("senha", message="A senha e a confirmação de senha não coincidem."),
        ],
    )
    # Campo para indicar se o usuário é administrador
    is_admin = BooleanField("Administrador")
    # Botão de submissão do formulário
    submit = SubmitField("Adicionar")

    # Validador para garantir que o e-mail seja único no banco de dados
    def validate_email(self, email):
        usuario = Usuario.query.filter_by(email=email.data).first()
        if usuario:
            raise ValidationError("Este e-mail já está cadastrado.")

    # Validador para garantir que o login seja único e não seja uma palavra reservada
    def validate_login(self, login):
        palavras_reservadas = ["admin", "root", "suporte", "teste", "webmaster"]
        if login.data.lower() in palavras_reservadas:
            raise ValidationError("Este login é reservado e não pode ser utilizado.")
        usuario = Usuario.query.filter_by(login=login.data).first()
        if usuario:
            raise ValidationError("Este login já está em uso.")


class EditarUsuarioForm(FlaskForm):
    # Campo para o nome do usuário com validações
    nome = StringField(
        "Nome",
        validators=[
            DataRequired("O campo nome é obrigatório."),
            Length(min=3, max=50, message="O nome deve ter entre 3 e 50 caracteres."),
            Regexp(
                r"^(?!.*\s\s)[a-zA-ZÀ-ÿ\s'\-]+$",  # Não permite múltiplos espaços
                message="O nome contém caracteres inválidos ou múltiplos espaços. Use apenas letras, espaços, hífens ou apóstrofos.",
            ),
        ],
    )
    # Campo para o sobrenome do usuário com validações
    sobrenome = StringField(
        "Sobrenome",
        validators=[
            DataRequired("O campo sobrenome é obrigatório."),
            Length(
                min=3, max=50, message="O sobrenome deve ter entre 3 e 50 caracteres."
            ),
            Regexp(
                r"^(?!.*\s\s)[a-zA-ZÀ-ÿ\s'\-]+$",  # Não permite múltiplos espaços
                message="O sobrenome contém caracteres inválidos ou múltiplos espaços. Use apenas letras, espaços, hífens ou apóstrofos.",
            ),
        ],
    )
    # Campo para o e-mail com validações estritas
    email = StringField(
        "E-mail",
        validators=[
            DataRequired("O campo e-mail é obrigatório."),
            validar_email_strict_custom,  # Usa o validador customizado mais rigoroso
            Length(max=120),
        ],
    )
    # Campo para o login (nome de usuário) com validações
    login = StringField(
        "Login (Nome de Usuário)",
        validators=[
            DataRequired("O campo login é obrigatório."),
            Length(min=4, max=20, message="O login deve ter entre 4 e 20 caracteres."),
            Regexp(
                r"^[a-z0-9._]+$",
                message="O login contém caracteres inválidos. Use apenas letras minúsculas, números, pontos ou sublinhados.",
            ),
        ],
    )
    # Campo para nova senha (opcional na edição)
    senha = PasswordField(
        "Nova Senha (opcional)",
        validators=[
            Optional(),  # Permite que o campo seja vazio
            validar_senha_forte_custom,  # Valida a força da senha apenas se o campo não estiver vazio
        ],
    )
    # Campo para confirmar nova senha (opcional na edição)
    confirmar_senha = PasswordField(
        "Confirmar Nova Senha",
        validators=[
            Optional(),  # Permite que o campo seja vazio
            EqualTo(
                "senha", message="A nova senha e a confirmação de senha não coincidem."
            ),
        ],
    )
    # Campo para indicar se o usuário está ativo
    is_active = BooleanField("Ativo?")
    # Campo para indicar se o usuário é administrador
    is_admin = BooleanField("Administrador")
    # Botão de submissão do formulário
    submit = SubmitField("Atualizar")

    # Construtor para EditarUsuarioForm, recebendo e-mail e login originais para validação de unicidade
    def __init__(self, original_email, original_login, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_email = original_email
        self.original_login = original_login

    # Validador para garantir que o e-mail seja único, excluindo o e-mail original do usuário atual
    def validate_email(self, email):
        if email.data != self.original_email:  # Somente valida se o e-mail mudou
            usuario = Usuario.query.filter_by(email=email.data).first()
            if usuario:
                raise ValidationError(
                    "Este e-mail já está cadastrado por outro usuário."
                )

    # Validador para garantir que o login seja único (exceto o do usuário atual) e não seja uma palavra reservada
    def validate_login(self, login):
        palavras_reservadas = ["admin", "root", "suporte", "teste", "webmaster"]
        # Verifica se o novo login é uma palavra reservada e diferente do login original do usuário
        if (
            login.data.lower() in palavras_reservadas
            and login.data.lower() != self.original_login.lower()
        ):
            raise ValidationError("Este login é reservado e não pode ser utilizado.")
        if login.data != self.original_login:  # Somente valida se o login mudou
            usuario = Usuario.query.filter_by(login=login.data).first()
            if usuario:
                raise ValidationError("Este login já está em uso por outro usuário.")
