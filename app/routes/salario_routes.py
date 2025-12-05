# app/routes/salario_routes.py

import calendar
import json
from datetime import date, datetime
from operator import and_

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload, subqueryload

from app import db
from app.forms.salario_forms import (
    AdicionarItemFolhaForm,
    CabecalhoFolhaForm,
    CadastroSalarioItemForm,
    EditarSalarioItemForm,
)
from app.models.conta_model import Conta
from app.models.salario_item_model import SalarioItem
from app.models.salario_movimento_item_model import SalarioMovimentoItem
from app.models.salario_movimento_model import SalarioMovimento
from app.services import salario_service
from app.services.salario_service import (
    adicionar_item_folha,
    criar_folha_pagamento,
)
from app.services.salario_service import (
    excluir_folha_pagamento as excluir_folha_pagamento_service,
)
from app.services.salario_service import (
    excluir_item_folha as excluir_item_folha_service,
)

salario_bp = Blueprint("salario", __name__, url_prefix="/salario")


@salario_bp.route("/itens")
@login_required
def listar_itens():
    itens = (
        SalarioItem.query.filter_by(usuario_id=current_user.id)
        .order_by(SalarioItem.tipo.asc(), SalarioItem.nome.asc())
        .all()
    )
    return render_template(
        "salario_item/list.html", itens=itens, title="Itens da Folha de Pagamento"
    )


