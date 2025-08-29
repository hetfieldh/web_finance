# app/models/crediario_grupo_model.py

from datetime import datetime, timezone

from sqlalchemy import Enum, UniqueConstraint

from app import db
from app.utils import FormChoices


class CrediarioGrupo(db.Model):
    __tablename__ = "crediario_grupo"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    grupo_crediario = db.Column(db.String(100), nullable=False)
    tipo_grupo_crediario = db.Column(
        db.Enum(
            *(item.value for item in FormChoices.TiposCrediarioGrupo),
            name="tipo_grupo_crediario_enum",
        ),
        nullable=False,
    )
    data_criacao = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    descricao = db.Column(db.String(255), nullable=True)

    usuario = db.relationship(
        "Usuario", backref=db.backref("crediario_grupos", lazy=True)
    )

    __table_args__ = (
        UniqueConstraint(
            "usuario_id",
            "grupo_crediario",
            "tipo_grupo_crediario",
            name="_usuario_grupo_crediario_uc",
        ),
    )

    def __repr__(self):
        return f"<CrediarioGrupo {self.grupo_crediario} ({self.tipo_grupo_crediario})>"
