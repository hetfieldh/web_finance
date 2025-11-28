# app/models/salario_movimento_model.py

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Enum, UniqueConstraint

from app import db
from app.utils import (
    FormChoices,
)


class SalarioMovimento(db.Model):
    __tablename__ = "salario_movimento"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    mes_referencia = db.Column(db.String(7), nullable=False)

    tipo = db.Column(
        db.Enum(
            *(item.value for item in FormChoices.TipoFolha),
            name="tipo_folha_enum",
        ),
        nullable=False,
        default=FormChoices.TipoFolha.MENSAL.value,
        server_default=FormChoices.TipoFolha.MENSAL.value,
    )

    data_recebimento = db.Column(db.Date, nullable=False)

    movimento_bancario_salario_id = db.Column(
        db.Integer, db.ForeignKey("conta_movimento.id"), nullable=True, unique=True
    )
    movimento_bancario_beneficio_id = db.Column(
        db.Integer, db.ForeignKey("conta_movimento.id"), nullable=True, unique=True
    )
    movimento_bancario_fgts_id = db.Column(
        db.Integer, db.ForeignKey("conta_movimento.id"), nullable=True, unique=True
    )
    status = db.Column(
        db.Enum(
            *(item.value for item in FormChoices.SalarioMovimento),
            name="status_salario_enum",
        ),
        nullable=False,
        default=FormChoices.SalarioMovimento.PENDENTE.value,
        server_default=FormChoices.SalarioMovimento.PENDENTE.value,
    )

    data_criacao = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    usuario = db.relationship(
        "Usuario", backref=db.backref("salario_movimentos", lazy=True)
    )

    itens = db.relationship(
        "SalarioMovimentoItem",
        back_populates="movimento_pai",
        cascade="all, delete-orphan",
    )

    movimento_bancario_salario = db.relationship(
        "ContaMovimento", foreign_keys=[movimento_bancario_salario_id]
    )
    movimento_bancario_beneficio = db.relationship(
        "ContaMovimento", foreign_keys=[movimento_bancario_beneficio_id]
    )
    movimento_bancario_fgts = db.relationship(
        "ContaMovimento", foreign_keys=[movimento_bancario_fgts_id]
    )

    __table_args__ = (
        UniqueConstraint(
            "usuario_id", "mes_referencia", "tipo", name="_usuario_mes_tipo_uc"
        ),
    )

    def __repr__(self):
        return f"<SalarioMovimento Mês: {self.mes_referencia} | Tipo: {self.tipo} | Status: {self.status}>"

    @property
    def salario_liquido(self):
        proventos = sum(
            i.valor
            for i in self.itens
            if i.salario_item.tipo == FormChoices.TipoSalarioItem.PROVENTO.value
        )
        descontos_impostos = sum(
            i.valor
            for i in self.itens
            if i.salario_item.tipo
            in [
                FormChoices.TipoSalarioItem.IMPOSTO.value,
                FormChoices.TipoSalarioItem.DESCONTO.value,
            ]
        )
        return proventos - descontos_impostos

    @property
    def total_beneficios(self):
        return sum(
            i.valor
            for i in self.itens
            if i.salario_item.tipo == FormChoices.TipoSalarioItem.BENEFICIO.value
        )

    @property
    def total_fgts(self):
        return sum(
            i.valor
            for i in self.itens
            if i.salario_item.tipo == FormChoices.TipoSalarioItem.FGTS.value
        )
