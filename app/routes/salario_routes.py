# app/routes/salario_routes.py

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

from app import db
from app.forms.salario_forms import (
    AdicionarItemFolhaForm,
    CabecalhoFolhaForm,
    CadastroSalarioItemForm,
    EditarSalarioItemForm,
)
from app.models.salario_item_model import SalarioItem
from app.models.salario_movimento_item_model import SalarioMovimentoItem
from app.models.salario_movimento_model import SalarioMovimento

salario_bp = Blueprint("salario", __name__, url_prefix="/salario")


@salario_bp.route("/itens")
@login_required
def listar_itens():
    itens = (
        SalarioItem.query.filter_by(usuario_id=current_user.id)
        .order_by(SalarioItem.ativo.desc(), SalarioItem.nome.asc())
        .all()
    )
    return render_template(
        "salario_item/list.html", itens=itens, title="Itens da Folha de Pagamento"
    )


@salario_bp.route("/itens/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_item():
    form = CadastroSalarioItemForm()
    if form.validate_on_submit():
        try:
            novo_item = SalarioItem(
                usuario_id=current_user.id,
                nome=form.nome.data.strip().upper(),
                tipo=form.tipo.data,
                descricao=form.descricao.data.strip() if form.descricao.data else None,
                ativo=form.ativo.data,
            )
            db.session.add(novo_item)
            db.session.commit()
            flash("Item da folha adicionado com sucesso!", "success")
            current_app.logger.info(
                f"Item de salário '{novo_item.nome}' criado por {current_user.login}."
            )
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

    if form.validate_on_submit():
        try:
            item.descricao = (
                form.descricao.data.strip() if form.descricao.data else None
            )
            item.ativo = form.ativo.data
            db.session.commit()
            flash("Item da folha atualizado com sucesso!", "success")
            current_app.logger.info(
                f"Item de salário ID {id} atualizado por {current_user.login}."
            )
            return redirect(url_for("salario.listar_itens"))
        except Exception as e:
            db.session.rollback()
            flash("Erro ao atualizar o item. Tente novamente.", "danger")
            current_app.logger.error(
                f"Erro ao editar SalarioItem ID {id}: {e}", exc_info=True
            )

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
        current_app.logger.info(
            f"Item de salário ID {id} ('{item.nome}') excluído por {current_user.login}."
        )
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
    movimentos = (
        SalarioMovimento.query.filter_by(usuario_id=current_user.id)
        .order_by(SalarioMovimento.mes_referencia.desc())
        .all()
    )
    return render_template(
        "salario_movimento/list.html",
        movimentos=movimentos,
        title="Folhas de Pagamento",
    )


@salario_bp.route("/lancamento/novo", methods=["GET", "POST"])
@login_required
def novo_lancamento_folha():
    form = CabecalhoFolhaForm()
    if form.validate_on_submit():
        movimento_existente = SalarioMovimento.query.filter_by(
            usuario_id=current_user.id, mes_referencia=form.mes_referencia.data
        ).first()
        if movimento_existente:
            flash(
                f"Já existe uma folha de pagamento para o mês {form.mes_referencia.data}.",
                "warning",
            )
            return redirect(
                url_for("salario.gerenciar_itens_folha", id=movimento_existente.id)
            )

        try:
            novo_movimento = SalarioMovimento(
                usuario_id=current_user.id,
                mes_referencia=form.mes_referencia.data,
                data_recebimento=form.data_recebimento.data,
            )
            db.session.add(novo_movimento)
            db.session.commit()
            flash("Folha de pagamento criada. Agora adicione as verbas.", "success")
            return redirect(
                url_for("salario.gerenciar_itens_folha", id=novo_movimento.id)
            )
        except Exception as e:
            db.session.rollback()
            flash("Erro ao criar a folha de pagamento.", "danger")
            current_app.logger.error(
                f"Erro ao criar SalarioMovimento: {e}", exc_info=True
            )

    return render_template(
        "salario_movimento/add.html", form=form, title="Nova Folha de Pagamento"
    )


@salario_bp.route("/lancamento/<int:id>/gerenciar", methods=["GET", "POST"])
@login_required
def gerenciar_itens_folha(id):
    movimento = SalarioMovimento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()
    form = AdicionarItemFolhaForm()

    if form.validate_on_submit():
        try:
            novo_item = SalarioMovimentoItem(
                salario_movimento_id=movimento.id,
                salario_item_id=form.salario_item_id.data,
                valor=form.valor.data,
            )
            db.session.add(novo_item)
            db.session.commit()
            flash("Verba adicionada com sucesso!", "success")
        except Exception as e:
            db.session.rollback()
            flash("Erro ao adicionar verba.", "danger")
            current_app.logger.error(
                f"Erro ao adicionar SalarioMovimentoItem: {e}", exc_info=True
            )
        return redirect(url_for("salario.gerenciar_itens_folha", id=id))

    totais = {
        "proventos": sum(
            item.valor
            for item in movimento.itens
            if item.salario_item.tipo == "Provento"
        ),
        "beneficios": sum(
            item.valor
            for item in movimento.itens
            if item.salario_item.tipo == "Benefício"
        ),
        "impostos": sum(
            item.valor
            for item in movimento.itens
            if item.salario_item.tipo == "Imposto"
        ),
        "descontos": sum(
            item.valor
            for item in movimento.itens
            if item.salario_item.tipo == "Desconto"
        ),
    }
    totais["salario_bruto"] = totais["proventos"]
    totais["total_descontos_impostos"] = totais["descontos"] + totais["impostos"]
    totais["salario_liquido"] = (
        totais["salario_bruto"] - totais["total_descontos_impostos"]
    )

    return render_template(
        "salario_movimento/gerenciar_itens.html",
        movimento=movimento,
        form=form,
        totais=totais,
        title=f"Gerenciar Folha de {movimento.mes_referencia}",
    )


@salario_bp.route("/lancamento/item/excluir/<int:item_id>", methods=["POST"])
@login_required
def excluir_item_folha(item_id):
    item = SalarioMovimentoItem.query.get_or_404(item_id)
    movimento_id = item.salario_movimento_id
    movimento = SalarioMovimento.query.filter_by(
        id=movimento_id, usuario_id=current_user.id
    ).first_or_404()

    try:
        db.session.delete(item)
        db.session.commit()
        flash("Verba removida com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Erro ao remover verba.", "danger")
        current_app.logger.error(
            f"Erro ao excluir SalarioMovimentoItem ID {item_id}: {e}", exc_info=True
        )

    return redirect(url_for("salario.gerenciar_itens_folha", id=movimento_id))


@salario_bp.route("/lancamento/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_movimento(id):
    movimento = SalarioMovimento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    if movimento.movimento_bancario_id:
        flash(
            "Não é possível excluir uma folha de pagamento que já foi conciliada com uma movimentação bancária.",
            "danger",
        )
        return redirect(url_for("salario.listar_movimentos"))

    try:
        db.session.delete(movimento)
        db.session.commit()
        flash("Folha de pagamento excluída com sucesso!", "success")
        current_app.logger.info(
            f"Folha de pagamento ID {id} excluída por {current_user.login}."
        )
    except Exception as e:
        db.session.rollback()
        flash("Erro ao excluir a folha de pagamento.", "danger")
        current_app.logger.error(
            f"Erro ao excluir folha de pagamento ID {id}: {e}", exc_info=True
        )

    return redirect(url_for("salario.listar_movimentos"))
