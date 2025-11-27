# app/models/crediario_movimento_model.py

from datetime import date, datetime, timezone

from sqlalchemy import Enum, Numeric

from app import db
from app.models.crediario_subgrupo_model import CrediarioSubgrupo
from app.models.fornecedor_model import Fornecedor
from app.utils import FormChoices


class CrediarioMovimento(db.Model):
    __tablename__ = "crediario_movimento"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    crediario_id = db.Column(db.Integer, db.ForeignKey("crediario.id"), nullable=False)
    crediario_grupo_id = db.Column(
        db.Integer, db.ForeignKey("crediario_grupo.id"), nullable=True
    )
    crediario_subgrupo_id = db.Column(
        db.Integer, db.ForeignKey("crediario_subgrupo.id"), nullable=True
    )
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("fornecedor.id"), nullable=True)
    data_compra = db.Column(db.Date, nullable=False)
    valor_total_compra = db.Column(Numeric(12, 2), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    destino = db.Column(
        db.Enum(
            *(item.value for item in FormChoices.DestinoCrediario),
            name="destino_crediario_enum",
        ),
        nullable=False,
        server_default=FormChoices.DestinoCrediario.PROPRIO.value,
    )
    data_primeira_parcela = db.Column(db.Date, nullable=False)
    numero_parcelas = db.Column(db.Integer, nullable=False, default=1)
    data_criacao = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    usuario = db.relationship(
        "Usuario", backref=db.backref("crediario_movimentos", lazy=True)
    )
    crediario = db.relationship(
        "Crediario", backref=db.backref("movimentos_crediario", lazy=True)
    )
    crediario_grupo = db.relationship(
        "CrediarioGrupo", backref=db.backref("movimentos_grupo", lazy=True)
    )
    crediario_subgrupo = db.relationship(
        "CrediarioSubgrupo", backref=db.backref("movimentos_subgrupo", lazy=True)
    )
    fornecedor = db.relationship("Fornecedor", back_populates="movimentos", lazy=True)
    parcelas = db.relationship(
        "CrediarioParcela",
        back_populates="movimento_pai",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<CrediarioMovimento {self.descricao} | {self.valor_total_compra} | {self.numero_parcelas}x>"
