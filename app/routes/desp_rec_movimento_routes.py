# app\routes\desp_rec_movimento_routes.py

import calendar
import json
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
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app import db
from app.forms.desp_rec_forms import (
    EditarMovimentoForm,
    GerarPrevisaoForm,
    LancamentoUnicoForm,
)
from app.models.desp_rec_model import DespRec
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.services import desp_rec_service
from app.services.desp_rec_service import gerar_previsoes
from app.utils import STATUS_PAGO, STATUS_PENDENTE, STATUS_RECEBIDO

desp_rec_movimento_bp = Blueprint(
    "desp_rec_movimento", __name__, url_prefix="/despesas_receitas/movimentos"
)


@desp_rec_movimento_bp.route("/")
@login_required
def listar_movimentos():
    data_inicial_str = request.args.get("data_inicial")
    data_final_str = request.args.get("data_final")

    hoje = date.today()

    if not data_inicial_str and not data_final_str:
        primeiro_dia = date(hoje.year, hoje.month, 1)
        ultimo_dia = date(
            hoje.year, hoje.month, calendar.monthrange(hoje.year, hoje.month)[1]
        )
        data_inicial_str = primeiro_dia.isoformat()
        data_final_str = ultimo_dia.isoformat()

    query = DespRecMovimento.query.filter_by(usuario_id=current_user.id).options(
        joinedload(DespRecMovimento.despesa_receita)
    )

    if data_inicial_str and data_final_str:
        try:
            data_inicial = date.fromisoformat(data_inicial_str)
            data_final = date.fromisoformat(data_final_str)

            query = query.filter(
                and_(
                    DespRecMovimento.data_vencimento >= data_inicial,
                    DespRecMovimento.data_vencimento <= data_final,
                )
            )
        except ValueError:
            flash("Formato de data inválido. Use AAAA-MM-DD.", "danger")
            return redirect(url_for("desp_rec_movimento.listar_movimentos"))

    elif data_inicial_str:
        try:
            data_inicial = date.fromisoformat(data_inicial_str)
            query = query.filter(DespRecMovimento.data_vencimento >= data_inicial)
        except ValueError:
            flash("Formato de data inicial inválido. Use AAAA-MM-DD.", "danger")
            return redirect(url_for("desp_rec_movimento.listar_movimentos"))

    elif data_final_str:
        try:
            data_final = date.fromisoformat(data_final_str)
            query = query.filter(DespRecMovimento.data_vencimento <= data_final)
        except ValueError:
            flash("Formato de data final inválido. Use AAAA-MM-DD.", "danger")
            return redirect(url_for("desp_rec_movimento.listar_movimentos"))

    movimentos = query.order_by(
        DespRecMovimento.data_vencimento.asc(),
        DespRecMovimento.id.desc(),
    ).all()

    return render_template(
        "desp_rec_movimento/list.html",
        movimentos=movimentos,
        data_inicial=data_inicial_str,
        data_final=data_final_str,
    )


@desp_rec_movimento_bp.route("/gerar-previsao", methods=["GET", "POST"])
@login_required
def gerar_previsao():
    fixed_choices = desp_rec_service.get_fixed_desp_rec_for_user_choices()
    form = GerarPrevisaoForm(desp_rec_choices=fixed_choices)
    desp_rec_items_fixos = DespRec.query.filter_by(
        usuario_id=current_user.id, ativo=True, tipo="Fixa"
    ).all()
    vencimentos_map = {
        item.id: item.dia_vencimento
        for item in desp_rec_items_fixos
        if item.dia_vencimento is not None
    }

    if form.validate_on_submit():
        success, message = gerar_previsoes(form)
        if success:
            flash(message, "success")
            return redirect(url_for("desp_rec_movimento.listar_movimentos"))
        else:
            flash(message, "danger")
            return redirect(url_for("desp_rec_movimento.gerar_previsao"))

    return render_template(
        "desp_rec_movimento/gerar_previsao.html",
        form=form,
        title="Gerar Previsão de Lançamentos",
        vencimentos_map=json.dumps(vencimentos_map),
    )


