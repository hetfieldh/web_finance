# app/routes/conta_movimento_routes.py

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from decimal import Decimal, getcontext

getcontext().prec = 10

from app import db
from app.models.conta_movimento_model import ContaMovimento
from app.models.conta_model import Conta
from app.models.conta_transacao_model import ContaTransacao
from app.forms.conta_movimento_forms import (
    CadastroContaMovimentoForm,
    EditarContaMovimentoForm,
)

conta_movimento_bp = Blueprint("conta_movimento", __name__, url_prefix="/movimentacoes")


# Listagem de movimentações
@conta_movimento_bp.route("/")
@login_required
def listar_movimentacoes():
    movimentacoes = (
        ContaMovimento.query.filter_by(usuario_id=current_user.id)
        .order_by(ContaMovimento.data_movimento.desc())
        .all()
    )
    return render_template("conta_movimentos/list.html", movimentacoes=movimentacoes)


# Adicionar nova movimentação
@conta_movimento_bp.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_movimentacao():
    form = CadastroContaMovimentoForm()

    if form.validate_on_submit():
        conta_origem_id = form.conta_id.data
        tipo_transacao_id = form.conta_transacao_id.data
        data_movimento = form.data_movimento.data
        valor = form.valor.data
        descricao = form.descricao.data.strip() if form.descricao.data else None
        is_transferencia = form.is_transferencia.data
        conta_destino_id = form.conta_destino_id.data if is_transferencia else None

        # Recarrega a conta para garantir o estado mais recente do DB
        conta_origem = db.session.query(Conta).get(conta_origem_id)
        tipo_transacao = ContaTransacao.query.get(tipo_transacao_id)
        conta_destino = Conta.query.get(conta_destino_id) if is_transferencia else None

        if not conta_origem or not tipo_transacao:
            flash("Erro: Conta ou Tipo de Transação inválidos.", "danger")
            return render_template("conta_movimentos/add.html", form=form)

        # Validação de valor
        if valor <= 0:
            flash("O valor da movimentação deve ser maior que zero.", "danger")
            return render_template("conta_movimentos/add.html", form=form)

        valor_decimal = Decimal(str(valor))
        # Garante que saldo_atual é um Decimal antes de qualquer operação
        saldo_origem_decimal = Decimal(str(conta_origem.saldo_atual))

        # Validação de débito e limite
        if tipo_transacao.tipo == "Débito":
            tipos_com_limite = ["Corrente", "Digital"]
            if saldo_origem_decimal < valor_decimal:
                if conta_origem.tipo in tipos_com_limite and conta_origem.limite:
                    limite_decimal = Decimal(str(conta_origem.limite))
                    if (saldo_origem_decimal + limite_decimal) < valor_decimal:
                        flash("Saldo e limite insuficientes.", "danger")
                        return render_template("conta_movimentos/add.html", form=form)
                    else:
                        flash(
                            f"Atenção: será utilizado R$ {(valor_decimal - saldo_origem_decimal):.2f} do seu limite.",
                            "warning",
                        )
                else:
                    flash("Saldo insuficiente para a movimentação.", "danger")
                    return render_template("conta_movimentos/add.html", form=form)

        # Validação de transferência
        if is_transferencia:
            if not conta_destino:
                flash("Conta de destino inválida.", "danger")
                return render_template("conta_movimentos/add.html", form=form)

            if conta_origem.id == conta_destino.id:
                flash("A conta de origem e destino devem ser diferentes.", "danger")
                return render_template("conta_movimentos/add.html", form=form)

            if tipo_transacao.tipo != "Débito":
                flash(
                    'Em transferências, a transação de origem deve ser do tipo "Débito".',
                    "danger",
                )
                return render_template("conta_movimentos/add.html", form=form)

            tipo_transacao_credito = ContaTransacao.query.filter_by(
                usuario_id=current_user.id,
                transacao_tipo=tipo_transacao.transacao_tipo,
                tipo="Crédito",
            ).first()

            if not tipo_transacao_credito:
                flash(
                    f'Não foi encontrado o tipo de transação "{tipo_transacao.transacao_tipo}" do tipo "Crédito" na conta de destino.',
                    "danger",
                )
                return render_template("conta_movimentos/add.html", form=form)

        try:
            # Criação da movimentação de origem
            movimento_origem = ContaMovimento(
                usuario_id=current_user.id,
                conta_id=conta_origem_id,
                conta_transacao_id=tipo_transacao_id,
                data_movimento=data_movimento,
                valor=valor,
                descricao=descricao,
            )
            db.session.add(movimento_origem)
            db.session.flush()  # Força o ID para o movimento de origem

            # Atualização do saldo da conta de origem
            # Garante que a operação é feita com Decimal a partir do valor DO BANCO DE DADOS
            # Recarrega o saldo_atual da conta_origem do DB novamente antes de operar
            db.session.refresh(conta_origem)  # NOVO: Recarrega o objeto do DB
            saldo_origem_atualizado = Decimal(
                str(conta_origem.saldo_atual)
            )  # NOVO: Usa o valor recarregado

            if tipo_transacao.tipo == "Débito":
                conta_origem.saldo_atual = saldo_origem_atualizado - valor_decimal
            elif tipo_transacao.tipo == "Crédito":
                conta_origem.saldo_atual = saldo_origem_atualizado + valor_decimal
            else:
                # Caso um tipo inesperado passe, o que não deveria ocorrer com ENUM
                pass

            # Transferência: movimentação na conta de destino
            if is_transferencia:
                # Recarrega a conta de destino para garantir o estado mais recente do DB
                db.session.refresh(conta_destino)  # NOVO: Recarrega o objeto do DB
                saldo_destino_atualizado = Decimal(
                    str(conta_destino.saldo_atual)
                )  # NOVO: Usa o valor recarregado

                movimento_destino = ContaMovimento(
                    usuario_id=current_user.id,
                    conta_id=conta_destino_id,
                    conta_transacao_id=tipo_transacao_credito.id,
                    data_movimento=data_movimento,
                    valor=valor,
                    descricao=f"Transferência recebida de {conta_origem.nome_banco} - {conta_origem.conta}",
                )
                db.session.add(movimento_destino)
                db.session.flush()

                conta_destino.saldo_atual = saldo_destino_atualizado + valor_decimal

                # Vincular os dois movimentos
                movimento_origem.id_movimento_relacionado = movimento_destino.id
                movimento_destino.id_movimento_relacionado = movimento_origem.id

            db.session.commit()
            flash("Movimentação registrada com sucesso!", "success")
            current_app.logger.info(
                f"Movimentação {tipo_transacao.tipo} de R$ {valor:.2f} registrada por {current_user.login}."
            )
            return redirect(url_for("conta_movimento.listar_movimentacoes"))

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Erro de integridade: {e}", exc_info=True)
            flash("Erro ao registrar movimentação. Verifique os dados.", "danger")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro inesperado: {e}", exc_info=True)
            flash("Erro inesperado. Tente novamente.", "danger")

    return render_template("conta_movimentos/add.html", form=form)


