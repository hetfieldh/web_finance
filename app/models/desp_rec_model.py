# app/models/desp_rec_model.py

from datetime import datetime, timezone

from sqlalchemy import Enum, UniqueConstraint

from app import db
from app.utils import FormChoices


class DespRec(db.Model):
    __tablename__ = "desp_rec"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    natureza = db.Column(
        db.Enum(
            *(item.value for item in FormChoices.NaturezaDespRec), name="natureza_enum"
        ),
        nullable=False,
    )
    tipo = db.Column(
        db.Enum(
            *(item.value for item in FormChoices.TipoCadastroDespRec),
            name="tipo_desp_rec_enum",
        ),
        nullable=False,
    )
    dia_vencimento = db.Column(db.Integer, nullable=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    data_criacao = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    usuario = db.relationship(
        "Usuario", backref=db.backref("despesas_receitas", lazy=True)
    )

    __table_args__ = (
        UniqueConstraint(
            "usuario_id", "nome", "natureza", "tipo", name="_usuario_desp_rec_uc"
        ),
    )

    def __repr__(self):
        return f"<DespRec {self.nome} ({self.natureza} - {self.tipo})>"
