# app/routes/financiamento_routes.py

import functools
import re
from datetime import datetime
from decimal import Decimal

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import asc, desc
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash

from app import db
from app.forms.financiamento_forms import (
    AmortizacaoForm,
    CadastroFinanciamentoForm,
    EditarFinanciamentoForm,
    ImportarParcelasForm,
)
from app.models.conta_movimento_model import ContaMovimento
from app.models.financiamento_model import Financiamento
from app.models.financiamento_parcela_model import FinanciamentoParcela
from app.services import conta_service
from app.services.financiamento_service import (
    amortizar_parcelas,
    importar_e_processar_csv,
)

financiamento_bp = Blueprint("financiamento", __name__, url_prefix="/financiamentos")


@financiamento_bp.route("/")
@login_required
def listar_financiamentos():
    financiamentos = (
        Financiamento.query.filter_by(usuario_id=current_user.id)
        .options(joinedload(Financiamento.conta))
        .order_by(Financiamento.data_inicio.desc())
        .all()
    )
    return render_template("financiamentos/list.html", financiamentos=financiamentos)


@financiamento_bp.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_financiamento():
    account_choices = conta_service.get_active_accounts_for_user_choices_simple()
    form = CadastroFinanciamentoForm(account_choices=account_choices)
    if form.validate_on_submit():
        novo_financiamento = Financiamento(
            usuario_id=current_user.id,
            conta_id=form.conta_id.data,
            nome_financiamento=form.nome_financiamento.data.strip().upper(),
            valor_total_financiado=form.valor_total_financiado.data,
            saldo_devedor_atual=form.valor_total_financiado.data,
            taxa_juros_anual=form.taxa_juros_anual.data,
            data_inicio=form.data_inicio.data,
            prazo_meses=form.prazo_meses.data,
            tipo_amortizacao=form.tipo_amortizacao.data,
            descricao=form.descricao.data.strip() if form.descricao.data else None,
        )
        db.session.add(novo_financiamento)
        db.session.commit()
        flash(
            "Financiamento principal criado com sucesso! Agora, importe o arquivo .csv com as parcelas.",
            "success",
        )
        return redirect(
            url_for("financiamento.importar_parcelas", id=novo_financiamento.id)
        )
    return render_template("financiamentos/add.html", form=form)


@financiamento_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_financiamento(id):
    financiamento = Financiamento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()
    if any(p.status == "Paga" for p in financiamento.parcelas):
        flash(
            "Não é possível editar um financiamento que já possui parcelas pagas.",
            "danger",
        )
        return redirect(url_for("financiamento.listar_financiamentos"))
    account_choices = conta_service.get_active_accounts_for_user_choices_simple()
    form = EditarFinanciamentoForm(
        obj=financiamento,
        original_nome_financiamento=financiamento.nome_financiamento,
        account_choices=account_choices,
    )
    if form.validate_on_submit():
        financiamento.descricao = (
            form.descricao.data.strip() if form.descricao.data else None
        )
        db.session.commit()
        flash("Financiamento atualizado com sucesso!", "success")
        return redirect(url_for("financiamento.listar_financiamentos"))
    return render_template(
        "financiamentos/edit.html", form=form, financiamento=financiamento
    )


@financiamento_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_financiamento(id):
    financiamento = Financiamento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()
    if any(p.status == "Paga" for p in financiamento.parcelas):
        flash(
            "Não é possível excluir um financiamento que já possui parcelas pagas.",
            "danger",
        )
        return redirect(url_for("financiamento.listar_financiamentos"))
    db.session.delete(financiamento)
    db.session.commit()
    flash("Financiamento excluído com sucesso!", "success")
    return redirect(url_for("financiamento.listar_financiamentos"))


@financiamento_bp.route("/<int:id>/importar", methods=["GET", "POST"])
@login_required
def importar_parcelas(id):
    financiamento = Financiamento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()
    form = ImportarParcelasForm()

    if form.validate_on_submit():
        csv_file = form.csv_file.data
        success, message = importar_e_processar_csv(financiamento, csv_file)

        if success:
            flash(message, "success")
            return redirect(url_for("financiamento.listar_financiamentos"))
        else:
            flash(message, "danger")
            return redirect(url_for("financiamento.importar_parcelas", id=id))

    return render_template(
        "financiamentos/importar_parcelas.html", form=form, financiamento=financiamento
    )


@financiamento_bp.route("/<int:id>/parcelas")
@login_required
def visualizar_parcelas(id):
    financiamento = Financiamento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()
    parcelas_data = (
        db.session.query(FinanciamentoParcela, ContaMovimento.valor)
        .outerjoin(
            ContaMovimento,
            FinanciamentoParcela.movimento_bancario_id == ContaMovimento.id,
        )
        .filter(FinanciamentoParcela.financiamento_id == id)
        .options(joinedload(FinanciamentoParcela.financiamento))
        .order_by(FinanciamentoParcela.numero_parcela.asc())
        .all()
    )
    return render_template(
        "financiamentos/parcelas.html",
        financiamento=financiamento,
        parcelas_data=parcelas_data,
    )


@financiamento_bp.route("/amortizar/<int:id>", methods=["GET", "POST"])
@login_required
def amortizar_financiamento(id):
    financiamento = Financiamento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()
    account_choices_with_balance = conta_service.get_active_accounts_for_user_choices()

    form = AmortizacaoForm(
        request.form, account_choices_with_balance=account_choices_with_balance
    )

    if request.method == "POST":
        ids_parcelas_selecionadas = request.form.getlist(
            "parcelas_selecionadas", type=int
        )

        if not ids_parcelas_selecionadas:
            flash("Selecione pelo menos uma parcela para amortizar.", "danger")
        elif form.validate():
            success, message = amortizar_parcelas(
                financiamento, form, ids_parcelas_selecionadas
            )
            if success:
                flash(message, "success")
                return redirect(url_for("financiamento.listar_financiamentos"))
            else:
                flash(message, "danger")
        elif form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(
                        f"Erro no campo '{getattr(form, field).label.text}': {error}",
                        "danger",
                    )

    parcelas_pendentes = (
        FinanciamentoParcela.query.filter(
            FinanciamentoParcela.financiamento_id == id,
            FinanciamentoParcela.status == "Pendente",
        )
        .order_by(FinanciamentoParcela.numero_parcela.desc())
        .all()
    )

    return render_template(
        "financiamentos/amortizar.html",
        form=form,
        financiamento=financiamento,
        parcelas=parcelas_pendentes,
    )
