# app/models/financiamento_model.py

from datetime import date, datetime, timezone

from sqlalchemy import Enum, Numeric, UniqueConstraint

from app import db
from app.utils import FormChoices


class Financiamento(db.Model):
    __tablename__ = "financiamento"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    conta_id = db.Column(db.Integer, db.ForeignKey("conta.id"), nullable=False)
    nome_financiamento = db.Column(db.String(100), nullable=False)
    valor_total_financiado = db.Column(Numeric(12, 2), nullable=False)
    saldo_devedor_atual = db.Column(Numeric(12, 2), nullable=False)
    taxa_juros_anual = db.Column(Numeric(5, 4), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    prazo_meses = db.Column(db.Integer, nullable=False)
    tipo_amortizacao = db.Column(
        db.Enum(
            *(item.value for item in FormChoices.TipoAmortizacao),
            name="tipo_amortizacao_enum",
        ),
        nullable=False,
    )
    data_criacao = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    descricao = db.Column(db.String(255), nullable=True)

    usuario = db.relationship(
        "Usuario", backref=db.backref("financiamentos", lazy=True)
    )
    conta = db.relationship("Conta", backref=db.backref("financiamentos", lazy=True))

    __table_args__ = (
        UniqueConstraint(
            "usuario_id", "nome_financiamento", name="_usuario_financiamento_uc"
        ),
    )

    def __repr__(self):
        return f"<Financiamento {self.nome_financiamento} ({self.tipo_amortizacao})>"
