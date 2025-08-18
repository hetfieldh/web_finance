# app/services/financiamento_service.py

import csv
import io
from datetime import datetime
from decimal import Decimal

from flask import current_app
from sqlalchemy import func

from app import db
from app.models.financiamento_parcela_model import FinanciamentoParcela


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
            pago = bool(data_pagamento)
            status = "Paga" if pago else "Pendente"

            valor_pago = Decimal(valor_pago_str) if valor_pago_str.strip() else None

            nova_parcela = FinanciamentoParcela(
                financiamento_id=financiamento.id,
                numero_parcela=int(numero_parcela),
                data_vencimento=datetime.strptime(
                    data_vencimento_str, "%Y-%m-%d"
                ).date(),
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
                pago=pago,
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
            "15 colunas estão presentes e no formato correto."
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
