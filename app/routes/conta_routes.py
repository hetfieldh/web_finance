# app/routes/conta_routes.py

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
import functools
from app import db
from app.models.conta_model import Conta
from app.forms.conta_forms import CadastroContaForm, EditarContaForm

# Cria um Blueprint para as rotas de contas bancárias
conta_bp = Blueprint("conta", __name__, url_prefix="/contas")


# Rota para listar todas as contas do usuário logado
@conta_bp.route("/")
@login_required
def listar_contas():
    contas = Conta.query.filter_by(usuario_id=current_user.id).all()
    return render_template("contas/list.html", contas=contas)


# Rota para adicionar uma nova conta bancária
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
                "Você já possui uma conta com este banco, agência, número e tipo.",
                "danger",
            )
            return render_template(
                "contas/add.html", form=form
            )  # Renderiza o formulário novamente com a mensagem

        # Cria uma nova instância de Conta
        nova_conta = Conta(
            usuario_id=current_user.id,
            nome_banco=nome_banco,
            agencia=agencia,
            conta=conta_num,
            tipo=tipo,
            saldo_inicial=saldo_inicial,
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


# Rota para editar uma conta bancária existente
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
        conta.tipo = conta.tipo

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


# Rota para excluir uma conta bancária
@conta_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_conta(id):
    conta = Conta.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()

    db.session.delete(conta)
    db.session.commit()
    flash("Conta bancária excluída com sucesso!", "success")
    current_app.logger.info(
        f"Conta {conta.nome_banco}-{conta.conta} (ID: {conta.id}) excluída por {current_user.login} (ID: {current_user.id})"
    )
    return redirect(url_for("conta.listar_contas"))
