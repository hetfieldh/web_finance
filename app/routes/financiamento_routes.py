# app/routes/financiamento_routes.py

import math
from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app import db
from app.forms.financiamento_forms import (
    CadastroFinanciamentoForm,
    EditarFinanciamentoForm,
)
from app.models.conta_model import Conta
from app.models.financiamento_model import Financiamento
from app.models.financiamento_parcela_model import FinanciamentoParcela

financiamento_bp = Blueprint("financiamento", __name__, url_prefix="/financiamentos")


@financiamento_bp.route("/")
@login_required
def listar_financiamentos():
    financiamentos = (
        Financiamento.query.filter_by(usuario_id=current_user.id)
        .order_by(Financiamento.data_inicio.desc())
        .all()
    )
    return render_template("financiamentos/list.html", financiamentos=financiamentos)


@financiamento_bp.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_financiamento():
    form = CadastroFinanciamentoForm()

    if form.validate_on_submit():
        nome_financiamento = form.nome_financiamento.data.strip()
        conta_id = form.conta_id.data
        valor_total_financiado = form.valor_total_financiado.data
        taxa_juros_anual = form.taxa_juros_anual.data
        data_inicio = form.data_inicio.data
        prazo_meses = form.prazo_meses.data
        tipo_amortizacao = form.tipo_amortizacao.data
        descricao = form.descricao.data.strip() if form.descricao.data else None

        try:
            # 1. Cria o financiamento principal
            novo_financiamento = Financiamento(
                usuario_id=current_user.id,
                conta_id=conta_id,
                nome_financiamento=nome_financiamento,
                valor_total_financiado=valor_total_financiado,
                saldo_devedor_atual=valor_total_financiado,  # Saldo devedor inicial
                taxa_juros_anual=taxa_juros_anual,
                data_inicio=data_inicio,
                prazo_meses=prazo_meses,
                tipo_amortizacao=tipo_amortizacao,
                descricao=descricao,
            )
            db.session.add(novo_financiamento)
            db.session.flush()  # Força o ID para o novo_financiamento

            # 2. Geração da tabela de amortização (parcelas)
            taxa_juros_mensal = taxa_juros_anual / Decimal(
                "1200"
            )  # Converte % anual para decimal mensal

            if tipo_amortizacao == "PRICE":
                # Lógica de amortização PRICE
                if taxa_juros_mensal > 0:
                    parcela_fixa = valor_total_financiado * (
                        taxa_juros_mensal
                        / (
                            Decimal("1")
                            - (Decimal("1") + taxa_juros_mensal) ** -prazo_meses
                        )
                    )
                else:
                    parcela_fixa = valor_total_financiado / Decimal(str(prazo_meses))

                saldo_devedor = valor_total_financiado
                for i in range(prazo_meses):
                    juros_parcela = saldo_devedor * taxa_juros_mensal
                    amortizacao_principal = parcela_fixa - juros_parcela
                    saldo_devedor -= amortizacao_principal

                    nova_parcela = FinanciamentoParcela(
                        financiamento_id=novo_financiamento.id,
                        numero_parcela=i + 1,
                        valor_principal=amortizacao_principal,
                        valor_juros=juros_parcela,
                        valor_total_previsto=parcela_fixa,
                        data_vencimento=data_inicio + relativedelta(months=i + 1),
                    )
                    db.session.add(nova_parcela)

            elif tipo_amortizacao == "SAC":
                # Lógica de amortização SAC
                amortizacao_principal = valor_total_financiado / Decimal(
                    str(prazo_meses)
                )
                saldo_devedor = valor_total_financiado
                for i in range(prazo_meses):
                    juros_parcela = saldo_devedor * taxa_juros_mensal
                    valor_total_previsto = amortizacao_principal + juros_parcela
                    saldo_devedor -= amortizacao_principal

                    nova_parcela = FinanciamentoParcela(
                        financiamento_id=novo_financiamento.id,
                        numero_parcela=i + 1,
                        valor_principal=amortizacao_principal,
                        valor_juros=juros_parcela,
                        valor_total_previsto=valor_total_previsto,
                        data_vencimento=data_inicio + relativedelta(months=i + 1),
                    )
                    db.session.add(nova_parcela)

            else:  # Outro tipo de amortização
                # Por simplicidade, dividimos o valor total igualmente.
                valor_por_parcela = valor_total_financiado / Decimal(str(prazo_meses))
                for i in range(prazo_meses):
                    nova_parcela = FinanciamentoParcela(
                        financiamento_id=novo_financiamento.id,
                        numero_parcela=i + 1,
                        valor_principal=valor_por_parcela,
                        valor_juros=Decimal("0.00"),
                        valor_total_previsto=valor_por_parcela,
                        data_vencimento=data_inicio + relativedelta(months=i + 1),
                    )
                    db.session.add(nova_parcela)

            db.session.commit()
            flash("Financiamento adicionado e parcelas geradas com sucesso!", "success")
            current_app.logger.info(
                f'Financiamento "{nome_financiamento}" (ID: {novo_financiamento.id}) adicionado por {current_user.login}.'
            )
            return redirect(url_for("financiamento.listar_financiamentos"))

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(
                f"Erro de integridade ao adicionar financiamento: {e}", exc_info=True
            )
            flash(
                "Erro ao adicionar financiamento. Verifique se o nome já não existe.",
                "danger",
            )
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Erro inesperado ao adicionar financiamento: {e}", exc_info=True
            )
            flash("Ocorreu um erro inesperado. Tente novamente.", "danger")

    return render_template("financiamentos/add.html", form=form)


@financiamento_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_financiamento(id):
    financiamento = Financiamento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    if any(p.pago for p in financiamento.parcelas):
        flash(
            "Não é possível editar um financiamento que já possui parcelas pagas.",
            "danger",
        )
        return redirect(url_for("financiamento.listar_financiamentos"))

    # CORRIGIDO: Passa o original_nome_financiamento ao inicializar o formulário
    form = EditarFinanciamentoForm(
        obj=financiamento, original_nome_financiamento=financiamento.nome_financiamento
    )

    if form.validate_on_submit():
        financiamento.descricao = (
            form.descricao.data.strip() if form.descricao.data else None
        )

        try:
            db.session.commit()
            flash("Financiamento atualizado com sucesso!", "success")
            current_app.logger.info(
                f"Financiamento (ID: {financiamento.id}) atualizado por {current_user.login}."
            )
            return redirect(url_for("financiamento.listar_financiamentos"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Erro ao salvar atualização de financiamento: {e}", exc_info=True
            )
            flash(
                "Ocorreu um erro ao atualizar o financiamento. Tente novamente.",
                "danger",
            )
            return render_template(
                "financiamentos/edit.html", form=form, financiamento=financiamento
            )

    elif request.method == "GET":
        pass

    return render_template(
        "financiamentos/edit.html", form=form, financiamento=financiamento
    )


@financiamento_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_financiamento(id):
    financiamento = Financiamento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    if any(p.pago for p in financiamento.parcelas):
        flash(
            "Não é possível excluir um financiamento que já possui parcelas pagas.",
            "danger",
        )
        return redirect(url_for("financiamento.listar_financiamentos"))

    db.session.delete(financiamento)
    db.session.commit()
    flash("Financiamento excluído com sucesso!", "success")
    current_app.logger.info(
        f"Financiamento (ID: {financiamento.id}) excluído por {current_user.login}."
    )
    return redirect(url_for("financiamento.listar_financiamentos"))
