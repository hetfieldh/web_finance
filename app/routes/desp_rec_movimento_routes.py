# app/routes/desp_rec_movimento_routes.py

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
from sqlalchemy import extract
from sqlalchemy.exc import IntegrityError

from app import db
from app.forms.desp_rec_forms import (
    EditarMovimentoForm,
    GerarPrevisaoForm,
    LancamentoUnicoForm,
)
from app.models.desp_rec_model import DespRec
from app.models.desp_rec_movimento_model import DespRecMovimento

desp_rec_movimento_bp = Blueprint(
    "desp_rec_movimento", __name__, url_prefix="/despesas_receitas/movimentos"
)


@desp_rec_movimento_bp.route("/")
@login_required
def listar_movimentos():
    movimentos = (
        DespRecMovimento.query.filter_by(usuario_id=current_user.id)
        .order_by(DespRecMovimento.data_vencimento.desc())
        .all()
    )
    return render_template("desp_rec_movimento/list.html", movimentos=movimentos)


@desp_rec_movimento_bp.route("/gerar-previsao", methods=["GET", "POST"])
@login_required
def gerar_previsao():
    form = GerarPrevisaoForm()
    if form.validate_on_submit():
        try:
            desp_rec_id = form.desp_rec_id.data
            valor_previsto = form.valor_previsto.data
            data_inicio = form.data_inicio.data
            numero_meses = form.numero_meses.data
            descricao = form.descricao.data.strip() if form.descricao.data else None

            cadastro_base = DespRec.query.get(desp_rec_id)
            if not cadastro_base:
                flash("Cadastro base não encontrado.", "danger")
                return redirect(url_for("desp_rec_movimento.gerar_previsao"))

            datas_a_verificar = [
                data_inicio + relativedelta(months=i) for i in range(numero_meses)
            ]
            meses_anos_a_verificar = {(d.year, d.month) for d in datas_a_verificar}

            conflitos = DespRecMovimento.query.filter(
                DespRecMovimento.usuario_id == current_user.id,
                DespRecMovimento.desp_rec_id == desp_rec_id,
                extract("year", DespRecMovimento.data_vencimento).in_(
                    [y for y, m in meses_anos_a_verificar]
                ),
                extract("month", DespRecMovimento.data_vencimento).in_(
                    [m for y, m in meses_anos_a_verificar]
                ),
            ).all()

            if conflitos:
                meses_conflito = sorted(
                    {c.data_vencimento.strftime("%m/%Y") for c in conflitos}
                )
                flash(
                    f"Erro: Já existem lançamentos para '{cadastro_base.nome}' nos seguintes meses: {', '.join(meses_conflito)}. Nenhuma previsão foi gerada.",
                    "danger",
                )
                return redirect(url_for("desp_rec_movimento.gerar_previsao"))

            novos_lancamentos = []
            for i in range(numero_meses):
                data_vencimento_atual = data_inicio + relativedelta(months=i)
                dia_venc = cadastro_base.dia_vencimento or data_vencimento_atual.day
                try:
                    data_vencimento_final = data_vencimento_atual.replace(day=dia_venc)
                except ValueError:
                    ultimo_dia_mes = (
                        data_vencimento_atual.replace(day=28) + relativedelta(days=4)
                    ).replace(day=1) - relativedelta(days=1)
                    data_vencimento_final = ultimo_dia_mes

                novo_movimento = DespRecMovimento(
                    usuario_id=current_user.id,
                    desp_rec_id=desp_rec_id,
                    data_vencimento=data_vencimento_final,
                    valor_previsto=valor_previsto,
                    descricao=descricao,
                    status="Pendente",
                )
                novos_lancamentos.append(novo_movimento)

            db.session.bulk_save_objects(novos_lancamentos)
            db.session.commit()
            flash(
                f"{numero_meses} lançamentos previstos gerados com sucesso!", "success"
            )
            return redirect(url_for("desp_rec_movimento.listar_movimentos"))

        except Exception as e:
            db.session.rollback()
            flash("Erro ao gerar previsões. Tente novamente.", "danger")
            current_app.logger.error(f"Erro ao gerar previsões: {e}", exc_info=True)

    return render_template(
        "desp_rec_movimento/gerar_previsao.html",
        form=form,
        title="Gerar Previsão de Lançamentos",
    )


@desp_rec_movimento_bp.route("/adicionar-lancamento", methods=["GET", "POST"])
@login_required
def adicionar_lancamento_unico():
    form = LancamentoUnicoForm()
    if form.validate_on_submit():
        try:
            desp_rec_id = form.desp_rec_id.data
            data_vencimento = form.data_vencimento.data

            conflito = DespRecMovimento.query.filter(
                DespRecMovimento.usuario_id == current_user.id,
                DespRecMovimento.desp_rec_id == desp_rec_id,
                extract("year", DespRecMovimento.data_vencimento)
                == data_vencimento.year,
                extract("month", DespRecMovimento.data_vencimento)
                == data_vencimento.month,
            ).first()

            if conflito:
                cadastro_base = DespRec.query.get(desp_rec_id)
                flash(
                    f"Erro: Já existe um lançamento para '{cadastro_base.nome}' no mês {data_vencimento.strftime('%m/%Y')}.",
                    "danger",
                )
                return render_template(
                    "desp_rec_movimento/add_unico.html",
                    form=form,
                    title="Adicionar Lançamento Único",
                )

            novo_movimento = DespRecMovimento(
                usuario_id=current_user.id,
                desp_rec_id=desp_rec_id,
                data_vencimento=data_vencimento,
                valor_previsto=form.valor_previsto.data,
                descricao=form.descricao.data.strip() if form.descricao.data else None,
                status="Pendente",
            )
            db.session.add(novo_movimento)
            db.session.commit()
            flash("Lançamento adicionado com sucesso!", "success")
            return redirect(url_for("desp_rec_movimento.listar_movimentos"))
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
    )


@desp_rec_movimento_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_movimento(id):
    movimento = DespRecMovimento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()
    form = EditarMovimentoForm(obj=movimento)

    if form.validate_on_submit():
        try:
            nova_data_vencimento = form.data_vencimento.data

            if (
                nova_data_vencimento.year != movimento.data_vencimento.year
                or nova_data_vencimento.month != movimento.data_vencimento.month
            ):
                conflito = DespRecMovimento.query.filter(
                    DespRecMovimento.id != id,
                    DespRecMovimento.usuario_id == current_user.id,
                    DespRecMovimento.desp_rec_id == movimento.desp_rec_id,
                    extract("year", DespRecMovimento.data_vencimento)
                    == nova_data_vencimento.year,
                    extract("month", DespRecMovimento.data_vencimento)
                    == nova_data_vencimento.month,
                ).first()
                if conflito:
                    flash(
                        f"Erro: Já existe um lançamento para esta conta no mês {nova_data_vencimento.strftime('%m/%Y')}.",
                        "danger",
                    )
                    return render_template(
                        "desp_rec_movimento/edit.html",
                        form=form,
                        title="Editar Lançamento",
                        movimento=movimento,
                    )

            movimento.data_vencimento = nova_data_vencimento
            movimento.valor_previsto = form.valor_previsto.data
            movimento.descricao = (
                form.descricao.data.strip() if form.descricao.data else None
            )

            db.session.commit()
            flash("Lançamento atualizado com sucesso!", "success")
            return redirect(url_for("desp_rec_movimento.listar_movimentos"))
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
    )


@desp_rec_movimento_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_movimento(id):
    movimento = DespRecMovimento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    if movimento.status == "Pago":
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
