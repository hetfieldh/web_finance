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
from app.utils import (
    STATUS_AMORTIZADO,
    STATUS_ATRASADO,
    STATUS_PAGO,
    STATUS_PENDENTE,
    TIPO_DEBITO,
)


def _determinar_status_parcela(valor_pago, data_vencimento, hoje):
    if data_vencimento < hoje:
        return STATUS_PAGO if valor_pago else STATUS_ATRASADO
    else:
        return STATUS_AMORTIZADO if valor_pago else STATUS_PENDENTE


def importar_e_processar_csv(financiamento, csv_file):
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

        soma_principal_csv = Decimal("0.00")
        parcelas_temporarias = []
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
                _,
                data_pagamento_str,
                valor_pago_str,
                *observacoes_tuple,
            ) = row

            valor_principal = Decimal(valor_principal_str)
            soma_principal_csv += valor_principal

            data_vencimento_obj = datetime.strptime(
                data_vencimento_str, "%Y-%m-%d"
            ).date()
            data_pagamento = (
                datetime.strptime(data_pagamento_str, "%Y-%m-%d").date()
                if data_pagamento_str.strip()
                else None
            )
            valor_pago = Decimal(valor_pago_str) if valor_pago_str.strip() else None

            status = _determinar_status_parcela(valor_pago, data_vencimento_obj, hoje)
            pago = status in [STATUS_PAGO, STATUS_AMORTIZADO]

            parcelas_temporarias.append(
                {
                    "financiamento_id": financiamento.id,
                    "numero_parcela": int(numero_parcela),
                    "data_vencimento": data_vencimento_obj,
                    "valor_principal": valor_principal,
                    "valor_juros": Decimal(valor_juros_str),
                    "valor_seguro": Decimal(valor_seguro_str),
                    "valor_seguro_2": Decimal(valor_seguro_2_str),
                    "valor_seguro_3": Decimal(valor_seguro_3_str),
                    "valor_taxas": Decimal(valor_taxas_str),
                    "multa": Decimal(multa_str),
                    "mora": Decimal(mora_str),
                    "ajustes": Decimal(ajustes_str),
                    "valor_total_previsto": Decimal(valor_total_previsto_str),
                    "pago": pago,
                    "data_pagamento": data_pagamento,
                    "valor_pago": valor_pago,
                    "status": status,
                    "observacoes": (
                        observacoes_tuple[0] if observacoes_tuple else None
                    ),
                }
            )

        if soma_principal_csv.quantize(
            Decimal("0.01")
        ) != financiamento.valor_total_financiado.quantize(Decimal("0.01")):
            message = (
                f"Erro de validação: O valor total financiado ( {financiamento.valor_total_financiado:,.2f}) "
                f"não corresponde à soma do valor principal das parcelas no arquivo CSV ( {soma_principal_csv:,.2f})."
            )
            return False, message

        saldo_devedor_cumulativo = Decimal("0.00")
        parcelas_para_adicionar = []
        for parcela_data in reversed(parcelas_temporarias):
            saldo_devedor_cumulativo += parcela_data["valor_principal"]
            parcela_data["saldo_devedor"] = saldo_devedor_cumulativo
            parcelas_para_adicionar.append(FinanciamentoParcela(**parcela_data))

        parcelas_para_adicionar.reverse()

        db.session.bulk_save_objects(parcelas_para_adicionar)

        novo_saldo_devedor = db.session.query(
            func.sum(FinanciamentoParcela.valor_principal)
        ).filter(
            FinanciamentoParcela.financiamento_id == financiamento.id,
            FinanciamentoParcela.status.in_([STATUS_PENDENTE, STATUS_ATRASADO]),
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
            "colunas necessárias estão presentes e no formato correto."
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


def amortizar_parcelas(financiamento, form):
    try:
        valor_amortizacao = form.valor_amortizacao.data
        conta_debito = Conta.query.get(form.conta_id.data)
        data_pagamento = form.data_pagamento.data
        estrategia_amortizacao = form.estrategia.data

        saldo_devedor_maximo = financiamento.saldo_devedor_atual
        if valor_amortizacao > saldo_devedor_maximo:
            return (
                False,
                f"O valor da amortização não pode exceder o saldo devedor de  {saldo_devedor_maximo:,.2f}.",
            )

        saldo_disponivel = conta_debito.saldo_atual
        if conta_debito.tipo in ["Corrente", "Digital"] and conta_debito.limite:
            saldo_disponivel += conta_debito.limite
        if valor_amortizacao > saldo_disponivel:
            return (
                False,
                f"Saldo insuficiente na conta {conta_debito.nome_banco}. Saldo disponível:  {saldo_disponivel:,.2f}",
            )

        tipo_transacao = ContaTransacao.query.filter_by(
            usuario_id=current_user.id, transacao_tipo="AMORTIZAÇÃO", tipo=TIPO_DEBITO
        ).first()
        if not tipo_transacao:
            return (
                False,
                'Tipo de transação "AMORTIZAÇÃO" (Débito) não encontrado. Cadastre-o primeiro.',
            )

        novo_movimento = ContaMovimento(
            usuario_id=current_user.id,
            conta_id=conta_debito.id,
            conta_transacao_id=tipo_transacao.id,
            data_movimento=data_pagamento,
            valor=valor_amortizacao,
            descricao=f"Amortização do financiamento {financiamento.nome_financiamento}",
        )
        db.session.add(novo_movimento)
        conta_debito.saldo_atual -= valor_amortizacao
        db.session.flush()

        msg = ""

        if estrategia_amortizacao == "prazo":
            valor_restante = valor_amortizacao
            parcelas_quitadas = 0
            parcela_parcial = False

            parcelas_pendentes = (
                FinanciamentoParcela.query.filter(
                    FinanciamentoParcela.financiamento_id == financiamento.id,
                    FinanciamentoParcela.status.in_([STATUS_PENDENTE, STATUS_ATRASADO]),
                )
                .order_by(FinanciamentoParcela.numero_parcela.desc())
                .all()
            )

            for parcela in parcelas_pendentes:
                if valor_restante <= Decimal("0.00"):
                    break

                if parcela.valor_pago is None:
                    parcela.valor_pago = Decimal("0.00")
                valor_necessario = parcela.valor_principal - parcela.valor_pago

                if valor_restante >= valor_necessario:
                    valor_a_aplicar = valor_necessario
                    valor_restante -= valor_a_aplicar
                    parcela.valor_pago += valor_a_aplicar
                    parcela.status = STATUS_AMORTIZADO
                    parcelas_quitadas += 1
                else:
                    valor_a_aplicar = valor_restante
                    parcela.valor_pago += valor_a_aplicar
                    valor_restante = Decimal("0.00")
                    parcela_parcial = True

                parcela.data_pagamento = data_pagamento
                parcela.movimento_bancario_id = novo_movimento.id
                obs = f"Amort. de  {valor_a_aplicar:,.2f} em {data_pagamento.strftime('%d/%m/%Y')}."
                parcela.observacoes = (
                    (parcela.observacoes + "; " + obs) if parcela.observacoes else obs
                )

            msg = f"Amortização de  {valor_amortizacao:,.2f} realizada para reduzir prazo. {parcelas_quitadas} parcelas foram quitadas."
            if parcela_parcial:
                msg += " Uma parcela foi parcialmente paga."

        elif estrategia_amortizacao == "parcela":
            parcelas_pendentes = (
                FinanciamentoParcela.query.filter(
                    FinanciamentoParcela.financiamento_id == financiamento.id,
                    FinanciamentoParcela.status.in_([STATUS_PENDENTE, STATUS_ATRASADO]),
                )
                .order_by(FinanciamentoParcela.numero_parcela.asc())
                .all()
            )

            if not parcelas_pendentes:
                return False, "Não há parcelas pendentes para amortizar."

            qtd_parcelas = len(parcelas_pendentes)
            reducao_por_parcela = (valor_amortizacao / qtd_parcelas).quantize(
                Decimal("0.01"), rounding=ROUND_DOWN
            )
            valor_total_distribuido = reducao_por_parcela * qtd_parcelas
            ajuste_primeira_parcela = valor_amortizacao - valor_total_distribuido

            for i, parcela in enumerate(parcelas_pendentes):
                valor_reducao = reducao_por_parcela
                if i == 0:
                    valor_reducao += ajuste_primeira_parcela

                parcela.valor_principal -= valor_reducao
                parcela.valor_total_previsto -= valor_reducao

                obs = f"Amort. de  {valor_reducao:,.2f} em {data_pagamento.strftime('%d/%m/%Y')} para reduzir valor da parcela."
                parcela.observacoes = (
                    (parcela.observacoes + "; " + obs) if parcela.observacoes else obs
                )

            msg = f"Amortização de  {valor_amortizacao:,.2f} distribuída para reduzir o valor de {qtd_parcelas} parcelas futuras."

        novo_saldo_devedor = db.session.query(
            func.sum(
                FinanciamentoParcela.valor_principal
                - func.coalesce(FinanciamentoParcela.valor_pago, 0)
            )
        ).filter(
            FinanciamentoParcela.financiamento_id == financiamento.id,
            FinanciamentoParcela.status.in_([STATUS_PENDENTE, STATUS_ATRASADO]),
        ).scalar() or Decimal(
            "0.00"
        )
        financiamento.saldo_devedor_atual = novo_saldo_devedor

        db.session.commit()
        return True, msg.strip()

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao amortizar parcelas: {e}", exc_info=True)
        return False, "Ocorreu um erro inesperado durante a amortização."
