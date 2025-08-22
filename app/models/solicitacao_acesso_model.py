# app/models/solicitacao_acesso_model.py (Refatorado)

from datetime import datetime, timezone

from sqlalchemy import Enum

from app import db


class SolicitacaoAcesso(db.Model):
    __tablename__ = "solicitacao_acesso"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    sobrenome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    justificativa = db.Column(db.Text, nullable=True)
    status = db.Column(
        Enum("Pendente", "Aprovada", "Rejeitada", name="status_solicitacao_enum"),
        nullable=False,
        default="Pendente",
    )
    data_solicitacao = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    admin_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=True)
    data_decisao = db.Column(db.DateTime, nullable=True)
    motivo_decisao = db.Column(db.Text, nullable=True)
    login_criado = db.Column(db.String(80), nullable=True)
    admin = db.relationship("Usuario")

    def __repr__(self):
        return f"<SolicitacaoAcesso {self.id} - {self.email} ({self.status})>"
