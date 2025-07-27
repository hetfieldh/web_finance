# app/models/conta_movimento_model.py

from app import db
from datetime import datetime, timezone
from sqlalchemy import Numeric


class ContaMovimento(db.Model):
    # Define o nome da tabela no banco de dados
    __tablename__ = "conta_movimento"

    # Definição das colunas da tabela
    id = db.Column(db.Integer, primary_key=True)  # Chave primária, auto-incrementável
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuario.id"), nullable=False
    )  # Chave estrangeira para o usuário
    conta_id = db.Column(
        db.Integer, db.ForeignKey("conta.id"), nullable=False
    )  # Chave estrangeira para a conta bancária
    conta_transacao_id = db.Column(
        db.Integer, db.ForeignKey("conta_transacao.id"), nullable=False
    )  # Chave estrangeira para o tipo de transação

    data_movimento = db.Column(
        db.Date, nullable=False
    )  # Data em que a movimentação ocorreu
    valor = db.Column(Numeric(12, 2), nullable=False)  # Valor da movimentação
    descricao = db.Column(
        db.String(255), nullable=True
    )  # Descrição detalhada da movimentação (opcional)

    # Campo para relacionar movimentos de transferência (chave estrangeira auto-referenciada)
    id_movimento_relacionado = db.Column(
        db.Integer, db.ForeignKey("conta_movimento.id"), nullable=True
    )

    data_criacao = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )  # Data de criação do registro

    # Relacionamentos
    usuario = db.relationship("Usuario", backref=db.backref("movimentos", lazy=True))
    conta = db.relationship("Conta", backref=db.backref("movimentos", lazy=True))
    tipo_transacao = db.relationship(
        "ContaTransacao", backref=db.backref("movimentos", lazy=True)
    )

    # Relacionamento auto-referenciado para transferências
    movimento_relacionado = db.relationship(
        "ContaMovimento",
        remote_side=[
            id
        ],  # Indica que 'id' é o lado remoto (o que está sendo referenciado)
        backref=db.backref("movimentos_associados", lazy="dynamic"),
    )

    def __repr__(self):
        return f"<Movimento ID: {self.id} | Conta: {self.conta_id} | Valor: {self.valor} | Tipo: {self.tipo_transacao.transacao_tipo}>"
