# app/models/crediario_movimento_model.py

from datetime import date, datetime, timezone

from sqlalchemy import Numeric

from app import db


class CrediarioMovimento(db.Model):
    __tablename__ = "crediario_movimento"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    crediario_id = db.Column(db.Integer, db.ForeignKey("crediario.id"), nullable=False)
    crediario_grupo_id = db.Column(
        db.Integer, db.ForeignKey("crediario_grupo.id"), nullable=True
    )

    data_compra = db.Column(db.Date, nullable=False)
    valor_total_compra = db.Column(Numeric(12, 2), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    numero_parcelas = db.Column(db.Integer, nullable=False, default=1)

    data_criacao = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    usuario = db.relationship(
        "Usuario", backref=db.backref("crediario_movimentos", lazy=True)
    )
    crediario = db.relationship(
        "Crediario", backref=db.backref("movimentos", lazy=True)
    )
    crediario_grupo = db.relationship(
        "CrediarioGrupo", backref=db.backref("movimentos", lazy=True)
    )

    # NOVO: Relacionamento com CrediarioParcela com cascade delete
    # Renomeado o backref para 'movimento_pai' para evitar conflito
    parcelas = db.relationship(
        "CrediarioParcela",
        backref="movimento_pai",  # AJUSTADO: backref renomeado
        lazy=True,
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<CrediarioMovimento {self.descricao} | R$ {self.valor_total_compra} | {self.numero_parcelas}x>"
