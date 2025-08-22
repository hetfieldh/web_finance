# app/routes/extrato_desp_rec_routes.py

from datetime import date, datetime
from decimal import Decimal

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import extract, func

from app import db
from app.forms.extrato_desp_rec_forms import ExtratoDespRecForm
from app.models.desp_rec_model import DespRec
from app.models.desp_rec_movimento_model import DespRecMovimento
from app.services import desp_rec_service

extrato_desp_rec_bp = Blueprint("extrato_desp_rec", __name__, url_prefix="/extratos")


@extrato_desp_rec_bp.route("/despesas_receitas", methods=["GET", "POST"])
@login_required
def extrato_despesas_receitas():
    desp_rec_choices = desp_rec_service.get_all_desp_rec_for_user_choices()
    form = ExtratoDespRecForm(request.form, desp_rec_choices=desp_rec_choices)

    movimentos = []
    totais = {
        "receitas_previstas": Decimal("0.00"),
        "despesas_previstas": Decimal("0.00"),
        "saldo_previsto": Decimal("0.00"),
        "receitas_realizadas": Decimal("0.00"),
        "despesas_realizadas": Decimal("0.00"),
        "saldo_realizado": Decimal("0.00"),
    }

    if request.method == "GET":
        hoje = date.today()
        mes_ano_atual = hoje.strftime("%Y-%m")
        form.mes_ano.data = mes_ano_atual

    if form.validate_on_submit():
        tipo_relatorio = form.tipo_relatorio.data
        query = DespRecMovimento.query.join(DespRec).filter(
            DespRecMovimento.usuario_id == current_user.id
        )

        if tipo_relatorio == "mensal":
            mes_ano_str = form.mes_ano.data
            if mes_ano_str:
                ano, mes = map(int, mes_ano_str.split("-"))
                query = query.filter(
                    extract("year", DespRecMovimento.data_vencimento) == ano,
                    extract("month", DespRecMovimento.data_vencimento) == mes,
                )

        elif tipo_relatorio == "periodo":
            desp_rec_id = form.desp_rec_id.data
            data_inicio = form.data_inicio.data
            data_fim = form.data_fim.data

            if desp_rec_id:
                query = query.filter(DespRecMovimento.desp_rec_id == desp_rec_id)
            if data_inicio:
                query = query.filter(DespRecMovimento.data_vencimento >= data_inicio)
            if data_fim:
                query = query.filter(DespRecMovimento.data_vencimento <= data_fim)

        movimentos = query.order_by(DespRecMovimento.data_vencimento.asc()).all()

        for mov in movimentos:
            if mov.despesa_receita.natureza == "Receita":
                totais["receitas_previstas"] += mov.valor_previsto
                if mov.valor_realizado is not None:
                    totais["receitas_realizadas"] += mov.valor_realizado
            else:
                totais["despesas_previstas"] += mov.valor_previsto
                if mov.valor_realizado is not None:
                    totais["despesas_realizadas"] += mov.valor_realizado

        totais["saldo_previsto"] = (
            totais["receitas_previstas"] - totais["despesas_previstas"]
        )
        totais["saldo_realizado"] = (
            totais["receitas_realizadas"] - totais["despesas_realizadas"]
        )

    return render_template(
        "extratos/desp_rec.html",
        form=form,
        movimentos=movimentos,
        totais=totais,
        title="Extrato de Despesas e Receitas",
    )
