# app/models/salario_movimento_item_model.py

from sqlalchemy import Numeric

from app import db


class SalarioMovimentoItem(db.Model):
    __tablename__ = "salario_movimento_item"

    id = db.Column(db.Integer, primary_key=True)
    salario_movimento_id = db.Column(
        db.Integer, db.ForeignKey("salario_movimento.id"), nullable=False
    )
    salario_item_id = db.Column(
        db.Integer, db.ForeignKey("salario_item.id"), nullable=False
    )
    valor = db.Column(Numeric(12, 2), nullable=False)

    salario_item = db.relationship("SalarioItem")

    def __repr__(self):
        return f"<SalarioMovimentoItem ID: {self.id} | Valor: {self.valor}>"
