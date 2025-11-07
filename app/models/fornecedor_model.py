# app/models/fornecedor_model.py

from datetime import datetime, timezone

from sqlalchemy import UniqueConstraint

from app import db


class Fornecedor(db.Model):
    __tablename__ = "fornecedor"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    data_criacao = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    usuario = db.relationship("Usuario", backref=db.backref("fornecedores", lazy=True))
    movimentos = db.relationship(
        "CrediarioMovimento", back_populates="fornecedor", lazy="dynamic"
    )

    __table_args__ = (
        UniqueConstraint(
            "usuario_id",
            "nome",
            name="_usuario_fornecedor_nome_uc",
        ),
    )

    def __repr__(self):
        return f"<Fornecedor {self.nome}>"
