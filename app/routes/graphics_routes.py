# app/routes/graphics_routes.py

from datetime import date

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from app.models.financiamento_model import Financiamento
from app.services.graphics_service import (
    get_annual_evolution_data,
    get_financing_progress_data,
    get_monthly_graphics_data,
)

graphics_bp = Blueprint("graphics", __name__, url_prefix="/graficos")


@graphics_bp.route("/")
@login_required
def view_graphics():
    hoje = date.today()

    # 1. Buscar todos os financiamentos do usuário para a caixa de seleção
    todos_financiamentos = (
        Financiamento.query.filter_by(usuario_id=current_user.id)
        .order_by(Financiamento.nome_financiamento.asc())
        .all()
    )

    # 2. Verificar qual financiamento foi selecionado (ou usar o primeiro como padrão)
    selected_finan_id = request.args.get("financiamento_id", type=int)
    if not selected_finan_id and todos_financiamentos:
        selected_finan_id = todos_financiamentos[0].id

    # 3. Buscar os dados dos gráficos
    dados_mensais = get_monthly_graphics_data(
        user_id=current_user.id, year=hoje.year, month=hoje.month
    )
    dados_anuais = get_annual_evolution_data(user_id=current_user.id, year=hoje.year)

    # 4. Chamar o serviço com o ID do financiamento selecionado
    dados_financiamento = get_financing_progress_data(
        user_id=current_user.id, year=hoje.year, financiamento_id=selected_finan_id
    )

    dados_graficos = {
        **dados_mensais,
        "evolucao_anual": dados_anuais,
        "progresso_financiamento": dados_financiamento,
    }

    return render_template(
        "graphics.html",
        dados_graficos=dados_graficos,
        mes_referencia=hoje.strftime("%B/%Y").capitalize(),
        ano_atual=hoje.year,
        # 5. Enviar a lista e o ID selecionado para o template
        todos_financiamentos=todos_financiamentos,
        selected_finan_id=selected_finan_id,
    )
