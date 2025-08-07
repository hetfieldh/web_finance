# app/routes/extrato_routes.py

from datetime import date, datetime, timedelta
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.forms.extrato_forms import ExtratoBancarioForm
from app.models.conta_model import Conta
from app.models.conta_movimento_model import ContaMovimento
from app.models.conta_transacao_model import ContaTransacao

extrato_bp = Blueprint("extrato", __name__, url_prefix="/extratos")


@extrato_bp.route("/bancario", methods=["GET", "POST"])
@login_required
def extrato_bancario():
    form = ExtratoBancarioForm()
    movimentacoes = []
    saldo_anterior = Decimal("0.00")
    saldo_final_mes = Decimal("0.00")
    total_creditos = Decimal("0.00")
    total_debitos = Decimal("0.00")
    conta_selecionada = None
    limite_conta = None
    conta_elegivel_limite = False

    if form.validate_on_submit():
        conta_id = form.conta_id.data
        mes_ano_str = form.mes_ano.data

        conta_selecionada = Conta.query.filter_by(
            id=conta_id, usuario_id=current_user.id
        ).first()

        if not conta_selecionada:
            flash("Conta bancária inválida.", "danger")
            return render_template("extratos/bancario.html", form=form)

        limite_conta = conta_selecionada.limite
        if conta_selecionada.tipo in ["Corrente", "Digital"]:
            conta_elegivel_limite = True

        ano = int(mes_ano_str.split("-")[0])
        mes = int(mes_ano_str.split("-")[1])

        data_inicio_mes = datetime(ano, mes, 1)
        if mes == 12:
            data_fim_mes = datetime(ano + 1, 1, 1) - timedelta(days=1)
        else:
            data_fim_mes = datetime(ano, mes + 1, 1) - timedelta(days=1)

        saldo_anterior = Decimal(str(conta_selecionada.saldo_inicial))

        movs_anteriores = ContaMovimento.query.filter(
            ContaMovimento.conta_id == conta_selecionada.id,
            ContaMovimento.data_movimento < data_inicio_mes,
        ).all()

        for mov_ant in movs_anteriores:
            tipo_transacao_ant = ContaTransacao.query.get(mov_ant.conta_transacao_id)
            if tipo_transacao_ant:
                if tipo_transacao_ant.tipo == "Crédito":
                    saldo_anterior += mov_ant.valor
                else:
                    saldo_anterior -= mov_ant.valor

        # --- LÓGICA DE ORDENAÇÃO E CÁLCULO CORRIGIDA ---
        movimentacoes_do_mes = (
            ContaMovimento.query.filter(
                ContaMovimento.conta_id == conta_selecionada.id,
                ContaMovimento.data_movimento >= data_inicio_mes,
                ContaMovimento.data_movimento <= data_fim_mes,
            )
            # 1. Busca na ordem cronológica correta (ascendente) para o cálculo
            .order_by(
                ContaMovimento.data_movimento.asc(), ContaMovimento.id.asc()
            ).all()
        )

        saldo_acumulado_temp = saldo_anterior
        movimentacoes_para_template = []

        # 2. Calcula o saldo acumulado na ordem correta
        for mov in movimentacoes_do_mes:
            tipo_transacao_mov = ContaTransacao.query.get(mov.conta_transacao_id)
            if tipo_transacao_mov:
                if tipo_transacao_mov.tipo == "Crédito":
                    saldo_acumulado_temp += mov.valor
                    total_creditos += mov.valor
                else:
                    saldo_acumulado_temp -= mov.valor
                    total_debitos += mov.valor

                movimentacoes_para_template.append(
                    {
                        "id": mov.id,
                        "data_movimento": mov.data_movimento,
                        "tipo_transacao_nome": tipo_transacao_mov.transacao_tipo,
                        "tipo_movimento": tipo_transacao_mov.tipo,
                        "valor": mov.valor,
                        "descricao": mov.descricao,
                        "saldo_acumulado": saldo_acumulado_temp,
                    }
                )

        # 3. A lista já está na ordem cronológica correta para exibição.
        movimentacoes = movimentacoes_para_template
        saldo_final_mes = saldo_acumulado_temp
        # --- FIM DA CORREÇÃO ---

    elif request.method == "GET":
        if form.conta_id.choices:
            form.conta_id.data = form.conta_id.choices[0][0]

        hoje = date.today()
        mes_atual_str = f"{hoje.year}-{hoje.month:02d}"
        if any(choice[0] == mes_atual_str for choice in form.mes_ano.choices):
            form.mes_ano.data = mes_atual_str

    return render_template(
        "extratos/bancario.html",
        form=form,
        movimentacoes=movimentacoes,
        saldo_anterior=saldo_anterior,
        saldo_final_mes=saldo_final_mes,
        total_creditos=total_creditos,
        total_debitos=total_debitos,
        conta_selecionada=conta_selecionada,
        limite_conta=limite_conta,
        conta_elegivel_limite=conta_elegivel_limite,
    )
