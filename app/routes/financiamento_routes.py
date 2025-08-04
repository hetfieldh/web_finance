# app/routes/financiamento_routes.py

import csv
import io
from datetime import datetime
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
from sqlalchemy.exc import IntegrityError

from app import db
from app.forms.financiamento_forms import (
    CadastroFinanciamentoForm,
    EditarFinanciamentoForm,
    ImportarParcelasForm,
)
from app.models.conta_model import Conta
from app.models.conta_movimento_model import ContaMovimento
from app.models.financiamento_model import Financiamento
from app.models.financiamento_parcela_model import FinanciamentoParcela

financiamento_bp = Blueprint("financiamento", __name__, url_prefix="/financiamentos")


@financiamento_bp.route("/")
@login_required
def listar_financiamentos():
    financiamentos = (
        Financiamento.query.filter_by(usuario_id=current_user.id)
        .order_by(Financiamento.data_inicio.desc())
        .all()
    )
    return render_template("financiamentos/list.html", financiamentos=financiamentos)


@financiamento_bp.route("/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_financiamento():
    form = CadastroFinanciamentoForm()

    if form.validate_on_submit():
        nome_financiamento = form.nome_financiamento.data.strip()
        conta_id = form.conta_id.data
        valor_total_financiado = form.valor_total_financiado.data
        taxa_juros_anual = form.taxa_juros_anual.data
        data_inicio = form.data_inicio.data
        prazo_meses = form.prazo_meses.data
        tipo_amortizacao = form.tipo_amortizacao.data
        descricao = form.descricao.data.strip() if form.descricao.data else None

        try:
            novo_financiamento = Financiamento(
                usuario_id=current_user.id,
                conta_id=conta_id,
                nome_financiamento=nome_financiamento,
                valor_total_financiado=valor_total_financiado,
                saldo_devedor_atual=valor_total_financiado,
                taxa_juros_anual=taxa_juros_anual,
                data_inicio=data_inicio,
                prazo_meses=prazo_meses,
                tipo_amortizacao=tipo_amortizacao,
                descricao=descricao,
            )
            db.session.add(novo_financiamento)
            db.session.commit()

            flash(
                "Financiamento principal criado com sucesso! Agora, importe o arquivo .csv com as parcelas.",
                "success",
            )
            current_app.logger.info(
                f'Financiamento "{nome_financiamento}" (ID: {novo_financiamento.id}) adicionado por {current_user.login}.'
            )
            return redirect(
                url_for("financiamento.importar_parcelas", id=novo_financiamento.id)
            )

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(
                f"Erro de integridade ao adicionar financiamento: {e}", exc_info=True
            )
            flash(
                "Erro ao adicionar financiamento. Verifique se o nome já não existe.",
                "danger",
            )
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Erro inesperado ao adicionar financiamento: {e}", exc_info=True
            )
            flash("Ocorreu um erro inesperado. Tente novamente.", "danger")

    return render_template("financiamentos/add.html", form=form)


