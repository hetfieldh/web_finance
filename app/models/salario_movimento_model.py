# app/models/salario_movimento_model.py

from datetime import datetime, timezone

from sqlalchemy import Enum, UniqueConstraint

from app import db


class SalarioMovimento(db.Model):
    __tablename__ = "salario_movimento"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    mes_referencia = db.Column(db.String(7), nullable=False)  # Formato AAAA-MM
    data_recebimento = db.Column(db.Date, nullable=False)
    movimento_bancario_id = db.Column(
        db.Integer, db.ForeignKey("conta_movimento.id"), nullable=True, unique=True
    )
    status = db.Column(
        Enum("Pendente", "Recebido", name="status_salario_enum"),
        nullable=False,
        default="Pendente",
        server_default="Pendente",
    )
    data_criacao = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    usuario = db.relationship(
        "Usuario", backref=db.backref("salario_movimentos", lazy=True)
    )
    itens = db.relationship(
        "SalarioMovimentoItem",
        backref="movimento_pai",
        lazy=True,
        cascade="all, delete-orphan",
    )
    movimento_bancario = db.relationship(
        "ContaMovimento",
        backref=db.backref("salario_movimento_associado", uselist=False),
        foreign_keys=[movimento_bancario_id],
    )

    __table_args__ = (
        UniqueConstraint(
            "usuario_id", "mes_referencia", name="_usuario_mes_referencia_uc"
        ),
    )

    def __repr__(self):
        return f"<SalarioMovimento Mês: {self.mes_referencia} | Status: {self.status}>"
