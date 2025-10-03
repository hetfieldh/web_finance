# app/models/crediario_model.py

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Enum, Numeric, UniqueConstraint, func

from app import db
from app.models.crediario_fatura_model import CrediarioFatura
from app.utils import FormChoices

from .crediario_movimento_model import CrediarioMovimento
from .crediario_parcela_model import CrediarioParcela


class Crediario(db.Model):
    __tablename__ = "crediario"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    nome_crediario = db.Column(db.String(100), nullable=False)
    tipo_crediario = db.Column(
        db.Enum(
            *(item.value for item in FormChoices.TipoCrediario),
            name="tipo_crediario_enum",
        ),
        nullable=False,
    )
    identificador_final = db.Column(db.String(50), nullable=True)
    limite_total = db.Column(Numeric(12, 2), nullable=True)
    dia_vencimento = db.Column(db.Integer, nullable=False, default=30)
    ativa = db.Column(db.Boolean, nullable=False, default=True)
    data_criacao = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    usuario = db.relationship("Usuario", backref=db.backref("crediarios", lazy=True))

    __table_args__ = (
        UniqueConstraint(
            "usuario_id",
            "nome_crediario",
            "tipo_crediario",
            "identificador_final",
            name="_usuario_crediario_uc",
        ),
    )

    def __repr__(self):
        return f"<Crediario {self.nome_crediario} ({self.tipo_crediario})>"

