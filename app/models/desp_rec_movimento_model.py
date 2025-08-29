# app\models\desp_rec_movimento_model.py

from datetime import datetime, timezone

from sqlalchemy import Enum, Numeric, UniqueConstraint, event, text

from app import db
from app.models.conta_movimento_model import ContaMovimento
from app.utils import STATUS_PENDENTE, FormChoices

from .desp_rec_model import DespRec


class DespRecMovimento(db.Model):
    __tablename__ = "desp_rec_movimento"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    desp_rec_id = db.Column(db.Integer, db.ForeignKey("desp_rec.id"), nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    mes = db.Column(db.Integer, nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    valor_previsto = db.Column(db.Numeric(12, 2), nullable=False)
    data_pagamento = db.Column(db.Date, nullable=True)
    valor_realizado = db.Column(db.Numeric(12, 2), nullable=True)
    status = db.Column(
        db.Enum(
            *(item.value for item in FormChoices.StatusDespesaReceita),
            name="status_lancamento_enum",
        ),
        nullable=False,
        default=FormChoices.StatusDespesaReceita.PENDENTE.value,
    )
    descricao = db.Column(db.String(255), nullable=True)
    movimento_bancario_id = db.Column(
        db.Integer, db.ForeignKey("conta_movimento.id"), nullable=True
    )
    movimento_bancario = db.relationship("ContaMovimento")
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

    __table_args__ = ()

    def __repr__(self):
        return f"<DespRecMovimento ID: {self.id} | Venc: {self.data_vencimento} | Valor: {self.valor_previsto}>"


@event.listens_for(DespRecMovimento.__table__, "after_create")
def create_partial_unique_constraint(target, connection, **kw):
    connection.execute(
        text(
            """
        CREATE UNIQUE INDEX ix_unique_fixed_desprec_movimento
        ON desp_rec_movimento (usuario_id, desp_rec_id, ano, mes)
        WHERE (
            SELECT tipo FROM desp_rec WHERE id = desp_rec_id
        ) = 'Fixa'
    """
        )
    )


@event.listens_for(DespRecMovimento, "before_insert")
@event.listens_for(DespRecMovimento, "before_update")
def popular_mes_ano(mapper, connection, target):
    if target.data_vencimento:
        target.ano = target.data_vencimento.year
        target.mes = target.data_vencimento.month
