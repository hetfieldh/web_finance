# app/models/financiamento_parcela_model.py

from datetime import datetime, timezone

from sqlalchemy import Enum, Numeric, UniqueConstraint

from app import db
from app.models.conta_movimento_model import ContaMovimento
from app.utils import FormChoices


class FinanciamentoParcela(db.Model):
    __tablename__ = "financiamento_parcela"

    id = db.Column(db.Integer, primary_key=True)
    financiamento_id = db.Column(
        db.Integer, db.ForeignKey("financiamento.id"), nullable=False
    )
    numero_parcela = db.Column(db.Integer, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)

    valor_principal = db.Column(Numeric(12, 2), nullable=False)
    valor_juros = db.Column(Numeric(12, 2), nullable=False)
    valor_seguro = db.Column(Numeric(12, 2), nullable=False, default=0.00)
    valor_seguro_2 = db.Column(Numeric(12, 2), nullable=False, default=0.00)
    valor_seguro_3 = db.Column(Numeric(12, 2), nullable=False, default=0.00)
    valor_taxas = db.Column(Numeric(12, 2), nullable=False, default=0.00)
    multa = db.Column(Numeric(12, 2), nullable=False, default=0.00)
    mora = db.Column(Numeric(12, 2), nullable=False, default=0.00)
    ajustes = db.Column(Numeric(12, 2), nullable=False, default=0.00)
    valor_total_previsto = db.Column(Numeric(12, 2), nullable=False)
    saldo_devedor = db.Column(Numeric(12, 2), nullable=False)
    pago = db.Column(db.Boolean, nullable=False, default=False)
    data_pagamento = db.Column(db.Date, nullable=True)
    valor_pago = db.Column(Numeric(12, 2), nullable=True)
    observacoes = db.Column(db.String(255), nullable=True)
    movimento_bancario_id = db.Column(
        db.Integer, db.ForeignKey("conta_movimento.id"), nullable=True
    )
    movimento_bancario = db.relationship("ContaMovimento")
    status = db.Column(
        db.Enum(
            *(item.value for item in FormChoices.StatusFinanciamento),
            name="status_parcela_enum",
        ),
        nullable=False,
        default=FormChoices.StatusFinanciamento.PENDENTE.value,
    )
    data_criacao = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    financiamento = db.relationship(
        "Financiamento",
        backref=db.backref("parcelas", lazy=True, cascade="all, delete-orphan"),
    )
    __table_args__ = (
        UniqueConstraint(
            "financiamento_id", "numero_parcela", name="_financiamento_parcela_uc"
        ),
    )

    def __repr__(self):
        return f"<Parcela {self.numero_parcela} de {self.financiamento_id} | Total: R$ {self.valor_total_previsto}>"
