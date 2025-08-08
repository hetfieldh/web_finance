# app/routes/conta_routes.py

import functools
from decimal import Decimal

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
from app.forms.conta_forms import CadastroContaForm, EditarContaForm
from app.models.conta_model import Conta
from app.models.conta_movimento_model import ContaMovimento

conta_bp = Blueprint("conta", __name__, url_prefix="/contas")


@conta_bp.route("/")
@login_required
def listar_contas():
    contas = (
        Conta.query.filter_by(usuario_id=current_user.id)
        .order_by(Conta.ativa.desc(), Conta.nome_banco.asc(), Conta.tipo.asc())
        .all()
    )
    return render_template("contas/list.html", contas=contas)


@conta_bp.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_conta():
    form = CadastroContaForm()

    if form.validate_on_submit():
        nome_banco = form.nome_banco.data.strip().upper()
        agencia = form.agencia.data.strip()
        conta_num = form.conta.data.strip()
        tipo = form.tipo.data
        saldo_inicial = form.saldo_inicial.data
        limite = form.limite.data
        ativa = form.ativa.data

        existing_account = Conta.query.filter_by(
            usuario_id=current_user.id,
            nome_banco=nome_banco,
            agencia=agencia,
            conta=conta_num,
            tipo=tipo,
        ).first()

        if existing_account:
            flash(
                "Você já possui uma conta com este banco, agência, número e tipo de conta.",
                "danger",
            )
            return render_template("contas/add.html", form=form)

        nova_conta = Conta(
            usuario_id=current_user.id,
            nome_banco=nome_banco,
            agencia=agencia,
            conta=conta_num,
            tipo=tipo,
            saldo_inicial=saldo_inicial,
            saldo_atual=saldo_inicial,
            limite=limite,
            ativa=ativa,
        )
        db.session.add(nova_conta)
        db.session.commit()
        flash("Conta bancária adicionada com sucesso!", "success")
        current_app.logger.info(
            f"Conta {nome_banco}-{conta_num} adicionada por {current_user.login} (ID: {current_user.id})"
        )
        return redirect(url_for("conta.listar_contas"))

    return render_template("contas/add.html", form=form)


@conta_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_conta(id):
    conta = Conta.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()

    form = EditarContaForm(
        original_nome_banco=conta.nome_banco,
        original_agencia=conta.agencia,
        original_conta=conta.conta,
        original_tipo=conta.tipo,
    )

    if form.validate_on_submit():
        if not form.ativa.data and Decimal(str(conta.saldo_atual)) != Decimal("0.00"):
            flash(
                "Não é possível inativar a conta. O saldo atual deve ser zero para inativação.",
                "danger",
            )
            form.nome_banco.data = conta.nome_banco
            form.agencia.data = conta.agencia
            form.conta.data = conta.conta
            form.tipo.data = conta.tipo
            form.saldo_inicial.data = conta.saldo_inicial
            form.limite.data = conta.limite
            form.ativa.data = conta.ativa
            return render_template("contas/edit.html", form=form, conta=conta)

        nome_banco_form = form.nome_banco.data.strip().upper()
        agencia_form = form.agencia.data.strip()
        conta_num_form = form.conta.data.strip()
        tipo_form = conta.tipo

        if (
            nome_banco_form != form.original_nome_banco.strip().upper()
            or agencia_form != form.original_agencia.strip()
            or conta_num_form != form.original_conta.strip()
            or tipo_form != form.original_tipo
        ):

            existing_account = Conta.query.filter_by(
                usuario_id=current_user.id,
                nome_banco=nome_banco_form,
                agencia=agencia_form,
                conta=conta_num_form,
                tipo=tipo_form,
            ).first()

            if existing_account and existing_account.id != conta.id:
                flash(
                    "Você já possui outra conta com este banco, agência, número e tipo de conta.",
                    "danger",
                )
                return render_template("contas/edit.html", form=form, conta=conta)

        conta.nome_banco = nome_banco_form
        conta.agencia = agencia_form
        conta.conta = conta_num_form
        conta.saldo_inicial = form.saldo_inicial.data

        conta.tipo = tipo_form

        conta.limite = form.limite.data
        conta.ativa = form.ativa.data

        db.session.commit()
        flash("Conta bancária atualizada com sucesso!", "success")
        current_app.logger.info(
            f"Conta {conta.nome_banco}-{conta.conta} (ID: {conta.id}) atualizada por {current_user.login} (ID: {current_user.id})"
        )
        return redirect(url_for("conta.listar_contas"))

    elif request.method == "GET":
        form.nome_banco.data = conta.nome_banco
        form.agencia.data = conta.agencia
        form.conta.data = conta.conta
        form.tipo.data = conta.tipo
        form.saldo_inicial.data = conta.saldo_inicial
        form.limite.data = conta.limite
        form.ativa.data = conta.ativa

    return render_template("contas/edit.html", form=form, conta=conta)


@conta_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_conta(id):
    conta = Conta.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()

    if len(conta.movimentos) > 0:
        flash(
            "Não é possível excluir a conta. Existem movimentações associadas a ela.",
            "danger",
        )
        return redirect(url_for("conta.listar_contas"))

    if Decimal(str(conta.saldo_atual)) != Decimal("0.00"):
        flash("Não é possível excluir a conta. O saldo atual deve ser zero.", "danger")
        return redirect(url_for("conta.listar_contas"))

    db.session.delete(conta)
    db.session.commit()
    flash("Conta bancária excluída com sucesso!", "success")
    current_app.logger.info(
        f"Conta {conta.nome_banco}-{conta.conta} (ID: {conta.id}) excluída por {current_user.login} (ID: {current_user.id})"
    )
    return redirect(url_for("conta.listar_contas"))
