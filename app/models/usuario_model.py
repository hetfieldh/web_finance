# app/models/usuario_model.py

from app import db
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class Usuario(db.Model, UserMixin):
    # Define o nome da tabela no banco de dados
    __tablename__ = "usuario"

    # Definição das colunas da tabela
    id = db.Column(db.Integer, primary_key=True)  # Chave primária, auto-incrementável
    nome = db.Column(db.String(100), nullable=False)  # Nome do usuário, obrigatório
    sobrenome = db.Column(
        db.String(100), nullable=False
    )  # Sobrenome do usuário, obrigatório
    email = db.Column(
        db.String(120), unique=True, nullable=False
    )  # E-mail, único e obrigatório
    login = db.Column(
        db.String(80), unique=True, nullable=False
    )  # Login/Nome de usuário, único e obrigatório
    senha_hash = db.Column(
        db.String(256), nullable=False
    )  # Hash da senha, obrigatório (tamanho maior para scrypt)
    is_active = db.Column(
        db.Boolean, default=True
    )  # Indica se o usuário está ativo, padrão True
    is_admin = db.Column(
        db.Boolean, default=False
    )  # Indica se o usuário é administrador, padrão False
    # Data de criação do registro, com timezone UTC para consistência
    data_criacao = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Método de representação para facilitar a depuração
    def __repr__(self):
        return f"<Usuario {self.login} ({self.email})>"

    # Método para definir a senha, gerando um hash seguro
    def set_password(self, password):
        self.senha_hash = generate_password_hash(password)

    # Método para verificar se a senha fornecida corresponde ao hash armazenado
    def check_password(self, password):
        return check_password_hash(self.senha_hash, password)
