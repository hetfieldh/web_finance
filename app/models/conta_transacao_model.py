# app/models/conta_transacao_model.py

from app import db
from datetime import datetime, timezone
from sqlalchemy import Enum, UniqueConstraint


class ContaTransacao(db.Model):
    __tablename__ = "conta_transacao"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    transacao_tipo = db.Column(db.String(100), nullable=False)

    tipo = db.Column(
        Enum("Crédito", "Débito", name="tipo_movimento_enum"), nullable=False
    )

    data_criacao = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    usuario = db.relationship(
        "Usuario", backref=db.backref("tipos_transacao", lazy=True)
    )

    __table_args__ = (
        UniqueConstraint(
            "usuario_id", "transacao_tipo", "tipo", name="_usuario_transacao_tipo_uc"
        ),
    )

    def __repr__(self):
        return f"<ContaTransacao {self.transacao_tipo} ({self.tipo})>"