@financiamento_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_financiamento(id):
    financiamento = Financiamento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    if any(p.pago for p in financiamento.parcelas):
        flash(
            "Não é possível editar um financiamento que já possui parcelas pagas.",
            "danger",
        )
        return redirect(url_for("financiamento.listar_financiamentos"))

    form = EditarFinanciamentoForm(
        obj=financiamento, original_nome_financiamento=financiamento.nome_financiamento
    )

    if form.validate_on_submit():
        financiamento.descricao = (
            form.descricao.data.strip() if form.descricao.data else None
        )
        try:
            db.session.commit()
            flash("Financiamento atualizado com sucesso!", "success")
            current_app.logger.info(
                f"Financiamento (ID: {financiamento.id}) atualizado por {current_user.login}."
            )
            return redirect(url_for("financiamento.listar_financiamentos"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Erro ao salvar atualização de financiamento: {e}", exc_info=True
            )
            flash(
                "Ocorreu um erro ao atualizar o financiamento. Tente novamente.",
                "danger",
            )

    return render_template(
        "financiamentos/edit.html", form=form, financiamento=financiamento
    )


@financiamento_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_financiamento(id):
    financiamento = Financiamento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    if any(p.pago for p in financiamento.parcelas):
        flash(
            "Não é possível excluir um financiamento que já possui parcelas pagas.",
            "danger",
        )
        return redirect(url_for("financiamento.listar_financiamentos"))

    db.session.delete(financiamento)
    db.session.commit()
    flash("Financiamento excluído com sucesso!", "success")
    current_app.logger.info(
        f"Financiamento (ID: {financiamento.id}) excluído por {current_user.login}."
    )
    return redirect(url_for("financiamento.listar_financiamentos"))


@financiamento_bp.route("/<int:id>/importar", methods=["GET", "POST"])
@login_required
def importar_parcelas(id):
    financiamento = Financiamento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()
    form = ImportarParcelasForm()

    if form.validate_on_submit():
        csv_file = form.csv_file.data
        if not csv_file or not csv_file.filename.endswith(".csv"):
            flash("Por favor, selecione um arquivo .csv válido.", "danger")
            return redirect(url_for("financiamento.importar_parcelas", id=id))

        try:
            stream = io.StringIO(csv_file.stream.read().decode("UTF-8"), newline=None)
            csv_reader = csv.reader(stream)
            header = next(csv_reader, None)
            all_rows = list(csv_reader)

            if len(all_rows) != financiamento.prazo_meses:
                flash(
                    (
                        f"Erro: O arquivo CSV contém {len(all_rows)} parcelas, "
                        f"mas o financiamento espera {financiamento.prazo_meses}. "
                        "Por favor, verifique o arquivo."
                    ),
                    "danger",
                )
                return redirect(url_for("financiamento.importar_parcelas", id=id))

            FinanciamentoParcela.query.filter_by(financiamento_id=id).delete()

            saldo_devedor_corrente = financiamento.valor_total_financiado
            parcelas_para_adicionar = []

            for i, row in enumerate(all_rows, start=2):
                if not row:
                    continue

                (
                    numero_parcela,
                    data_vencimento_str,
                    valor_principal_str,
                    valor_juros_str,
                    valor_seguro_str,
                    valor_seguro_2_str,
                    valor_seguro_3_str,
                    valor_taxas_str,
                    multa_str,
                    mora_str,
                    ajustes_str,
                    _,
                    _,
                    *observacoes_tuple,
                ) = row

                valor_principal = Decimal(valor_principal_str)
                valor_juros = Decimal(valor_juros_str)
                valor_seguro = Decimal(valor_seguro_str)
                valor_seguro_2 = Decimal(valor_seguro_2_str)
                valor_seguro_3 = Decimal(valor_seguro_3_str)
                valor_taxas = Decimal(valor_taxas_str)
                multa = Decimal(multa_str)
                mora = Decimal(mora_str)
                ajustes = Decimal(ajustes_str)
                observacoes = observacoes_tuple[0] if observacoes_tuple else None

                valor_total_calculado = (
                    valor_principal
                    + valor_juros
                    + valor_seguro
                    + valor_seguro_2
                    + valor_seguro_3
                    + valor_taxas
                    + multa
                    + mora
                    + ajustes
                )

                saldo_devedor_corrente -= valor_principal

                nova_parcela = FinanciamentoParcela(
                    financiamento_id=id,
                    numero_parcela=int(numero_parcela),
                    data_vencimento=datetime.strptime(
                        data_vencimento_str, "%Y-%m-%d"
                    ).date(),
                    valor_principal=valor_principal,
                    valor_juros=valor_juros,
                    valor_seguro=valor_seguro,
                    valor_seguro_2=valor_seguro_2,
                    valor_seguro_3=valor_seguro_3,
                    valor_taxas=valor_taxas,
                    multa=multa,
                    mora=mora,
                    ajustes=ajustes,
                    valor_total_previsto=valor_total_calculado,
                    saldo_devedor=saldo_devedor_corrente,
                    observacoes=observacoes,
                )
                parcelas_para_adicionar.append(nova_parcela)

            db.session.bulk_save_objects(parcelas_para_adicionar)
            db.session.commit()

            flash(
                f"{len(parcelas_para_adicionar)} parcelas importadas com sucesso!",
                "success",
            )
            return redirect(url_for("financiamento.listar_financiamentos"))

        except (ValueError, IndexError) as e:
            db.session.rollback()
            flash(
                (
                    f"Erro ao processar o arquivo CSV na linha {i}. Verifique se todas as "
                    "14 colunas estão presentes e no formato correto (data como AAAA-MM-DD, "
                    f"números com ponto decimal). Detalhe: {e}"
                ),
                "danger",
            )
        except Exception as e:
            db.session.rollback()
            flash(f"Ocorreu um erro inesperado durante a importação: {e}", "danger")

    return render_template(
        "financiamentos/importar_parcelas.html", form=form, financiamento=financiamento
    )


@financiamento_bp.route("/<int:id>/parcelas")
@login_required
def visualizar_parcelas(id):
    financiamento = Financiamento.query.filter_by(
        id=id, usuario_id=current_user.id
    ).first_or_404()

    # Consulta atualizada para buscar a parcela e o valor do movimento relacionado
    parcelas_data = (
        db.session.query(FinanciamentoParcela, ContaMovimento.valor)
        .outerjoin(
            ContaMovimento,
            FinanciamentoParcela.movimento_bancario_id == ContaMovimento.id,
        )
        .filter(FinanciamentoParcela.financiamento_id == id)
        .order_by(FinanciamentoParcela.numero_parcela.asc())
        .all()
    )

    return render_template(
        "financiamentos/parcelas.html",
        financiamento=financiamento,
        parcelas_data=parcelas_data,
    )