@salario_bp.route("/itens/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_item():
    form = CadastroSalarioItemForm()
    contas_usuario = (
        Conta.query.filter_by(usuario_id=current_user.id, ativa=True)
        .order_by(Conta.nome_banco)
        .all()
    )
    form.conta_destino_id.choices = [("", "Nenhuma")] + [
        (c.id, c.nome_banco) for c in contas_usuario
    ]

    if form.validate_on_submit():
        try:
            novo_item = SalarioItem(
                usuario_id=current_user.id,
                nome=form.nome.data.strip().upper(),
                tipo=form.tipo.data,
                descricao=form.descricao.data.strip() if form.descricao.data else None,
                ativo=form.ativo.data,
                id_conta_destino=(
                    form.conta_destino_id.data
                    if form.tipo.data == "Benefício"
                    else None
                ),
            )
            db.session.add(novo_item)
            db.session.commit()
            flash("Item da folha adicionado com sucesso!", "success")
            return redirect(url_for("salario.listar_itens"))
        except Exception as e:
            db.session.rollback()
            flash("Erro ao adicionar item. Tente novamente.", "danger")
            current_app.logger.error(
                f"Erro ao adicionar SalarioItem: {e}", exc_info=True
            )

    return render_template(
        "salario_item/add.html", form=form, title="Adicionar Item da Folha"
    )


@salario_bp.route("/itens/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_item(id):
    item = SalarioItem.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()
    form = EditarSalarioItemForm(obj=item)

    contas_usuario = (
        Conta.query.filter_by(usuario_id=current_user.id, ativa=True)
        .order_by(Conta.nome_banco)
        .all()
    )
    form.conta_destino_id.choices = [("", "Nenhuma")] + [
        (c.id, c.nome_banco) for c in contas_usuario
    ]

    if request.method == "GET":
        form.conta_destino_id.data = item.id_conta_destino

    if form.validate_on_submit():
        try:
            item.descricao = (
                form.descricao.data.strip() if form.descricao.data else None
            )
            item.ativo = form.ativo.data
            item.id_conta_destino = (
                form.conta_destino_id.data if item.tipo == "Benefício" else None
            )
            db.session.commit()
            flash("Item da folha atualizado com sucesso!", "success")
            return redirect(url_for("salario.listar_itens"))
        except Exception as e:
            db.session.rollback()
            flash("Erro ao atualizar o item. Tente novamente.", "danger")
            current_app.logger.error(
                f"Erro ao editar SalarioItem ID {id}: {e}", exc_info=True
            )

    if request.method == "GET":
        form.nome.data = item.nome
        form.tipo.data = item.tipo
        form.conta_destino_id.data = item.id_conta_destino
        form.descricao.data = item.descricao
        form.ativo.data = item.ativo

    return render_template(
        "salario_item/edit.html", form=form, item=item, title="Editar Item da Folha"
    )


@salario_bp.route("/itens/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_item(id):
    item = SalarioItem.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()

    if SalarioMovimentoItem.query.filter_by(salario_item_id=id).first():
        flash(
            "Não é possível excluir este item, pois ele já está sendo utilizado em lançamentos.",
            "danger",
        )
        return redirect(url_for("salario.listar_itens"))

    try:
        db.session.delete(item)
        db.session.commit()
        flash("Item da folha excluído com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Erro ao excluir o item.", "danger")
        current_app.logger.error(
            f"Erro ao excluir SalarioItem ID {id}: {e}", exc_info=True
        )

    return redirect(url_for("salario.listar_itens"))


@salario_bp.route("/lancamentos")
@login_required
def listar_movimentos():
    data_inicial_str = request.args.get("data_inicial")
    data_final_str = request.args.get("data_final")

    query = (
        db.session.query(SalarioMovimento)
        .outerjoin(SalarioMovimento.itens)
        .filter(SalarioMovimento.usuario_id == current_user.id)
        .options(
            joinedload(SalarioMovimento.itens).joinedload(
                SalarioMovimentoItem.salario_item
            )
        )
        .distinct()
    )

    try:
        if data_inicial_str:
            data_inicial = date.fromisoformat(data_inicial_str)
            query = query.filter(SalarioMovimento.data_recebimento >= data_inicial)

        if data_final_str:
            data_final = date.fromisoformat(data_final_str)
            query = query.filter(SalarioMovimento.data_recebimento <= data_final)
    except ValueError:
        flash("Formato de data inválido. Use DD-MM-AAAA.", "danger")
        return redirect(url_for("salario.listar_movimentos"))

    movimentos = query.order_by(
        SalarioMovimento.data_recebimento.desc(),
    ).all()

    return render_template(
        "salario_movimento/list.html",
        movimentos=movimentos,
        data_inicial=data_inicial_str,
        data_final=data_final_str,
    )


@salario_bp.route("/lancamento/novo", methods=["GET", "POST"])
@login_required
def novo_lancamento_folha():
    form = CabecalhoFolhaForm()
    if form.validate_on_submit():
        try:
            mes_ref_str = form.mes_referencia.data
            mes_referencia_date = datetime.strptime(
                f"01/{mes_ref_str}", "%d/%m/%Y"
            ).date()

            data_recebimento_date = None
            if form.tipo.data != "Mensal" and form.data_recebimento.data:
                data_recebimento_date = datetime.strptime(
                    form.data_recebimento.data, "%d/%m/%Y"
                ).date()

            success, message, movimento = criar_folha_pagamento(
                mes_referencia=mes_referencia_date,
                tipo_folha=form.tipo.data,
                data_recebimento_form=data_recebimento_date,
            )
            if success:
                flash(message, "success")
                return redirect(
                    url_for("salario.gerenciar_itens_folha", id=movimento.id)
                )
            else:
                flash(message, "warning")
                return redirect(url_for("salario.listar_movimentos"))
        except ValueError as e:
            flash(f"Erro no formato das datas: {str(e)}", "danger")
        except Exception as e:
            current_app.logger.error(f"Erro ao criar folha: {e}", exc_info=True)
            flash(f"Erro inesperado: {str(e)}", "danger")

    return render_template(
        "salario_movimento/add.html", form=form, title="Nova Folha de Pagamento"
    )


def _calcular_totais_folha(movimento):
    beneficios_individuais = [
        item for item in movimento.itens if item.salario_item.tipo == "Benefício"
    ]
    outros_itens = [
        item for item in movimento.itens if item.salario_item.tipo != "Benefício"
    ]

    totais = {
        "proventos": sum(
            item.valor for item in outros_itens if item.salario_item.tipo == "Provento"
        ),
        "impostos": sum(
            item.valor for item in outros_itens if item.salario_item.tipo == "Imposto"
        ),
        "descontos": sum(
            item.valor for item in outros_itens if item.salario_item.tipo == "Desconto"
        ),
        "fgts": sum(
            item.valor for item in outros_itens if item.salario_item.tipo == "FGTS"
        ),
        "beneficios": sum(item.valor for item in beneficios_individuais),
    }

    totais["salario_bruto"] = totais["proventos"]
    totais["total_descontos_impostos"] = totais["descontos"] + totais["impostos"]
    totais["salario_liquido"] = (
        totais["salario_bruto"] - totais["total_descontos_impostos"]
    )
    return totais, beneficios_individuais


@salario_bp.route("/lancamento/<int:id>/gerenciar", methods=["GET", "POST"])
@login_required
def gerenciar_itens_folha(id):
    movimento = (
        SalarioMovimento.query.options(
            joinedload(SalarioMovimento.itens).joinedload(
                SalarioMovimentoItem.salario_item
            )
        )
        .filter_by(id=id, usuario_id=current_user.id)
        .first_or_404()
    )

    salario_item_choices = salario_service.get_active_salario_items_for_user_choices()
    form = AdicionarItemFolhaForm(salario_item_choices=salario_item_choices)

    if form.validate_on_submit():
        success, message, item_data = salario_service.adicionar_item_folha(id, form)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            if success:
                totais_atualizados, _ = _calcular_totais_folha(movimento)
                return jsonify(
                    {
                        "success": True,
                        "message": message,
                        "item": item_data,
                        "totais": totais_atualizados,
                    }
                )
            else:
                return jsonify({"success": False, "message": message}), 400

        if success:
            flash(message, "success")
        else:
            flash(message, "warning")
        return redirect(url_for("salario.gerenciar_itens_folha", id=id))

    salario_pago = movimento.movimento_bancario_salario_id is not None
    algum_beneficio_pago = any(
        item.movimento_bancario_id is not None
        for item in movimento.itens
        if item.salario_item.tipo == "Benefício"
    )
    is_locked = salario_pago or algum_beneficio_pago

    totais, beneficios_individuais = _calcular_totais_folha(movimento)

    return render_template(
        "salario_movimento/gerenciar_itens.html",
        movimento=movimento,
        form=form,
        totais=totais,
        beneficios_individuais=beneficios_individuais,
        is_locked=is_locked,
        title=f"Gerenciar Folha de {movimento.mes_referencia}",
    )


@salario_bp.route("/lancamento/item/excluir/<int:item_id>", methods=["POST"])
@login_required
def excluir_item_folha(item_id):
    item = SalarioMovimentoItem.query.get_or_404(item_id)
    movimento = item.movimento_pai

    success, message, deleted_item_id = excluir_item_folha_service(item_id)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        if success:
            totais_atualizados, _ = _calcular_totais_folha(movimento)
            return jsonify(
                {
                    "success": True,
                    "message": message,
                    "deleted_item_id": deleted_item_id,
                    "totais": totais_atualizados,
                }
            )
        else:
            return jsonify({"success": False, "message": message}), 400

    if success:
        flash(message, "success")
    else:
        flash(message, "warning")
    return redirect(url_for("salario.gerenciar_itens_folha", id=movimento.id))


@salario_bp.route("/lancamento/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_movimento(id):
    success, message = excluir_folha_pagamento_service(id)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for("salario.listar_movimentos"))
