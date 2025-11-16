# app/routes/financiamento_routes.py

import functools
import re
from datetime import date, datetime
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
from app.utils import STATUS_AMORTIZADO, STATUS_ATRASADO, STATUS_PAGO, STATUS_PENDENTE

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

    has_paid_installments = any(p.status == STATUS_PAGO for p in financiamento.parcelas)

    account_choices = conta_service.get_active_accounts_for_user_choices_simple()
    form = EditarFinanciamentoForm(
        obj=financiamento,
        original_nome_financiamento=financiamento.nome_financiamento,
        account_choices=account_choices,
    )

    if has_paid_installments:
        form.nome_financiamento.render_kw = {"readonly": True}
        form.conta_id.render_kw = {"disabled": True}
        form.taxa_juros_anual.render_kw = {"readonly": True}
        form.data_inicio.render_kw = {"readonly": True}
        form.prazo_meses.render_kw = {"readonly": True}
        form.tipo_amortizacao.render_kw = {"disabled": True}

    if form.validate_on_submit():
        financiamento.descricao = (
            form.descricao.data.strip() if form.descricao.data else None
        )
        db.session.commit()
        flash("Financiamento atualizado com sucesso!", "success")
        return redirect(url_for("financiamento.listar_financiamentos"))

    return render_template(
        "financiamentos/edit.html",
        form=form,
        financiamento=financiamento,
        has_paid_installments=has_paid_installments,
    )


@financiamento_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_financiamento(id):
    financiamento = Financiamento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()
    if any(p.status == STATUS_PAGO for p in financiamento.parcelas):
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
    parcelas = (
        FinanciamentoParcela.query.filter(FinanciamentoParcela.financiamento_id == id)
        .order_by(FinanciamentoParcela.numero_parcela.asc())
        .all()
    )
    resumo_fluxo_caixa = {
        "total_previsto": Decimal("0.00"),
        "Pago": Decimal("0.00"),
        "Amortizado": Decimal("0.00"),
        "Pendente": Decimal("0.00"),
    }
    resumo_principal = {
        "total_contrato": financiamento.valor_total_financiado,
        "Pago": Decimal("0.00"),
        "Amortizado": Decimal("0.00"),
        "Pendente": Decimal("0.00"),
        "saldo_devedor": financiamento.saldo_devedor_atual,
    }

    hoje = date.today()
    for p in parcelas:
        resumo_fluxo_caixa["total_previsto"] += p.valor_total_previsto
        if p.status == STATUS_PAGO:
            resumo_fluxo_caixa[STATUS_PAGO] += p.valor_pago or Decimal("0.00")
        elif p.status == STATUS_AMORTIZADO:
            resumo_fluxo_caixa[STATUS_AMORTIZADO] += p.valor_pago or Decimal("0.00")
        elif p.status in [STATUS_PENDENTE, STATUS_ATRASADO]:
            resumo_fluxo_caixa[STATUS_PENDENTE] += p.valor_total_previsto

        if p.status == STATUS_PAGO:
            resumo_principal[STATUS_PAGO] += p.valor_principal
        elif p.status == STATUS_AMORTIZADO:
            resumo_principal[STATUS_AMORTIZADO] += p.valor_principal
        elif p.status == STATUS_ATRASADO or (
            p.status == STATUS_PENDENTE and p.data_vencimento < hoje
        ):
            resumo_principal[STATUS_PENDENTE] += p.valor_principal
            if "atrasado_valor" not in resumo_principal:
                resumo_principal["atrasado_valor"] = Decimal("0.00")
            if "atrasado_qtd" not in resumo_principal:
                resumo_principal["atrasado_qtd"] = 0
            resumo_principal["atrasado_valor"] += p.valor_principal
            resumo_principal["atrasado_qtd"] += 1

        elif p.status == STATUS_PENDENTE:
            resumo_principal[STATUS_PENDENTE] += p.valor_principal

    resumo_fluxo_caixa["diferenca"] = resumo_fluxo_caixa["total_previsto"] - (
        resumo_fluxo_caixa[STATUS_PAGO]
        + resumo_fluxo_caixa[STATUS_AMORTIZADO]
        + resumo_fluxo_caixa[STATUS_PENDENTE]
    )

    parcelas_com_saldo_dinamico = []
    saldo_devedor_corrente = financiamento.saldo_devedor_atual

    for parcela in parcelas:
        saldo_para_exibir = Decimal("0.00")
        if parcela.status in [STATUS_PENDENTE, STATUS_ATRASADO]:
            saldo_para_exibir = saldo_devedor_corrente
            saldo_devedor_corrente -= parcela.valor_principal
        parcelas_com_saldo_dinamico.append(
            {"parcela": parcela, "saldo_devedor_dinamico": saldo_para_exibir}
        )

    return render_template(
        "financiamentos/parcelas.html",
        financiamento=financiamento,
        resumo_fluxo_caixa=resumo_fluxo_caixa,
        resumo_principal=resumo_principal,
        parcelas_com_saldo_dinamico=parcelas_com_saldo_dinamico,
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

    if form.validate_on_submit():
        success, message = amortizar_parcelas(financiamento, form)
        if success:
            flash(message, "success")
            return redirect(url_for("financiamento.listar_financiamentos"))
        else:
            flash(message, "danger")
    elif request.method == "POST" and form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(
                    f"Erro no campo '{getattr(form, field).label.text}': {error}",
                    "danger",
                )

    parcelas_prazo = (
        FinanciamentoParcela.query.filter(
            FinanciamentoParcela.financiamento_id == id,
            FinanciamentoParcela.status.in_([STATUS_PENDENTE, STATUS_ATRASADO]),
        )
        .order_by(FinanciamentoParcela.numero_parcela.desc())
        .all()
    )
    parcelas_json_prazo = [
        {
            "numero_parcela": p.numero_parcela,
            "valor_principal": str(p.valor_principal),
            "valor_juros": str(p.valor_juros),
            "valor_pago": str(p.valor_pago or "0.00"),
        }
        for p in parcelas_prazo
    ]

    parcelas_parcela = (
        FinanciamentoParcela.query.filter(
            FinanciamentoParcela.financiamento_id == id,
            FinanciamentoParcela.status.in_([STATUS_PENDENTE, STATUS_ATRASADO]),
        )
        .order_by(FinanciamentoParcela.numero_parcela.asc())
        .all()
    )
    parcelas_json_parcela = [
        {"numero_parcela": p.numero_parcela, "valor_principal": str(p.valor_principal)}
        for p in parcelas_parcela
    ]

    return render_template(
        "financiamentos/amortizar.html",
        form=form,
        financiamento=financiamento,
        parcelas_json_prazo=parcelas_json_prazo,
        parcelas_json_parcela=parcelas_json_parcela,
    )
