# app/routes/graphics_routes.py

from datetime import date

from flask import Blueprint, render_template
from flask_login import current_user, login_required

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
    dados_mensais = get_monthly_graphics_data(
        user_id=current_user.id, year=hoje.year, month=hoje.month
    )
    dados_anuais = get_annual_evolution_data(user_id=current_user.id, year=hoje.year)
    dados_financiamento = get_financing_progress_data(
        user_id=current_user.id, year=hoje.year
    )

    return render_template(
        "graphics.html",
        dados_graficos={
            **dados_mensais,
            "evolucao_anual": dados_anuais,
            "progresso_financiamento": dados_financiamento,  # <-- ALTERAÇÃO: Adiciona ao dicionário
        },
        mes_referencia=hoje.strftime("%B/%Y").capitalize(),
    )
