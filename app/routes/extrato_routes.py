# app/routes/extrato_routes.py

from datetime import date, datetime, timedelta
from decimal import Decimal

from flask import Blueprint, flash, render_template, request
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from app import db
from app.forms.extrato_forms import ExtratoBancarioForm
from app.models.conta_model import Conta
from app.models.conta_movimento_model import ContaMovimento

extrato_bp = Blueprint("extrato", __name__, url_prefix="/extratos")


@extrato_bp.route("/bancario", methods=["GET"])
@login_required
def extrato_bancario():
    form = ExtratoBancarioForm(request.args)

    if not form.mes_ano.data:
        form.mes_ano.data = date.today().strftime("%m-%Y")

    movimentacoes = []
    saldo_anterior = Decimal("0.00")
    saldo_final_mes = Decimal("0.00")
    total_creditos = Decimal("0.00")
    total_debitos = Decimal("0.00")
    conta_selecionada = None
    limite_conta = None
    conta_elegivel_limite = False

    if form.conta_id.data:
        try:
            conta_id = int(form.conta_id.data)
            mes_ano_str = form.mes_ano.data
            mes, ano = map(int, mes_ano_str.split("-"))

            conta_selecionada = Conta.query.filter_by(
                id=conta_id, usuario_id=current_user.id
            ).first()

            if conta_selecionada:
                data_inicio_mes = datetime(ano, mes, 1)
                data_fim_mes = (data_inicio_mes + timedelta(days=32)).replace(
                    day=1
                ) - timedelta(days=1)

                limite_conta = conta_selecionada.limite
                if conta_selecionada.tipo in ["Corrente", "Digital"]:
                    conta_elegivel_limite = True

                saldo_anterior = Decimal(str(conta_selecionada.saldo_inicial))

                movs_anteriores = (
                    ContaMovimento.query.filter(
                        ContaMovimento.conta_id == conta_selecionada.id,
                        ContaMovimento.data_movimento < data_inicio_mes,
                    )
                    .options(joinedload(ContaMovimento.tipo_transacao))
                    .all()
                )

                for mov_ant in movs_anteriores:
                    if mov_ant.tipo_transacao:
                        if mov_ant.tipo_transacao.tipo == "Crédito":
                            saldo_anterior += mov_ant.valor
                        else:
                            saldo_anterior -= mov_ant.valor

                movimentacoes_do_mes = (
                    ContaMovimento.query.filter(
                        ContaMovimento.conta_id == conta_selecionada.id,
                        ContaMovimento.data_movimento >= data_inicio_mes,
                        ContaMovimento.data_movimento <= data_fim_mes,
                    )
                    .options(joinedload(ContaMovimento.tipo_transacao))
                    .order_by(
                        ContaMovimento.data_movimento.asc(), ContaMovimento.id.asc()
                    )
                    .all()
                )

                saldo_acumulado_temp = saldo_anterior

                for mov in movimentacoes_do_mes:
                    if mov.tipo_transacao:
                        if mov.tipo_transacao.tipo == "Crédito":
                            saldo_acumulado_temp += mov.valor
                            total_creditos += mov.valor
                        else:
                            saldo_acumulado_temp -= mov.valor
                            total_debitos += mov.valor

                        movimentacoes.append(
                            {
                                "id": mov.id,
                                "data_movimento": mov.data_movimento,
                                "tipo_transacao_nome": mov.tipo_transacao.transacao_tipo,
                                "tipo_movimento": mov.tipo_transacao.tipo,
                                "valor": mov.valor,
                                "descricao": mov.descricao,
                                "saldo_acumulado": saldo_acumulado_temp,
                            }
                        )

                saldo_final_mes = saldo_acumulado_temp

        except (ValueError, TypeError):
            flash("Por favor, selecione uma conta válida.", "warning")

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
