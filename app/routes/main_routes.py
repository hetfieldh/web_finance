from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html")
