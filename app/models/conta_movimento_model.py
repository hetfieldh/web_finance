# app/models/conta_movimento_model.py

from app import db
from datetime import datetime, timezone
from sqlalchemy import Numeric


class ContaMovimento(db.Model):
    __tablename__ = "conta_movimento"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    conta_id = db.Column(db.Integer, db.ForeignKey("conta.id"), nullable=False)
    conta_transacao_id = db.Column(
        db.Integer, db.ForeignKey("conta_transacao.id"), nullable=False
    )

    data_movimento = db.Column(db.Date, nullable=False)
    valor = db.Column(Numeric(12, 2), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)

    id_movimento_relacionado = db.Column(
        db.Integer, db.ForeignKey("conta_movimento.id"), nullable=True
    )

    data_criacao = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    usuario = db.relationship("Usuario", backref=db.backref("movimentos", lazy=True))
    conta = db.relationship("Conta", backref=db.backref("movimentos", lazy=True))
    tipo_transacao = db.relationship(
        "ContaTransacao", backref=db.backref("movimentos", lazy=True)
    )

    movimento_relacionado = db.relationship(
        "ContaMovimento",
        remote_side=[id],
        backref=db.backref("movimentos_associados", lazy="dynamic"),
    )

    def __repr__(self):
        return f"<Movimento ID: {self.id} | Conta: {self.conta_id} | Valor: {self.valor} | Tipo: {self.tipo_transacao.transacao_tipo}>"
