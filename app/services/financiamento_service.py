# app/services/financiamento_service.py

import csv
import io
from datetime import datetime
from decimal import Decimal

from flask import current_app

from app import db
from app.models.financiamento_parcela_model import FinanciamentoParcela


def importar_e_processar_csv(financiamento, csv_file):
    """
    Processa um arquivo CSV de parcelas para um financiamento.
    Retorna uma tupla (sucesso, mensagem).
    """
    try:
        # Garante que as parcelas existentes sejam removidas antes de uma nova importação
        FinanciamentoParcela.query.filter_by(financiamento_id=financiamento.id).delete()

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

        saldo_devedor_corrente = financiamento.valor_total_financiado
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
                _,
                _,
                *observacoes_tuple,
            ) = row

            valor_principal = Decimal(valor_principal_str)

            valor_total_calculado = (
                valor_principal
                + Decimal(valor_juros_str)
                + Decimal(valor_seguro_str)
                + Decimal(valor_seguro_2_str)
                + Decimal(valor_seguro_3_str)
                + Decimal(valor_taxas_str)
                + Decimal(multa_str)
                + Decimal(mora_str)
                + Decimal(ajustes_str)
            )

            saldo_devedor_corrente -= valor_principal

            nova_parcela = FinanciamentoParcela(
                financiamento_id=financiamento.id,
                numero_parcela=int(numero_parcela),
                data_vencimento=datetime.strptime(
                    data_vencimento_str, "%Y-%m-%d"
                ).date(),
                valor_principal=valor_principal,
                valor_juros=Decimal(valor_juros_str),
                valor_seguro=Decimal(valor_seguro_str),
                valor_seguro_2=Decimal(valor_seguro_2_str),
                valor_seguro_3=Decimal(valor_seguro_3_str),
                valor_taxas=Decimal(valor_taxas_str),
                multa=Decimal(multa_str),
                mora=Decimal(mora_str),
                ajustes=Decimal(ajustes_str),
                valor_total_previsto=valor_total_calculado,
                saldo_devedor=saldo_devedor_corrente,
                observacoes=(observacoes_tuple[0] if observacoes_tuple else None),
            )
            parcelas_para_adicionar.append(nova_parcela)

        db.session.bulk_save_objects(parcelas_para_adicionar)
        financiamento.saldo_devedor_atual = saldo_devedor_corrente
        db.session.commit()

        return True, f"{len(parcelas_para_adicionar)} parcelas importadas com sucesso!"

    except (ValueError, IndexError) as e:
        db.session.rollback()
        message = (
            f"Erro de formato no arquivo CSV na linha {i}. Verifique se todas as "
            "14 colunas estão presentes e no formato correto (data como AAAA-MM-DD, "
            f"números com ponto decimal). Detalhe: {e}"
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
