import logging
from threading import Lock
from typing import List

import src
import src.api.okvendas as api_okvendas
import src.database.connection as database
import src.database.utils as utils
from src.api.entities.service_fee import ServiceFee
from src.database import queries
from src.database.utils import DatabaseConfig
from src.jobs.system_jobs import OnlineLogger
from src.jobs.utils import executa_comando_sql
from src.log_types import LogType

logger = logging.getLogger()
send_log = OnlineLogger.send_log
lock = Lock()


def job_send_service_fee(job_config: dict):
    """
    Job para realizar a atualização de taxas de serviço
    Args:
        job_config: Configuração do job
    """
    try:
        with lock:
            db_config = utils.get_database_config(job_config)
            logger.info(f"==== THREAD INICIADA - job: {job_config.get('job_name')}")

            send_log(
                job_config.get('job_name'),
                job_config.get('enviar_logs'),
                job_config.get('enviar_logs_debug'),
                "Taxa de Serviço - Iniciado",
                LogType.EXEC,
                "SERVICE_FEE",
            )

            if job_config.get("executar_query_semaforo") == "S":
                executa_comando_sql(db_config, job_config)

            try:
                service_fees = query_service_fees(job_config, db_config)

                if service_fees and len(service_fees) > 0:
                    send_log(
                        job_config.get('job_name'),
                        job_config.get('enviar_logs'),
                        job_config.get('enviar_logs_debug'),
                        f"Total de Taxas de Serviço a serem atualizadas: {len(service_fees)}",
                        LogType.INFO,
                        "SERVICE_FEE",
                    )

                    # Envio em lotes de 50
                    for i in range(0, len(service_fees), 50):
                        batch = service_fees[i:i + 50]
                        send_batch(job_config, db_config, batch)

                else:
                    send_log(
                        job_config.get('job_name'),
                        job_config.get('enviar_logs'),
                        job_config.get('enviar_logs_debug'),
                        "Nao existem taxas de servico a serem enviadas no momento",
                        LogType.WARNING,
                        "SERVICE_FEE",
                    )
            except Exception as e:
                logger.error(f"Erro durante execução do job: {str(e)}")
                send_log(
                    job_config.get('job_name'),
                    job_config.get('enviar_logs'),
                    job_config.get('enviar_logs_debug'),
                    f"Erro durante execucao do job: {str(e)}",
                    LogType.ERROR,
                    "SERVICE_FEE",
                )
    except Exception as e:
        logger.error(f"Erro no job: {str(e)}")
        send_log(
            job_config.get('job_name'),
            job_config.get('enviar_logs'),
            job_config.get('enviar_logs_debug'),
            f"Erro durante execução: {str(e)}",
            LogType.ERROR,
            "SERVICE_FEE",
        )
    finally:
        if lock.locked():
            lock.release()
            logger.info("Lock liberado com segurança (dentro de job_send_service_fee).")


def send_batch(job_config: dict, db_config: DatabaseConfig, batch: List[ServiceFee]):
    """Envia um lote de taxas de serviço para a API."""
    send_log(
        job_config.get('job_name'),
        job_config.get('enviar_logs'),
        job_config.get('enviar_logs_debug'),
        f"Enviando Pacote: {len(batch)}",
        LogType.INFO,
        "SERVICE_FEE",
    )
    response = api_okvendas.post_service_fees(batch)
    validate_response_service_fee(response, db_config, job_config)


def query_service_fees(job_config: dict, db_config: DatabaseConfig) -> List[ServiceFee]:
    """
    Consulta as taxas de serviço para atualizar no banco de dados
    Args:
        job_config: Configuração do job
        db_config: Configuracao do banco de dados

    Returns:
        Lista de taxas de serviço para atualizar
    """
    db = database.Connection(db_config)
    conn = db.get_conect()
    cursor = conn.cursor()
    try:
        newsql = utils.final_query(db_config)
        if src.print_payloads:
            print(newsql)
        cursor.execute(newsql)
        rows = cursor.fetchall()
        columns = [col[0].lower() for col in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]
        cursor.close()
        conn.close()

        if results:
            return [ServiceFee(**fee) for fee in results]
        return []

    except Exception as ex:
        send_log(
            job_config.get('job_name'),
            job_config.get('enviar_logs'),
            job_config.get('enviar_logs_debug'),
            f" Erro ao consultar taxas de servico no banco semaforo: {str(ex)}",
            LogType.ERROR,
            "SERVICE_FEE",
        )
        if src.exibir_interface_grafica:
            raise
    return []


def validate_response_service_fee(response, db_config, job_config):
    """Valida a resposta da API e atualiza o semáforo."""
    if response is not None:
        conexao = database.Connection(db_config)
        conn = conexao.get_conect()
        cursor = conn.cursor()

        for item in response:
            identificador = item.get("codigo_escopo")
            identificador2 = item.get("tipo_escopo")
            sucesso = item.get("sucesso")
            mensagem = item.get("mensagem")

            msgret = "SUCESSO" if sucesso else mensagem

            if not sucesso:
                send_log(
                    job_config.get('job_name'),
                    job_config.get('enviar_logs'),
                    job_config.get('enviar_logs_debug'),
                    f"Mensagem de Retorno: {identificador}, {msgret}",
                    LogType.WARNING,
                    identificador,
                )

            try:
                cursor.execute(
                    queries.get_insert_update_semaphore_command(db_config.db_type),
                    queries.get_command_parameter(
                        db_config.db_type,
                        [
                            identificador,
                            identificador2,
                            27,  # tipo_id para 'taxa_servico'
                            msgret,
                        ],
                    ),
                )
            except Exception as e:
                send_log(
                    job_config.get('job_name'),
                    job_config.get('enviar_logs'),
                    job_config.get('enviar_logs_debug'),
                    f"Erro ao atualizar Taxa de Servico: {identificador}, Erro: {str(e)}",
                    LogType.ERROR,
                    f"{identificador}-{identificador2}",
                )

        cursor.close()
        conn.commit()
        conn.close()
