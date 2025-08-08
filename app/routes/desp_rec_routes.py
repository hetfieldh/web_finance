# app/routes/desp_rec_routes.py

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
from app.forms.desp_rec_forms import CadastroDespRecForm, EditarDespRecForm
from app.models.desp_rec_model import DespRec

desp_rec_bp = Blueprint("desp_rec", __name__, url_prefix="/despesas_receitas")


@desp_rec_bp.route("/")
@login_required
def listar_cadastros():
    cadastros = (
        DespRec.query.filter_by(usuario_id=current_user.id)
        .order_by(DespRec.ativo.desc(), DespRec.nome.asc(), DespRec.natureza.asc())
        .all()
    )
    return render_template("desp_rec/list.html", cadastros=cadastros)


@desp_rec_bp.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_cadastro():
    form = CadastroDespRecForm()
    if form.validate_on_submit():
        try:
            novo_cadastro = DespRec(
                usuario_id=current_user.id,
                nome=form.nome.data.strip().upper(),
                natureza=form.natureza.data,
                tipo=form.tipo.data,
                dia_vencimento=form.dia_vencimento.data,
                ativo=form.ativo.data,
            )
            db.session.add(novo_cadastro)
            db.session.commit()
            flash("Cadastro adicionado com sucesso!", "success")
            current_app.logger.info(
                f"Cadastro de Despesa/Receita '{novo_cadastro.nome}' criado por {current_user.login}."
            )
            return redirect(url_for("desp_rec.listar_cadastros"))
        except Exception as e:
            db.session.rollback()
            flash("Erro ao adicionar o cadastro. Tente novamente.", "danger")
            current_app.logger.error(f"Erro ao adicionar DespRec: {e}", exc_info=True)

    return render_template("desp_rec/add.html", form=form, title="Adicionar Cadastro")


@desp_rec_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_cadastro(id):
    cadastro = DespRec.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()
    form = EditarDespRecForm(obj=cadastro)

    if form.validate_on_submit():
        try:
            cadastro.dia_vencimento = form.dia_vencimento.data
            cadastro.ativo = form.ativo.data
            db.session.commit()
            flash("Cadastro atualizado com sucesso!", "success")
            current_app.logger.info(
                f"Cadastro de Despesa/Receita ID {id} atualizado por {current_user.login}."
            )
            return redirect(url_for("desp_rec.listar_cadastros"))
        except Exception as e:
            db.session.rollback()
            flash("Erro ao atualizar o cadastro. Tente novamente.", "danger")
            current_app.logger.error(
                f"Erro ao editar DespRec ID {id}: {e}", exc_info=True
            )

    elif request.method == "GET":
        form.nome.data = cadastro.nome
        form.natureza.data = cadastro.natureza
        form.tipo.data = cadastro.tipo
        form.dia_vencimento.data = cadastro.dia_vencimento
        form.ativo.data = cadastro.ativo

    return render_template(
        "desp_rec/edit.html", form=form, title="Editar Cadastro", cadastro=cadastro
    )


@desp_rec_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_cadastro(id):
    cadastro = DespRec.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()

    if cadastro.movimentos:
        flash(
            "Não é possível excluir este cadastro, pois existem lançamentos associados a ele.",
            "danger",
        )
        return redirect(url_for("desp_rec.listar_cadastros"))

    try:
        db.session.delete(cadastro)
        db.session.commit()
        flash("Cadastro excluído com sucesso!", "success")
        current_app.logger.info(
            f"Cadastro de Despesa/Receita ID {id} ('{cadastro.nome}') excluído por {current_user.login}."
        )
    except Exception as e:
        db.session.rollback()
        flash("Erro ao excluir o cadastro. Tente novamente.", "danger")
        current_app.logger.error(f"Erro ao excluir DespRec ID {id}: {e}", exc_info=True)

    return redirect(url_for("desp_rec.listar_cadastros"))
