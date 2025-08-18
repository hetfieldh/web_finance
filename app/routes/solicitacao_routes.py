# app\routes\solicitacao_routes.py

import re
import secrets
import string
import unicodedata
from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app import db
from app.forms.solicitacao_forms import (
    RejeicaoForm,
    SolicitacaoAcessoForm,
    VerificarStatusForm,
)
from app.models.solicitacao_acesso_model import SolicitacaoAcesso
from app.routes.usuario_routes import admin_required

solicitacao_bp = Blueprint("solicitacao", __name__, url_prefix="/solicitacao")


def sanitizar_login(texto):
    texto_sem_acentos = (
        unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    )
    return re.sub(r"[^a-z0-9._]", "", texto_sem_acentos.lower())


def gerar_senha_segura(tamanho=12):
    alfabeto = string.ascii_letters + string.digits + string.punctuation
    while True:
        senha = "".join(secrets.choice(alfabeto) for i in range(tamanho))
        if (
            any(c.islower() for c in senha)
            and any(c.isupper() for c in senha)
            and any(c.isdigit() for c in senha)
            and any(c in string.punctuation for c in senha)
        ):
            break
    return senha


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


@solicitacao_bp.route("/status", methods=["GET", "POST"])
def verificar_status():
    form = VerificarStatusForm()
    solicitacao = None
    if form.validate_on_submit():
        email_buscado = form.email.data.strip()
        solicitacao = (
            SolicitacaoAcesso.query.filter_by(email=email_buscado)
            .order_by(SolicitacaoAcesso.data_solicitacao.desc())
            .first()
        )
        if not solicitacao:
            flash(
                "Nenhuma solicitação de acesso foi encontrada para o e-mail informado.",
                "warning",
            )
    return render_template(
        "solicitacoes/verificar_status.html", form=form, solicitacao=solicitacao
    )


@solicitacao_bp.route("/gerenciar", methods=["GET"])
@admin_required
def gerenciar_solicitacoes():
    rejeicao_form = RejeicaoForm()
    solicitacoes = SolicitacaoAcesso.query.order_by(
        SolicitacaoAcesso.data_solicitacao.desc()
    ).all()
    return render_template(
        "solicitacoes/gerenciar.html",
        solicitacoes=solicitacoes,
        rejeicao_form=rejeicao_form,
    )


@solicitacao_bp.route("/aprovar/<int:id>", methods=["POST"])
@admin_required
def aprovar_solicitacao(id):
    solicitacao = SolicitacaoAcesso.query.get_or_404(id)
    if solicitacao.status == "Pendente":
        solicitacao.status = "Aprovada"
        solicitacao.admin_id = current_user.id
        solicitacao.data_decisao = datetime.now(timezone.utc)

        nome_sanitizado = sanitizar_login(solicitacao.nome.split(" ")[0])
        sobrenome_sanitizado = sanitizar_login(solicitacao.sobrenome.split(" ")[0])
        login_sugerido = f"{nome_sanitizado}.{sobrenome_sanitizado}"

        senha_gerada = gerar_senha_segura()
        solicitacao.senha_provisoria = senha_gerada

        db.session.commit()
        flash(
            f"Solicitação de {solicitacao.email} aprovada. Agora crie o usuário.",
            "success",
        )

        return redirect(
            url_for(
                "usuario.adicionar_usuario",
                nome=solicitacao.nome,
                sobrenome=solicitacao.sobrenome,
                email=solicitacao.email,
                login=login_sugerido,
            )
        )

    return redirect(url_for("solicitacao.gerenciar_solicitacoes"))


@solicitacao_bp.route("/rejeitar", methods=["POST"])
@admin_required
def rejeitar_solicitacao():
    form = RejeicaoForm()
    if form.validate_on_submit():
        solicitacao = SolicitacaoAcesso.query.get_or_404(form.solicitacao_id.data)
        if solicitacao.status == "Pendente":
            solicitacao.status = "Rejeitada"
            solicitacao.admin_id = current_user.id
            solicitacao.data_decisao = datetime.now(timezone.utc)
            solicitacao.motivo_decisao = form.motivo.data
            db.session.commit()
            flash(f"Solicitação de {solicitacao.email} foi rejeitada.", "warning")
        else:
            flash("Esta solicitação já foi processada.", "info")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(
                    f"Erro no campo '{getattr(form, field).label.text}': {error}",
                    "danger",
                )

    return redirect(url_for("solicitacao.gerenciar_solicitacoes"))
