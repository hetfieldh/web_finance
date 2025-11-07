# app/models/crediario_subgrupo_model.py

from datetime import datetime, timezone

from sqlalchemy import UniqueConstraint

from app import db


class CrediarioSubgrupo(db.Model):
    __tablename__ = "crediario_subgrupo"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    grupo_id = db.Column(
        db.Integer, db.ForeignKey("crediario_grupo.id"), nullable=False
    )
    nome = db.Column(db.String(100), nullable=False)
    data_criacao = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    usuario = db.relationship(
        "Usuario", backref=db.backref("crediario_subgrupos", lazy=True)
    )
    grupo = db.relationship("CrediarioGrupo", back_populates="subgrupos", lazy=True)

    __table_args__ = (
        UniqueConstraint(
            "usuario_id",
            "grupo_id",
            "nome",
            name="_usuario_grupo_subgrupo_nome_uc",
        ),
    )

    def __repr__(self):
        return f"<CrediarioSubgrupo {self.nome}>"