@desp_rec_movimento_bp.route("/adicionar-lancamento", methods=["GET", "POST"])
@login_required
def adicionar_lancamento_unico():
    variable_choices = desp_rec_service.get_variable_desp_rec_for_user_choices()
    form = LancamentoUnicoForm(desp_rec_choices=variable_choices)
    desp_rec_items = DespRec.query.filter_by(
        usuario_id=current_user.id, ativo=True
    ).all()
    vencimentos_map = {
        item.id: item.dia_vencimento
        for item in desp_rec_items
        if item.dia_vencimento is not None
    }

    if form.validate_on_submit():
        try:
            novo_movimento = DespRecMovimento(
                usuario_id=current_user.id,
                desp_rec_id=form.desp_rec_id.data,
                data_vencimento=form.data_vencimento.data,
                valor_previsto=form.valor_previsto.data,
                descricao=form.descricao.data.strip() if form.descricao.data else None,
                status=STATUS_PENDENTE,
            )
            db.session.add(novo_movimento)
            db.session.commit()
            flash("Lançamento adicionado com sucesso!", "success")
            return redirect(url_for("desp_rec_movimento.listar_movimentos"))
        except IntegrityError:
            db.session.rollback()
            cadastro_base = db.session.get(DespRec, form.desp_rec_id.data)
            data_vencimento = form.data_vencimento.data
            flash(
                f"Erro: Já existe um lançamento para '{cadastro_base.nome}' no mês {data_vencimento.strftime('%m/%Y')}.",
                "danger",
            )
        except Exception as e:
            db.session.rollback()
            flash("Erro ao adicionar o lançamento. Tente novamente.", "danger")
            current_app.logger.error(
                f"Erro ao adicionar lançamento único: {e}", exc_info=True
            )

    return render_template(
        "desp_rec_movimento/add_unico.html",
        form=form,
        title="Adicionar Lançamento Único",
        vencimentos_map=json.dumps(vencimentos_map),
    )


@desp_rec_movimento_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_movimento(id):
    movimento = DespRecMovimento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()
    form = EditarMovimentoForm(obj=movimento)

    is_locked = movimento.status in [STATUS_PAGO, STATUS_RECEBIDO]

    if is_locked:
        form.data_vencimento.render_kw = {"readonly": True}
        form.valor_previsto.render_kw = {"readonly": True}

    if form.validate_on_submit():
        if is_locked:
            flash(
                "Este lançamento já foi pago/recebido e não pode mais ser alterado.",
                "warning",
            )
            return redirect(url_for("desp_rec_movimento.listar_movimentos"))

        try:
            movimento.data_vencimento = form.data_vencimento.data
            movimento.valor_previsto = form.valor_previsto.data
            movimento.descricao = (
                form.descricao.data.strip() if form.descricao.data else None
            )

            db.session.commit()
            flash("Lançamento atualizado com sucesso!", "success")
            return redirect(url_for("desp_rec_movimento.listar_movimentos"))

        except IntegrityError:
            db.session.rollback()
            flash(
                f"Erro: Já existe um lançamento para esta conta no mês {form.data_vencimento.data.strftime('%m/%Y')}.",
                "danger",
            )
        except Exception as e:
            db.session.rollback()
            flash("Erro ao atualizar o lançamento. Tente novamente.", "danger")
            current_app.logger.error(
                f"Erro ao editar DespRecMovimento ID {id}: {e}", exc_info=True
            )

    return render_template(
        "desp_rec_movimento/edit.html",
        form=form,
        title="Editar Lançamento",
        movimento=movimento,
        is_locked=is_locked,
    )


@desp_rec_movimento_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_movimento(id):
    movimento = DespRecMovimento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    if movimento.status == STATUS_PAGO:
        flash("Não é possível excluir um lançamento que já foi pago.", "danger")
        return redirect(url_for("desp_rec_movimento.listar_movimentos"))

    try:
        db.session.delete(movimento)
        db.session.commit()
        flash("Lançamento excluído com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Erro ao excluir o lançamento. Tente novamente.", "danger")
        current_app.logger.error(
            f"Erro ao excluir DespRecMovimento ID {id}: {e}", exc_info=True
        )

    return redirect(url_for("desp_rec_movimento.listar_movimentos"))
