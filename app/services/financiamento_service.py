# app/services/financiamento_service.py

import csv
import io
from datetime import date, datetime
from decimal import ROUND_DOWN, Decimal

from flask import current_app
from flask_login import current_user
from sqlalchemy import func

from app import db
from app.models.conta_model import Conta
from app.models.conta_movimento_model import ContaMovimento
from app.models.conta_transacao_model import ContaTransacao
from app.models.financiamento_parcela_model import FinanciamentoParcela


def _determinar_status_parcela(valor_pago, data_vencimento, hoje):
    """
    Função auxiliar para determinar o status da parcela de forma clara e eficiente.
    """
    if data_vencimento < hoje:
        # Vencimento está no passado
        return "Paga" if valor_pago else "Atrasada"
    else:
        # Vencimento é hoje ou no futuro
        return "Amortizada" if valor_pago else "Pendente"


def importar_e_processar_csv(financiamento, csv_file):
    """
    Processa um arquivo CSV de parcelas para um financiamento, incluindo o status de pagamento.
    """
    try:
        FinanciamentoParcela.query.filter_by(financiamento_id=financiamento.id).delete()
        db.session.flush()

        stream = io.StringIO(csv_file.stream.read().decode("UTF-8"), newline=None)
        csv_reader = csv.reader(stream)
        header = next(csv_reader, None)
        all_rows = list(csv_reader)

        if len(all_rows) != financiamento.prazo_meses:
            message = (
                f"Erro: O arquivo CSV contém {len(all_rows)} parcelas, "
                f"mas o financiamento espera {financiamento.prazo_meses}. "
                "A importação foi cancelada."
            )
            return False, message

        parcelas_para_adicionar = []

        hoje = date.today()

        for i, row in enumerate(all_rows, start=1):
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
                valor_total_previsto_str,
                saldo_devedor_str,
                data_pagamento_str,
                valor_pago_str,
                *observacoes_tuple,
            ) = row

            data_pagamento = (
                datetime.strptime(data_pagamento_str, "%Y-%m-%d").date()
                if data_pagamento_str.strip()
                else None
            )
            valor_pago = Decimal(valor_pago_str) if valor_pago_str.strip() else None

            data_vencimento = datetime.strptime(data_vencimento_str, "%Y-%m-%d").date()
            status = _determinar_status_parcela(valor_pago, data_vencimento, hoje)

            nova_parcela = FinanciamentoParcela(
                financiamento_id=financiamento.id,
                numero_parcela=int(numero_parcela),
                data_vencimento=data_vencimento,
                valor_principal=Decimal(valor_principal_str),
                valor_juros=Decimal(valor_juros_str),
                valor_seguro=Decimal(valor_seguro_str),
                valor_seguro_2=Decimal(valor_seguro_2_str),
                valor_seguro_3=Decimal(valor_seguro_3_str),
                valor_taxas=Decimal(valor_taxas_str),
                multa=Decimal(multa_str),
                mora=Decimal(mora_str),
                ajustes=Decimal(ajustes_str),
                valor_total_previsto=Decimal(valor_total_previsto_str),
                saldo_devedor=Decimal(saldo_devedor_str),
                pago=bool(data_pagamento_str),
                data_pagamento=data_pagamento,
                valor_pago=valor_pago,
                status=status,
                observacoes=(observacoes_tuple[0] if observacoes_tuple else None),
            )
            parcelas_para_adicionar.append(nova_parcela)

        db.session.bulk_save_objects(parcelas_para_adicionar)

        novo_saldo_devedor = db.session.query(
            func.sum(FinanciamentoParcela.valor_principal)
        ).filter(
            FinanciamentoParcela.financiamento_id == financiamento.id,
            FinanciamentoParcela.status != "Paga",
        ).scalar() or Decimal(
            "0.00"
        )

        financiamento.saldo_devedor_atual = novo_saldo_devedor

        db.session.commit()

        return True, f"{len(parcelas_para_adicionar)} parcelas importadas com sucesso!"

    except (ValueError, IndexError) as e:
        db.session.rollback()
        message = (
            f"Erro de formato no arquivo CSV na linha {i}. Verifique se todas as "
            "17 colunas estão presentes e no formato correto."
            f" Detalhe: {e}"
        )
        current_app.logger.error(message)
        return False, message
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Ocorreu um erro inesperado durante a importação: {e}", exc_info=True
        )
        return (
            False,
            "Ocorreu um erro inesperado durante a importação. Consulte os logs.",
        )


def amortizar_parcelas(financiamento, form, ids_parcelas):
    """
    Processa a lógica de negócio para amortizar parcelas de um financiamento.
    Retorna uma tupla (sucesso, mensagem).
    """
    try:
        valor_total_amortizado = form.valor_amortizacao.data
        conta_debito = Conta.query.get(form.conta_id.data)
        data_pagamento = form.data_pagamento.data

        if not ids_parcelas:
            return False, "Nenhuma parcela foi selecionada para amortização."

        saldo_disponivel = conta_debito.saldo_atual
        if conta_debito.tipo in ["Corrente", "Digital"] and conta_debito.limite:
            saldo_disponivel += conta_debito.limite
        if valor_total_amortizado > saldo_disponivel:
            return (
                False,
                f"Saldo insuficiente na conta {conta_debito.nome_banco}. Saldo disponível: R$ {saldo_disponivel:.2f}",
            )

        tipo_transacao = ContaTransacao.query.filter_by(
            usuario_id=current_user.id, transacao_tipo="AMORTIZAÇÃO", tipo="Débito"
        ).first()
        if not tipo_transacao:
            return (
                False,
                'Tipo de transação "AMORTIZAÇÃO" (Débito) não encontrado. Por favor, cadastre-o primeiro.',
            )

        novo_movimento = ContaMovimento(
            usuario_id=current_user.id,
            conta_id=conta_debito.id,
            conta_transacao_id=tipo_transacao.id,
            data_movimento=data_pagamento,
            valor=valor_total_amortizado,
            descricao=f"Amortização do financiamento {financiamento.nome_financiamento}",
        )
        db.session.add(novo_movimento)
        conta_debito.saldo_atual -= valor_total_amortizado
        db.session.flush()

        valor_por_parcela = (valor_total_amortizado / len(ids_parcelas)).quantize(
            Decimal("0.01"), rounding=ROUND_DOWN
        )
        parcelas = FinanciamentoParcela.query.filter(
            FinanciamentoParcela.id.in_(ids_parcelas)
        ).all()

        for parcela in parcelas:
            parcela.status = "Amortizada"
            parcela.data_pagamento = data_pagamento
            parcela.valor_pago = valor_por_parcela
            parcela.movimento_bancario_id = novo_movimento.id
            data_formatada = data_pagamento.strftime("%d/%m/%Y")
            parcela.saldo_devedor = Decimal("0.00")
            parcela.observacoes = f"Amortização em {data_formatada}"

        novo_saldo_devedor = db.session.query(
            func.sum(FinanciamentoParcela.valor_principal)
        ).filter(
            FinanciamentoParcela.financiamento_id == financiamento.id,
            FinanciamentoParcela.status.in_(["Pendente", "Atrasada"]),
        ).scalar() or Decimal(
            "0.00"
        )
        financiamento.saldo_devedor_atual = novo_saldo_devedor

        db.session.commit()
        return True, f"{len(ids_parcelas)} parcelas amortizadas com sucesso!"
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao amortizar parcelas: {e}", exc_info=True)
        return False, "Ocorreu um erro inesperado durante a amortização."
