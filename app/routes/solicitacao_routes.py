# app\routes\solicitacao_routes.py

from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app import db
from app.forms.solicitacao_forms import SolicitacaoAcessoForm
from app.models.solicitacao_acesso_model import SolicitacaoAcesso
from app.routes.usuario_routes import admin_required

solicitacao_bp = Blueprint("solicitacao", __name__, url_prefix="/solicitacao")


@solicitacao_bp.route("/acesso", methods=["GET", "POST"])
def solicitar_acesso():
    form = SolicitacaoAcessoForm()
    if form.validate_on_submit():
        nova_solicitacao = SolicitacaoAcesso(
            nome=form.nome.data,
            sobrenome=form.sobrenome.data,
            email=form.email.data,
            justificativa=form.justificativa.data,
        )
        db.session.add(nova_solicitacao)
        db.session.commit()
        flash(
            "Sua solicitação de acesso foi enviada com sucesso! Um administrador irá analisá-la em breve.",
            "success",
        )
        return redirect(url_for("auth.login"))
    return render_template("solicitacoes/solicitar_acesso.html", form=form)


@solicitacao_bp.route("/gerenciar", methods=["GET"])
@admin_required
def gerenciar_solicitacoes():
    solicitacoes = SolicitacaoAcesso.query.order_by(
        SolicitacaoAcesso.data_solicitacao.desc()
    ).all()
    return render_template("solicitacoes/gerenciar.html", solicitacoes=solicitacoes)


@solicitacao_bp.route("/aprovar/<int:id>", methods=["POST"])
@admin_required
def aprovar_solicitacao(id):
    solicitacao = SolicitacaoAcesso.query.get_or_404(id)
    if solicitacao.status == "Pendente":
        solicitacao.status = "Aprovada"
        solicitacao.admin_id = current_user.id
        solicitacao.data_decisao = datetime.now(timezone.utc)
        db.session.commit()
        flash(
            f"Solicitação de {solicitacao.email} aprovada. Agora crie o usuário.",
            "success",
        )
        # Redireciona para a página de adicionar usuário com os dados pré-preenchidos
        return redirect(
            url_for(
                "usuario.adicionar_usuario",
                nome=solicitacao.nome,
                sobrenome=solicitacao.sobrenome,
                email=solicitacao.email,
            )
        )
    return redirect(url_for("solicitacao.gerenciar_solicitacoes"))


@solicitacao_bp.route("/rejeitar/<int:id>", methods=["POST"])
@admin_required
def rejeitar_solicitacao(id):
    solicitacao = SolicitacaoAcesso.query.get_or_404(id)
    if solicitacao.status == "Pendente":
        solicitacao.status = "Rejeitada"
        solicitacao.admin_id = current_user.id
        solicitacao.data_decisao = datetime.now(timezone.utc)
        db.session.commit()
        flash(f"Solicitação de {solicitacao.email} foi rejeitada.", "warning")
    return redirect(url_for("solicitacao.gerenciar_solicitacoes"))
