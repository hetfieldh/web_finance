# app\routes\solicitacao_routes.py

import re
import secrets
import string
import unicodedata
from datetime import datetime, timezone
from types import SimpleNamespace

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user

from app import db
from app.forms.solicitacao_forms import (
    AprovacaoForm,
    RejeicaoForm,
    SolicitacaoAcessoForm,
    VerificarStatusForm,
)
from app.models.solicitacao_acesso_model import SolicitacaoAcesso
from app.models.usuario_model import Usuario
from app.routes.usuario_routes import admin_required
from app.services.usuario_service import criar_novo_usuario
from app.utils import STATUS_APROVADO, STATUS_PENDENTE, STATUS_REJEITADO

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
    solicitacoes_pendentes = SolicitacaoAcesso.query.filter_by(
        status=STATUS_PENDENTE
    ).count()
    limite_atingido = solicitacoes_pendentes >= 10

    if limite_atingido:
        flash(
            "O número máximo de solicitações pendentes foi atingido. O envio de novas solicitações está temporariamente desabilitado.",
            "warning",
        )
        form = SolicitacaoAcessoForm()
        return render_template(
            "solicitacoes/solicitar_acesso.html", form=form, limite_atingido=True
        )

    form = SolicitacaoAcessoForm()
    if form.validate_on_submit():
        email_solicitado = form.email.data.strip().lower()

        solicitacao_existente = SolicitacaoAcesso.query.filter_by(
            email=email_solicitado
        ).first()
        if solicitacao_existente:
            flash(
                "Já encontramos uma solicitação para este e-mail. Veja o status abaixo.",
                "info",
            )
            return redirect(
                url_for("solicitacao.verificar_status", email=email_solicitado)
            )

        usuario_existente = Usuario.query.filter_by(email=email_solicitado).first()
        if usuario_existente:
            flash(
                "Este e-mail já pertence a um usuário cadastrado. Tente fazer o login.",
                "warning",
            )
            return redirect(url_for("auth.login"))

        nova_solicitacao = SolicitacaoAcesso(
            nome=form.nome.data,
            sobrenome=form.sobrenome.data,
            email=email_solicitado,
            justificativa=form.justificativa.data,
        )
        db.session.add(nova_solicitacao)
        db.session.commit()
        flash("Sua solicitação de acesso foi enviada com sucesso!", "success")
        return redirect(url_for("solicitacao.verificar_status", email=email_solicitado))

    return render_template(
        "solicitacoes/solicitar_acesso.html", form=form, limite_atingido=False
    )


@solicitacao_bp.route("/check-email")
def check_solicitacao_email():
    email = request.args.get("email", "", type=str).strip().lower()
    if not email:
        return jsonify({"exists": False, "user_exists": False})

    solicitacao = SolicitacaoAcesso.query.filter_by(email=email).first()
    usuario = Usuario.query.filter_by(email=email).first()

    if solicitacao:
        status_url = url_for("solicitacao.verificar_status", email=email)
        return jsonify({"exists": True, "status_url": status_url, "user_exists": False})
    elif usuario:
        login_url = url_for("auth.login")
        return jsonify({"exists": False, "user_exists": True, "login_url": login_url})
    else:
        return jsonify({"exists": False, "user_exists": False})


@solicitacao_bp.route("/status", methods=["GET", "POST"])
def verificar_status():
    form = VerificarStatusForm()
    solicitacao = None

    if request.method == "GET":
        email_da_url = request.args.get("email")
        if email_da_url:
            form.email.data = email_da_url
            solicitacao = (
                SolicitacaoAcesso.query.filter_by(email=email_da_url)
                .order_by(SolicitacaoAcesso.data_solicitacao.desc())
                .first()
            )

    if form.validate_on_submit():
        email_buscado = form.email.data.strip().lower()
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
    aprovacao_form = AprovacaoForm()
    solicitacoes = SolicitacaoAcesso.query.order_by(
        SolicitacaoAcesso.data_solicitacao.desc()
    ).all()
    return render_template(
        "solicitacoes/gerenciar.html",
        solicitacoes=solicitacoes,
        rejeicao_form=rejeicao_form,
        aprovacao_form=aprovacao_form,
    )


@solicitacao_bp.route("/aprovar/<int:id>", methods=["POST"])
@admin_required
def aprovar_solicitacao(id):
    solicitacao = SolicitacaoAcesso.query.get_or_404(id)
    if solicitacao.status != STATUS_PENDENTE:
        flash("Esta solicitação já foi processada.", "info")
        return redirect(url_for("usuario.listar_usuarios"))

    try:
        nome_sanitizado = sanitizar_login(solicitacao.nome.split(" ")[0])
        sobrenome_sanitizado = sanitizar_login(solicitacao.sobrenome.split(" ")[0])
        login_sugerido = f"{nome_sanitizado}.{sobrenome_sanitizado}"

        senha_provisoria_texto_puro = gerar_senha_segura()

        form_data = SimpleNamespace(
            nome=SimpleNamespace(data=solicitacao.nome),
            sobrenome=SimpleNamespace(data=solicitacao.sobrenome),
            email=SimpleNamespace(data=solicitacao.email),
            login=SimpleNamespace(data=login_sugerido),
            senha=SimpleNamespace(data=senha_provisoria_texto_puro),
            is_admin=SimpleNamespace(data=False),
        )

        success, message, novo_usuario = criar_novo_usuario(form_data)

        if not success:
            flash(message, "danger")
            return redirect(url_for("solicitacao.gerenciar_solicitacoes"))

        solicitacao.status = STATUS_APROVADO
        solicitacao.admin_id = current_user.id
        solicitacao.data_decisao = datetime.now(timezone.utc)
        solicitacao.login_criado = novo_usuario.login

        mensagem_final = (
            f"Seu acesso foi aprovado!\n\n"
            f"Use seu e-mail ou o login: <strong>{novo_usuario.login}</strong>.\n"
            f"Sua senha provisória é: <strong>{senha_provisoria_texto_puro}</strong>\n\n"
            f"Recomendamos que você a altere no primeiro acesso através do seu perfil."
        )
        solicitacao.motivo_decisao = mensagem_final
        db.session.commit()

        flash(
            f"Usuário '{novo_usuario.login}' criado com sucesso a partir da solicitação! Uma senha provisória foi enviada para o primeiro acesso.",
            "success",
        )

    except Exception as e:
        db.session.rollback()
        flash(f"Ocorreu um erro ao aprovar a solicitação: {e}", "danger")

    return redirect(url_for("usuario.listar_usuarios"))


@solicitacao_bp.route("/rejeitar", methods=["POST"])
@admin_required
def rejeitar_solicitacao():
    form = RejeicaoForm()
    if form.validate_on_submit():
        solicitacao = SolicitacaoAcesso.query.get_or_404(form.solicitacao_id.data)
        if solicitacao.status == STATUS_PENDENTE:
            solicitacao.status = STATUS_REJEITADO
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

    return redirect(url_for("usuario.listar_usuarios"))
