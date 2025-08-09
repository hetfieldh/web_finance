# app/models/crediario_fatura_model.py

from datetime import date, datetime, timezone

from sqlalchemy import Enum, Numeric, UniqueConstraint

from app import db


class CrediarioFatura(db.Model):
    __tablename__ = "crediario_fatura"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    crediario_id = db.Column(db.Integer, db.ForeignKey("crediario.id"), nullable=False)

    mes_referencia = db.Column(db.String(7), nullable=False)
    valor_total_fatura = db.Column(Numeric(12, 2), nullable=False)
    valor_pago_fatura = db.Column(Numeric(12, 2), nullable=False, default=0.00)

    data_fechamento = db.Column(db.Date, nullable=True)
    data_vencimento_fatura = db.Column(db.Date, nullable=False)

    status = db.Column(
        Enum(
            "Aberta",
            "Fechada",
            "Paga",
            "Atrasada",
            "Parcialmente Paga",
            name="status_fatura_enum",
        ),
        nullable=False,
        default="Aberta",
    )
    data_pagamento = db.Column(db.Date, nullable=True)

    movimento_bancario_id = db.Column(
        db.Integer, db.ForeignKey("conta_movimento.id"), nullable=True
    )

    data_criacao = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    usuario = db.relationship("Usuario", backref=db.backref("faturas", lazy=True))
    crediario = db.relationship("Crediario", backref=db.backref("faturas", lazy=True))

    __table_args__ = (
        UniqueConstraint(
            "usuario_id",
            "crediario_id",
            "mes_referencia",
            name="_usuario_crediario_fatura_uc",
        ),
    )

    def __repr__(self):
        return f"<Fatura {self.mes_referencia} | Crediário: {self.crediario_id} | Status: {self.status}>"
