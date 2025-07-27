# app/models/conta_model.py

from app import db
from datetime import datetime, timezone
from sqlalchemy import Enum, UniqueConstraint, Numeric


class Conta(db.Model):
    # Define o nome da tabela no banco de dados
    __tablename__ = "conta"

    # Definição das colunas da tabela
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    nome_banco = db.Column(db.String(100), nullable=False)
    agencia = db.Column(db.String(20), nullable=False)
    conta = db.Column(db.String(50), nullable=False)

    tipo = db.Column(
        Enum(
            "Corrente",
            "Poupança",
            "Digital",
            "Investimento",
            "Caixinha",
            "Dinheiro",
            name="tipo_conta_enum",
        ),
        nullable=False,
    )

    saldo_inicial = db.Column(Numeric(12, 2), nullable=False)
    saldo_atual = db.Column(Numeric(12, 2), nullable=False)
    limite = db.Column(Numeric(12, 2), nullable=True)
    ativa = db.Column(db.Boolean, nullable=False, default=True)
    data_criacao = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relacionamento com o modelo Usuario
    usuario = db.relationship("Usuario", backref=db.backref("contas", lazy=True))

    # Define um índice único composto
    __table_args__ = (
        UniqueConstraint(
            "usuario_id",
            "nome_banco",
            "agencia",
            "conta",
            "tipo",
            name="_usuario_conta_uc",
        ),
    )

    def __repr__(self):
        return f"<Conta {self.nome_banco} - {self.conta} ({self.tipo})>"
