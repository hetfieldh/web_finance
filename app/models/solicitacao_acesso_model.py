# app/models/solicitacao_acesso_model.py

from datetime import datetime, timezone

from sqlalchemy import Enum

from app import db
from app.utils import FormChoices


class SolicitacaoAcesso(db.Model):
    __tablename__ = "solicitacao_acesso"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    sobrenome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    justificativa = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum(
            *(item.value for item in FormChoices.StatusSolicitacao),
            name="status_solicitacao_enum",
        ),
        nullable=False,
        default=FormChoices.StatusSolicitacao.PENDENTE.value,
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