# Edição de movimentação (sem ajuste de saldo)
@conta_movimento_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_movimentacao(id):
    movimento = ContaMovimento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    form = EditarContaMovimentoForm()

    if form.validate_on_submit():
        # Obs: não atualiza valor, tipo ou conta — apenas descrição
        movimento.descricao = (
            form.descricao.data.strip() if form.descricao.data else None
        )

        db.session.commit()
        flash("Movimentação atualizada com sucesso!", "success")
        current_app.logger.info(
            f"Movimentação {movimento.id} editada por {current_user.login}."
        )
        return redirect(url_for("conta_movimento.listar_movimentacoes"))

    elif request.method == "GET":
        form.conta_id.data = movimento.conta_id
        form.conta_transacao_id.data = movimento.conta_transacao_id
        form.data_movimento.data = movimento.data_movimento
        form.valor.data = movimento.valor
        form.descricao.data = movimento.descricao

    return render_template("conta_movimentos/edit.html", form=form, movimento=movimento)


# Exclusão de movimentação
@conta_movimento_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_movimentacao(id):
    movimento = ContaMovimento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    conta_afetada = Conta.query.get(movimento.conta_id)
    tipo_transacao = ContaTransacao.query.get(movimento.conta_transacao_id)

    if conta_afetada and tipo_transacao:
        conta_afetada.saldo_atual = Decimal(str(conta_afetada.saldo_atual))
        valor_decimal = Decimal(str(movimento.valor))

        if tipo_transacao.tipo == "Débito":
            conta_afetada.saldo_atual += valor_decimal
        else:  # Crédito
            conta_afetada.saldo_atual -= valor_decimal

    # Remoção de transferência relacionada, se houver
    if movimento.id_movimento_relacionado:
        movimento_relacionado = ContaMovimento.query.get(
            movimento.id_movimento_relacionado
        )
        if movimento_relacionado:
            conta_destino = Conta.query.get(movimento_relacionado.conta_id)
            tipo_destino = ContaTransacao.query.get(
                movimento_relacionado.conta_transacao_id
            )

            if conta_destino and tipo_destino:
                conta_destino.saldo_atual = Decimal(str(conta_destino.saldo_atual))
                valor_rel = Decimal(str(movimento_relacionado.valor))

                if tipo_destino.tipo == "Crédito":
                    conta_destino.saldo_atual -= valor_rel
                else:
                    conta_destino.saldo_atual += valor_rel

            # Remover relação circular antes de excluir
            movimento.id_movimento_relacionado = None
            movimento_relacionado.id_movimento_relacionado = None
            db.session.add(movimento)
            db.session.add(movimento_relacionado)
            db.session.flush()

            db.session.delete(movimento_relacionado)

    db.session.delete(movimento)
    db.session.commit()
    flash("Movimentação excluída com sucesso!", "success")
    current_app.logger.info(
        f"Movimentação {movimento.id} excluída por {current_user.login}."
    )
    return redirect(url_for("conta_movimento.listar_movimentacoes"))
