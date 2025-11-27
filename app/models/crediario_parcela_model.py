# app/models/crediario_parcela_model.py

from datetime import date, datetime, timezone

from sqlalchemy import Numeric, UniqueConstraint

from app import db


class CrediarioParcela(db.Model):
    __tablename__ = "crediario_parcela"

    id = db.Column(db.Integer, primary_key=True)
    crediario_movimento_id = db.Column(
        db.Integer, db.ForeignKey("crediario_movimento.id"), nullable=False
    )
    numero_parcela = db.Column(db.Integer, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    valor_parcela = db.Column(Numeric(12, 2), nullable=False)
    pago = db.Column(db.Boolean, nullable=False, default=False)
    data_pagamento = db.Column(db.Date, nullable=True)

    data_criacao = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    movimento_pai = db.relationship("CrediarioMovimento", back_populates="parcelas")

    __table_args__ = (
        UniqueConstraint(
            "crediario_movimento_id", "numero_parcela", name="_crediario_parcela_uc"
        ),
    )

    def __repr__(self):
        return f"<Parcela {self.numero_parcela} de {self.crediario_movimento_id} | Venc: {self.data_vencimento} | {self.valor_parcela}>"
