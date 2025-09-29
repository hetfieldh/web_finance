# app/models/salario_item_model.py

from datetime import datetime, timezone

from sqlalchemy import Enum, UniqueConstraint

from app import db
from app.utils import FormChoices


class SalarioItem(db.Model):
    __tablename__ = "salario_item"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    id_conta_destino = db.Column(db.Integer, db.ForeignKey("conta.id"), nullable=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(
        db.Enum(
            *(item.value for item in FormChoices.TipoSalarioItem),
            name="tipo_salario_item_enum",
        ),
        nullable=False,
    )
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    descricao = db.Column(db.String(255), nullable=True)
    data_criacao = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    usuario = db.relationship("Usuario", backref=db.backref("salario_itens", lazy=True))
    conta_destino = db.relationship(
        "Conta", backref=db.backref("salario_itens_destino", lazy=True)
    )

    __table_args__ = (
        UniqueConstraint("usuario_id", "nome", "tipo", name="_usuario_salario_item_uc"),
    )

    def __repr__(self):
        return f"<SalarioItem {self.nome} ({self.tipo})>"
