# app/models/desp_rec_movimento_model.py

from datetime import datetime, timezone

from sqlalchemy import Enum, Numeric, UniqueConstraint

from app import db


class DespRecMovimento(db.Model):
    __tablename__ = "desp_rec_movimento"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    desp_rec_id = db.Column(db.Integer, db.ForeignKey("desp_rec.id"), nullable=False)

    data_vencimento = db.Column(db.Date, nullable=False)
    valor_previsto = db.Column(db.Numeric(12, 2), nullable=False)

    data_pagamento = db.Column(db.Date, nullable=True)
    valor_realizado = db.Column(db.Numeric(12, 2), nullable=True)

    status = db.Column(
        Enum("Pendente", "Pago", "Atrasado", name="status_lancamento_enum"),
        nullable=False,
        default="Pendente",
    )
    descricao = db.Column(db.String(255), nullable=True)

    movimento_bancario_id = db.Column(
        db.Integer, db.ForeignKey("conta_movimento.id"), nullable=True
    )
    data_criacao = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    usuario = db.relationship(
        "Usuario", backref=db.backref("desp_rec_movimentos", lazy=True)
    )
    despesa_receita = db.relationship(
        "DespRec",
        backref=db.backref("movimentos", lazy=True, cascade="all, delete-orphan"),
    )

    def __repr__(self):
        return f"<DespRecMovimento ID: {self.id} | Venc: {self.data_vencimento} | Valor: {self.valor_previsto}>"
