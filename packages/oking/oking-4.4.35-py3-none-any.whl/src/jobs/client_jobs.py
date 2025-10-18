import logging
import time
from datetime import datetime
from typing import Dict, List
import src
from src.jobs.utils import executa_comando_sql

from src.api.entities.client_erp_code import ClienteErpCode
from src.api.entities.cliente_aprovado import ApprovedClient
from src.database import utils
from src.api import okinghub as api_okHUB
import src.api.okvendas as api_okvendas
from src.api.entities.cliente import Cliente, Endereco

import src.database.connection as database
from src.database import queries
from src.database.entities.client import Client
from src.database.queries import IntegrationType
from src.database.utils import DatabaseConfig
from src.jobs.system_jobs import OnlineLogger
from threading import Lock
from src.log_types import LogType

logger = logging.getLogger()
send_log = OnlineLogger.send_log

lock = Lock()


def job_send_clients(job_config: dict):
    with lock:
        """
        Job para realizar atualização de clientes
        Args:
            job_config: Configuração do job
        """
        db_config = utils.get_database_config(job_config)
        # Exibe mensagem monstrando que a Thread foi Iniciada
        logger.info(f'==== THREAD INICIADA -job: ' + job_config.get('job_name'))

        # LOG de Inicialização do Método - Para acompanhamento de execução
        send_log(
            job_config.get('job_name'),
            job_config.get('enviar_logs'),
            job_config.get('enviar_logs_debug'),
            f'Cliente - Iniciado',
            LogType.EXEC,
            'CLIENTE')
        if job_config['executar_query_semaforo'] == 'S':
            executa_comando_sql(db_config, job_config)
        try:
            # CORREÇÃO: Verificar tanto okvendas quanto okinghub
            operacao = src.client_data.get('operacao', '').lower()
            logger.info(f"job_send_clients | operacao detectada: '{operacao}'")
            
            if 'okvendas' in operacao or 'okinghub' in operacao:
                logger.info(f"job_send_clients | Usando get_clients (banco semáforo)")
                db_clients = get_clients(job_config, db_config)

                logger.info(f'==== Consultou os Clientes  ')
                if len(db_clients) <= 0:
                    send_log(
                        job_config.get('job_name'),
                        job_config.get('enviar_logs'),
                        job_config.get('enviar_logs_debug'),
                        f'Nenhum cliente retornado para integracao no momento',
                        LogType.WARNING,
                        'CLIENTE'
                    )
                    return

                logger.info(f'==== Vai Inserir os Clientes na Semaforo')
                clients_inserted = insert_update_semaphore_client_jobs(job_config, db_config, db_clients)
                if not clients_inserted:
                    send_log(
                        job_config.get('job_name'),
                        job_config.get('enviar_logs'),
                        job_config.get('enviar_logs_debug'),
                        f'Nao foi possivel inserir os clientes no banco semaforo',
                        LogType.ERROR,
                        'CLIENTE')
                    return

                # Criar clientes com campos dinâmicos
                clients = []
                for c in db_clients:
                    # Campos obrigatórios/principais
                    client_data = {
                        'nome': c.name,
                        'razao_social': c.company_name,
                        'sexo': 'M',
                        'data_nascimento': None,
                        'data_bloqueio': c.blocked_date,
                        'data_constituicao': None,
                        'cpf': c.cpf or "",
                        'cnpj': c.cnpj,
                        'endereco': Endereco(
                            True, c.address_type, c.address, c.zipcode, c.number, c.complement,
                            c.neighbourhood, c.city, c.state, 
                            c.residential_phone or c.mobile_phone, str(), c.reference, 'BR',
                            c.ibge_code
                        ),
                        'email': c.email,
                        'codigo_referencia': c.client_erp,
                        'telefone_residencial': c.residential_phone,
                        'telefone_celular': c.mobile_phone,
                        'inscricao_estadual': c.state_registration,
                        'compra_liberada': c.purchase_released,
                        'site_pertencente': c.belonging_site,
                        'tipo_pessoa': c.person_type,
                        'limite_credito': int(c.credit_limit) if c.credit_limit is not None else c.credit_limit,
                        'codigo_representante': c.representative_code,
                        'origem_cadastro': 'E'
                    }
                    
                    # CAMPOS EXTRAS DINÂMICOS: Adiciona todos os campos extras do objeto Client
                    # que não são os campos principais já mapeados
                    campos_principais = {
                        'name', 'company_name', 'blocked_date', 'cpf', 'cnpj', 
                        'address_type', 'address', 'zipcode', 'number', 'complement',
                        'neighbourhood', 'city', 'state', 'residential_phone', 'mobile_phone',
                        'reference', 'ibge_code', 'email', 'client_erp', 'state_registration',
                        'purchase_released', 'belonging_site', 'person_type', 'credit_limit',
                        'representative_code'
                    }
                    
                    # Adiciona campos extras dinamicamente
                    campos_extras_adicionados = []
                    for attr_name in dir(c):
                        if (not attr_name.startswith('_') and 
                            attr_name not in campos_principais and
                            not callable(getattr(c, attr_name))):
                            try:
                                valor = getattr(c, attr_name)
                                if valor is not None:
                                    client_data[attr_name] = valor
                                    campos_extras_adicionados.append(f"{attr_name}={valor}")
                            except AttributeError:
                                pass
                    
                    # Log dos campos extras adicionados (apenas para o primeiro cliente)
                    if len(clients) == 0 and campos_extras_adicionados:
                        logger.info(f"job_send_clients | Campos extras detectados e adicionados: {', '.join(campos_extras_adicionados)}")
                    
                    # Criar objeto Cliente com todos os campos
                    clients.append(Cliente(**client_data))
                
                total = len(clients)
                send_log(
                    job_config.get('job_name'),
                    job_config.get('enviar_logs'),
                    job_config.get('enviar_logs_debug'),
                    f'Enviando {total} clientes via api {operacao}',
                    LogType.INFO,
                    'CLIENTE'
                )
                
                # DECISÃO: Qual API usar baseado na operação
                if 'okvendas' in operacao:
                    logger.info(f"job_send_clients | Usando API OKVendas")
                    # Processamento para OKVendas (com paginação de 10 em 10)
                    page = 10
                    limit = 10 if total > 10 else total
                    offset = 0

                    partial_clients = clients[offset:limit]
                    while limit <= total:
                        try:
                            # Delay de 2 segundos antes de chamar a API
                            time.sleep(2)
                            
                            results = api_okvendas.post_clients(partial_clients)
                            
                            if len(results) < 1:
                                send_log(
                                    job_config.get('job_name'),
                                    job_config.get('enviar_logs'),
                                    job_config.get('enviar_logs_debug'),
                                    f'Nenhum resultado retornado pela API',
                                    LogType.WARNING,
                                    'CLIENTE')
                            else:
                                for res in results:
                                    for c in clients:
                                        if res.identifiers[0].__contains__(c.cpf or c.cnpj):
                                            identificador = c.cpf or c.cnpj
                                            break
                                    if protocol_semaphore_send_clients(job_config,
                                                                       db_config,
                                                                       res,
                                                                       identificador):
                                        send_log(
                                            job_config.get('job_name'),
                                            job_config.get('enviar_logs'),
                                            job_config.get('enviar_logs_debug'),
                                            f'Cliente do cpf/cnpj: {identificador} protocolado no banco semaforo',
                                            LogType.INFO,
                                            'CLIENTE')
                                    else:
                                        send_log(
                                            job_config.get('job_name'),
                                            job_config.get('enviar_logs'),
                                            job_config.get('enviar_logs_debug'),
                                            f'Falha ao protocolar o cliente do cpf/cnpj: {identificador}',
                                            LogType.WARNING,
                                            'CLIENTE')

                                failed_results = [result for result in results if result.status > 1]

                                if len(failed_results) > 0:
                                    for fr in failed_results:
                                        for c in partial_clients:
                                            time.sleep(0.3)
                                            send_log(
                                                job_config.get('job_name'),
                                                job_config.get('enviar_logs'),
                                                job_config.get('enviar_logs_debug'),
                                                f'Falha ao integrar cliente cod.erp {c.codigo_referencia}, '
                                                f' cpf/cnpj {c.cnpj if c.cpf is None else c.cpf}: {fr.message}',
                                                LogType.ERROR,
                                                c.codigo_referencia)
                        
                        except Exception as e:
                            send_log(
                                job_config.get('job_name'),
                                job_config.get('enviar_logs'),
                                job_config.get('enviar_logs_debug'),
                                f'Erro ao processar lote offset {offset}-{limit} (continuando): {str(e)}',
                                LogType.ERROR,
                                'CLIENTE')
                            logger.exception("Erro detalhado ao processar lote:")

                        limit = limit + page
                        offset = offset + page
                        partial_clients = clients[offset:limit]
                
                elif 'okinghub' in operacao:
                    logger.info(f"job_send_clients | Usando API OKingHub")
                    # Processamento para OKingHub (com paginação de 50 em 50)
                    api_clients = []
                    for client in clients:
                        if len(api_clients) < 50:
                            api_clients.append(client)
                        else:
                            try:
                                send_log(
                                    job_config.get('job_name'),
                                    job_config.get('enviar_logs'),
                                    job_config.get('enviar_logs_debug'),
                                    f'Enviando Pacote: {len(api_clients)}',
                                    LogType.INFO,
                                    'CLIENTE')
                                
                                # Delay de 2 segundos antes de chamar a API
                                time.sleep(2)
                                
                                response = api_okHUB.post_clients(api_clients)
                                api_clients = []
                                
                                send_log(
                                    job_config.get('job_name'),
                                    job_config.get('enviar_logs'),
                                    job_config.get('enviar_logs_debug'),
                                    f'Tratando retorno',
                                    LogType.INFO,
                                    'CLIENTE')
                                
                                validate_response_client(response, db_config, job_config)
                                
                            except Exception as e:
                                # Limpa o lote para continuar com o próximo
                                api_clients = []
                                send_log(
                                    job_config.get('job_name'),
                                    job_config.get('enviar_logs'),
                                    job_config.get('enviar_logs_debug'),
                                    f'Erro ao enviar lote de clientes (continuando com próximo lote): {str(e)}',
                                    LogType.ERROR,
                                    'CLIENTE')
                                logger.exception("Erro detalhado ao enviar lote:")

                    # Envia o que sobrou (se houver)
                    if len(api_clients) > 0:
                        try:
                            send_log(
                                job_config.get('job_name'),
                                job_config.get('enviar_logs'),
                                job_config.get('enviar_logs_debug'),
                                f'Enviando Pacote: {len(api_clients)}',
                                LogType.INFO,
                                'CLIENTE')
                            
                            # Delay de 2 segundos antes de chamar a API
                            time.sleep(2)
                            
                            response = api_okHUB.post_clients(api_clients)
                            
                            send_log(
                                job_config.get('job_name'),
                                job_config.get('enviar_logs'),
                                job_config.get('enviar_logs_debug'),
                                f'Tratando retorno',
                                LogType.INFO,
                                'CLIENTE')
                            
                            validate_response_client(response, db_config, job_config)
                            
                        except Exception as e:
                            send_log(
                                job_config.get('job_name'),
                                job_config.get('enviar_logs'),
                                job_config.get('enviar_logs_debug'),
                                f'Erro ao enviar último lote de clientes: {str(e)}',
                                LogType.ERROR,
                                'CLIENTE')
                            logger.exception("Erro detalhado ao enviar último lote:")

            else:
                # Código original para quando não é okvendas nem okinghub
                clients = query_clients_erp(job_config, db_config)
                if clients is not None and len(clients) > 0:
                    send_log(
                        job_config.get('job_name'),
                        job_config.get('enviar_logs'),
                        job_config.get('enviar_logs_debug'),
                        f'Clientes para atualizar: {len(clients)}',
                        LogType.INFO,
                        'CLIENTE')

                    api_clients = []
                    for client in clients:
                        if api_clients.__len__() < 50:
                            api_clients.append(client)
                        else:
                            try:
                                send_log(
                                    job_config.get('job_name'),
                                    job_config.get('enviar_logs'),
                                    job_config.get('enviar_logs_debug'),
                                    f'Enviando Pacote: {api_clients.__len__()}',
                                    LogType.INFO,
                                    'CLIENTE')
                                
                                # Delay de 2 segundos antes de chamar a API
                                time.sleep(2)
                                
                                response = api_okHUB.post_clients(api_clients)
                                api_clients = []
                                
                                send_log(
                                    job_config.get('job_name'),
                                    job_config.get('enviar_logs'),
                                    job_config.get('enviar_logs_debug'),
                                    f'Tratando retorno',
                                    LogType.INFO,
                                    'CLIENTE')
                                
                                validate_response_client(response, db_config, job_config)
                                
                            except Exception as e:
                                # Limpa o lote para continuar com o próximo
                                api_clients = []
                                send_log(
                                    job_config.get('job_name'),
                                    job_config.get('enviar_logs'),
                                    job_config.get('enviar_logs_debug'),
                                    f'Erro ao enviar lote (continuando): {str(e)}',
                                    LogType.ERROR,
                                    'CLIENTE')
                                logger.exception("Erro detalhado ao enviar lote:")

                    if api_clients.__len__() > 0:
                        try:
                            send_log(
                                job_config.get('job_name'),
                                False,
                                job_config.get('enviar_logs_debug'),
                                f'Enviando Pacote: {api_clients.__len__()}',
                                LogType.INFO,
                                'CLIENTE')
                            
                            # Delay de 2 segundos antes de chamar a API
                            time.sleep(2)
                            
                            response = api_okHUB.post_clients(api_clients)
                            
                            send_log(
                                job_config.get('job_name'),
                                False,
                                job_config.get('enviar_logs_debug'),
                                f'Tratando retorno',
                                LogType.INFO,
                                'CLIENTE')
                            
                            validate_response_client(response, db_config, job_config)
                            
                        except Exception as e:
                            send_log(
                                job_config.get('job_name'),
                                job_config.get('enviar_logs'),
                                job_config.get('enviar_logs_debug'),
                                f'Erro ao enviar último lote: {str(e)}',
                                LogType.ERROR,
                                'CLIENTE')
                            logger.exception("Erro detalhado ao enviar último lote:")

                else:
                    send_log(
                        job_config.get('job_name'),
                        job_config.get('enviar_logs'),
                        job_config.get('enviar_logs_debug'),
                        'Não existem clientes a serem inseridos no momento',
                        LogType.WARNING,
                        'CLIENTE')

        except Exception as e:
            send_log(
                job_config.get('job_name'),
                job_config.get('enviar_logs'),
                job_config.get('enviar_logs_debug'),
                f'Erro na integracao de clientes: {str(e)}',
                LogType.ERROR,
                'CLIENTE')


def job_send_approved_clients(job_config: dict) -> None:
    with lock:
        """
        Job para realizar o envio de clientes B2B aprovados para o ERP

        Args:
            job_config: Configuração do job obtida na api do oking
        """
        logger.info(f'==== THREAD INICIADA -job: ' + job_config.get('job_name'))
        # LOG de Inicialização do Método - Para acompanhamento de execução
        send_log(
            job_config.get('job_name'),
            job_config.get('enviar_logs'),
            job_config.get('enviar_logs_debug'),
            f'Cliente Aprovado - Iniciado',
            LogType.EXEC,
            'CLIENTEAPROVADO')
        try:
            # 1 Consultar os clientes na api
            send_log(
                job_config.get('job_name'),
                job_config.get('enviar_logs'),
                job_config.get('enviar_logs_debug'),
                f'Consultando clientes aprovados na api okvendas',
                LogType.INFO,
                'CLIENTEAPROVADO')
            clients = api_okvendas.get_approved_clients()
            send_log(
                job_config.get('job_name'),
                job_config.get('enviar_logs'),
                job_config.get('enviar_logs_debug'),
                f'Encontrado {len(clients.data)} clientes aprovados',
                LogType.INFO,
                'CLIENTEAPROVADO')

            # 2 Inserir no banco semaforo
            send_log(
                job_config.get('job_name'),
                job_config.get('enviar_logs'),
                job_config.get('enviar_logs_debug'),
                f'Inserindo clientes aprovados no banco semaforo',
                LogType.INFO,
                'CLIENTEAPROVADO')
            db_config = utils.get_database_config(job_config)
            if job_config['executar_query_semaforo'] == 'S':
                executa_comando_sql(db_config, job_config)
            inserted_clients = insert_approved_clients(db_config, clients.data)

            # 3 Disparar nova procedure
            for client in [client_id for client_id, inserted in inserted_clients.items() if inserted]:
                client_data = [c for c in clients.data if c.id == client][0]
                client_erp = None
                try:
                    # 4 Receber codigo erp do cliente da procedure
                    send_log(
                        job_config.get('job_name'),
                        job_config.get('enviar_logs'),
                        job_config.get('enviar_logs_debug'),
                        f'Disparando procedure para o cliente {client}',
                        LogType.INFO,
                        'CLIENTE')
                    client_id_sem = get_semaphore_client_id(db_config, client_data)
                    client_erp = run_approved_clients_procedure(db_config, job_config.get('db_seller'), client_id_sem)
                    if client_erp is None:
                        raise 'Codigo erp do cliente nao retornado ou nao foi possivel obter da saida da procedure'

                    # 5 Enviar codigo erp do cliente para api okvendas
                    saved = api_okvendas.put_client_erp_code(
                        ClienteErpCode(client_data.cpf or client_data.cnpj, client_erp))
                    if saved:
                        send_log(
                            job_config.get('job_name'),
                            job_config.get('enviar_logs'),
                            job_config.get('enviar_logs_debug'),
                            f'Codigo erp {client_erp} do cliente {client} (id semaforo) salvo com sucesso no okvendas',
                            LogType.INFO,
                            'CLIENTEAPROVADO')
                    else:
                        send_log(
                            job_config.get('job_name'),
                            job_config.get('enviar_logs'),
                            job_config.get('enviar_logs_debug'),
                            f'Nao foi possivel salvar o codigo erp {client_erp} do cliente {client} no okvendas',
                            LogType.ERROR,
                            'CLIENTEAPROVADO')
                        continue

                    # 6 Protocolar no semaforo
                    protocoled = protocol_clients(db_config, [client_erp])
                    if protocoled:
                        send_log(
                            job_config.get('job_name'),
                            job_config.get('enviar_logs'),
                            job_config.get('enviar_logs_debug'),
                            f'Cliente {client} (id semaforo) com codigo erp {client_erp} '
                            f'protocolado com sucesso no banco semaforo',
                            LogType.INFO,
                            'CLIENTEAPROVADO')
                    else:
                        send_log(
                            job_config.get('job_name'),
                            job_config.get('enviar_logs'),
                            job_config.get('enviar_logs_debug'),
                            f'Nao foi possivel protocolar o cliente {client} (id semaforo) com codigo erp {client_erp}',
                            LogType.ERROR,
                            'CLIENTEAPROVADO')
                        continue
                except Exception as e:
                    send_log(
                        job_config.get('job_name'),
                        job_config.get('enviar_logs'),
                        job_config.get('enviar_logs_debug'),
                        f'Erro durante execucao da procedure do cliente {client} (id semaforo): {str(e)}',
                        LogType.ERROR,
                        'CLIENTEAPROVADO')

        except Exception as e:
            send_log(
                job_config.get('job_name'),
                job_config.get('enviar_logs'),
                job_config.get('enviar_logs_debug'),
                f'Erro nao esperado na integracao de clientes aprovados: {str(e)}',
                LogType.ERROR,
                'CLIENTEAPROVADO')


def query_clients_erp(job_config: dict, db_config: DatabaseConfig):
    """
    Consulta os clientes para atualizar no banco de dados
    Args:
        job_config: Configuração do job
        db_config: Configuração do banco de dados

    Returns:
        Lista de clientes para atualizar
    """
    db = database.Connection(db_config)
    conn = db.get_conect()
    cursor = conn.cursor()
    try:
        newsql = utils.final_query(db_config)
        if src.print_payloads:
            print(newsql)
        cursor.execute(newsql.lower())
        rows = cursor.fetchall()
        columns = [col[0].lower() for col in cursor.description]
        results = list(dict(zip(columns, row)) for row in rows)
        cursor.close()
        conn.close()

        clients = []

        if len(results) > 0:
            clients = client_dict(results)
        return clients

    except Exception as ex:
        if src.exibir_interface_grafica:
            raise
        else:
            send_log(
                job_config.get('job_name'),
                job_config.get('enviar_logs'),
                job_config.get('enviar_logs_debug'),
                f' Erro ao consultar clientes no banco semaforo: {str(ex)}',
                LogType.ERROR,
                'CLIENTE')


def client_dict(clients):
    lista = []
    for row in clients:
        pdict = {
            'token': str(src.client_data.get('token_oking')),
            'kdm': str(row['kdm']),
            'agente': str(row['agente']),
            'unidade': str(row['unidade']),
            'codigo_cliente': str(row['codigo_cliente']),
            'nome': str(row['nome']),
            'cnpj': str(row['cnpj']).replace(" ", "") if row['cnpj'] is not None else None,
            'data_cadastro': str(row['data_cadastro']),
            'ddd': int(row['ddd']),
            'telefone': str(row['telefone']),
            'email': str(row['email']),
            'endereco': str(row['endereco']),
            'numero': int(row['numero']),
            'bairro': str(row['bairro']),
            'uf': str(row['uf']),
            'faturamento_anual_total': int(row['faturamento_anual_total']),
            'consumo_cimento': float(row['consumo_cimento']),
            'percentual_faturamento_cimento': int(row['percentual_faturamento_cimento']),
            'canal': str(row['canal']),
            'municipio': str(row['municipio']),
            'uf_municipio': str(row['uf_municipio']),
            'codigo_ibge': str(row['codigo_ibge']),
            "cep": str(row['cep']),
            "contato": str(row['contato']),
            "contato_cargo": str(row['contato_cargo']),
            "canal_segmento": str(row['canal_segmento']),
            "status": str(row['status']),
            "vendedor": str(row['vendedor']),
            "ultima_atualizacao": None,
            "segmento_cliente": str(row['segmento_cliente']),
            "marca_exclusivo": str(row['marca_exclusivo']),
            "multimarca_percentual": int(row['multimarca_percentual']),
            "marca_principal_concorrente": str(row['marca_principal_concorrente']),
            "marca_segundo_concorrente": str(row['marca_segundo_concorrente']),
        }
        lista.append(pdict)

    return lista


def validate_response_client(response, db_config, job_config):
    """
    Valida a resposta da API e atualiza o semáforo
    """
    # Validações de segurança
    if response is None:
        logger.warning("validate_response_client | Resposta é None")
        return
    
    # Se response é uma string (erro da API), loga e retorna
    if isinstance(response, str):
        logger.error(f"validate_response_client | API retornou erro (string): {response}")
        send_log(
            job_config.get('job_name'),
            job_config.get('enviar_logs'),
            job_config.get('enviar_logs_debug'),
            f'API retornou erro: {response[:200]}',  # Limita tamanho do log
            LogType.ERROR,
            'CLIENTE')
        return
    
    # Se não é uma lista, tenta converter
    if not isinstance(response, list):
        logger.error(f"validate_response_client | Resposta não é uma lista: {type(response)}")
        return
    
    try:
        conexao = database.Connection(db_config)
        conn = conexao.get_conect()
        cursor = conn.cursor()

        # Percorre todos os registros
        for item in response:
            try:
                # Validação de atributos do item
                if not hasattr(item, 'identificador'):
                    logger.warning(f"validate_response_client | Item não tem atributo 'identificador': {item}")
                    continue
                
                identificador = item.identificador
                identificador2 = getattr(item, 'identificador2', '')
                
                if item.sucesso == 1 or item.sucesso == 'true':
                    msgret = 'SUCESSO'
                else:
                    # Suporta tanto 'Message' quanto 'message'
                    message = getattr(item, 'Message', getattr(item, 'message', 'Erro desconhecido'))
                    msgret = str(message)[:150]
                    send_log(
                        job_config.get('job_name'),
                        job_config.get('enviar_logs'),
                        job_config.get('enviar_logs_debug'),
                        f'Erro ao atualizar Cliente {identificador}: {msgret}',
                        LogType.WARNING,
                        f'{identificador}-{identificador2}')
                
                cursor.execute(queries.get_insert_update_semaphore_command(db_config.db_type),
                               queries.get_command_parameter(db_config.db_type, [identificador, identificador2,
                                                                                 IntegrationType.CLIENTE.value,
                                                                                 msgret]))
            except Exception as e:
                logger.error(f"validate_response_client | Erro ao processar item individual: {str(e)}")
                send_log(
                    job_config.get('job_name'),
                    job_config.get('enviar_logs'),
                    job_config.get('enviar_logs_debug'),
                    f'Erro ao processar item da resposta: {str(e)}',
                    LogType.ERROR,
                    'CLIENTE')
        
        cursor.close()
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.exception(f"validate_response_client | Erro geral: {str(e)}")
        send_log(
            job_config.get('job_name'),
            job_config.get('enviar_logs'),
            job_config.get('enviar_logs_debug'),
            f'Erro ao validar resposta da API: {str(e)}',
            LogType.ERROR,
            'CLIENTE')


def insert_approved_clients(db_config: DatabaseConfig, clients: List[ApprovedClient]) -> Dict[int, bool]:
    """
    Insere os clientes aprovados no banco semaforo

    Args:
        db_config: Configuracao do banco de dados
        clients: Lista de clientes aprovados vindos da api okvendas

    Returns:
        Quantidade de clientes inseridos
    """
    with database.Connection(db_config).get_conect() as conn:
        results: Dict[int, bool] = {}
        for c in clients:
            with conn.cursor() as cursor:
                existent_client: int = None
                try:
                    existent_client = get_semaphore_client_id(db_config, c)
                except Exception:
                    pass

                address = [a for a in c.addresses if a.id == c.address_id] or c.addresses[0]
                # Se nao existir um endereco na lista de enderecos que esteja relacionado com o cliente,
                # pega o primeiro endereco ordenado
                address = address[0] if isinstance(address, list) else address
                if existent_client is None or existent_client <= 0:
                    cursor.execute(queries.get_insert_in_clients(db_config.db_type),
                                   queries.get_command_parameter(db_config.db_type, [
                                       c.cpf,
                                       c.cnpj,
                                       datetime.now(),
                                       c.name,
                                       c.corporate_name,
                                       c.cpf,
                                       c.cnpj,
                                       c.email,
                                       c.home_phone,
                                       c.mobile_phone,
                                       address.zipcode,
                                       address.type,
                                       address.address,
                                       address.number,
                                       address.complement,
                                       address.neighbourhood,
                                       address.city,
                                       address.state,
                                       address.reference,
                                       'IN',  # IN pois esta indo para o ERP
                                       datetime.now(),
                                       address.ibge_code,
                                       c.state_registration,
                                       c.registration_origin,
                                       c.representative_code
                                   ]))
                else:
                    cursor.execute(queries.get_update_in_clients(db_config.db_type),
                                   queries.get_command_parameter(db_config.db_type, [datetime.now(), existent_client]))

                results[c.id] = cursor.rowcount > 0

        conn.commit()
        return results


def get_semaphore_client_id(db_config: DatabaseConfig, client_data: ApprovedClient) -> int:
    with database.Connection(db_config).get_conect() as conn:
        cursor = conn.cursor(buffered=True) if db_config.db_type.lower() == 'mysql' else conn.cursor()
        if client_data.cpf is not None and client_data.cpf != '':
            cursor.execute(queries.get_query_client_cpf(db_config.db_type),
                           queries.get_command_parameter(db_config.db_type, [client_data.cpf]))
        elif client_data.cnpj is not None and client_data.cnpj != '':
            cursor.execute(queries.get_query_client_cnpj(db_config.db_type),
                           queries.get_command_parameter(db_config.db_type, [client_data.cnpj]))

        res = cursor.fetchone()
        if res is None:
            raise 'Cliente nao encontrao no banco semaforo'

        cursor.close()
        client_id, = res
        return client_id


def run_approved_clients_procedure(db_config: DatabaseConfig, seller_id: int, client_id: int) -> str:
    """
    Dispara a procedure de integracao de clientes aprovados

    Args:
        seller_id: Id da loja
        db_config: Configuracao do banco de dados
        client_id: Id da tabela OPENK_SEMAFORO.CLIENTE

    Returns:
        Codigo do cliente no ERP
    """
    with database.Connection(db_config).get_conect() as conn:
        try:
            with conn.cursor() as cursor:
                if db_config.is_sql_server():
                    cursor.execute('exec openk_semaforo.sp_cliente_aprovado @cliente_id = ?, @loja_id = ?', client_id,
                                   seller_id)
                    client_erp_res = cursor.fetchone()
                    if client_erp_res is not None:
                        client_erp, = client_erp_res
                    else:
                        raise 'Nao foi possivel obter o codigo cliente_erp da procedure'
                elif db_config.is_oracle():
                    client_erp_out_value = cursor.var(str)
                    cursor.callproc('OPENK_SEMAFORO.SP_CLIENTE_APROVADO', [client_id, seller_id, client_erp_out_value])
                    client_erp = client_erp_out_value.getvalue()
                elif db_config.is_mysql():
                    result = cursor.callproc('openk_semaforo.SP_CLIENTE_APROVADO', [client_id, seller_id, (0, 'CHAR')])
                    client_erp = result[1]
        except Exception:
            conn.rollback()
            raise

        conn.commit()

    return client_erp


def protocol_clients(db_config: DatabaseConfig, client_erp_codes: List[str]) -> bool:
    conn = database.Connection(db_config).get_conect()
    cursor = conn.cursor()

    cursor.executemany(queries.get_out_client_protocol_command(db_config.db_type),
                       [queries.get_command_parameter(db_config.db_type, [c]) for c in client_erp_codes])
    result = cursor.rowcount

    cursor.close()
    conn.commit()
    conn.close()

    return result > 0


def get_clients(job_config: dict, db_config: DatabaseConfig) -> List[Client]:
    conn = database.Connection(db_config).get_conect()
    cursor = conn.cursor()
    try:
        logger.info(f"get_clients | Construindo query para banco semáforo")
        logger.info(f"get_clients | db_config: {db_config.__dict__}")
        
        newsql = utils.final_query(db_config)
        
        logger.info(f"get_clients | Query gerada: {newsql}")
        
        if src.print_payloads:
            print(newsql)
            
        cursor.execute(newsql)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        cursor.close()
        conn.close()

        clients_list = []
        new: dict = {}
        for row in results:
            for i, c in enumerate(columns):
                new[c.lower()] = row[i]

            clients_list.append(new.copy())

        logger.info(f"get_clients | Total de clientes recuperados: {len(clients_list)}")
        
        clients = [Client(**c) for c in clients_list]
        return clients
        
    except KeyError as ke:
        logger.error(f"get_clients | Erro de chave não encontrada: {str(ke)}")
        logger.error(f"get_clients | db_config disponível: {db_config.__dict__ if hasattr(db_config, '__dict__') else db_config}")
        raise
    except Exception as ex:
        logger.error(f"get_clients | Erro genérico: {str(ex)}")
        if src.exibir_interface_grafica:
            raise ex
        else:
            send_log(
                job_config.get('job_name'),
                job_config.get('enviar_logs'),
                job_config.get('enviar_logs_debug'),
                f' Erro ao consultar clientes: {str(ex)}',
                LogType.ERROR,
                'CLIENTE')


def insert_update_semaphore_client_jobs(job_config: dict, db_config: DatabaseConfig, lists: List[Client]) -> bool:
    """
    Insere os imposts no banco semáforo
    Args:
        job_config: Configuração do job
        db_config: Configuracao do banco de dados
        lists: Lista de clientes

    Returns:
        Boleano indicando se foram inseridos 1 ou mais registros
    """
    try:
        params = [(li.cnpj if li.cpf is None else li.cpf, ' ', IntegrationType.CLIENTE.value, 'SUCESSO') for li in
                  lists]

        db = database.Connection(db_config)
        conn = db.get_conect()
        cursor = conn.cursor()
        for p in params:
            cursor.execute(queries.get_insert_update_semaphore_command(db_config.db_type),
                           queries.get_command_parameter(db_config.db_type, list(p)))
        count = cursor.rowcount
        cursor.close()
        conn.commit()
        conn.close()
        return count > 0

    except Exception as ex:
        send_log(
            job_config.get('job_name'),
            job_config.get('enviar_logs'),
            job_config.get('enviar_logs_debug'),
            f' Erro ao atualizar clientes no banco semaforo: {str(ex)}',
            LogType.ERROR,
            'CLIENTE')

    return False


def protocol_semaphore_send_clients(job_config: dict, db_config: DatabaseConfig, result, identificador) -> bool:
    db = database.Connection(db_config)
    conn = db.get_conect()
    cursor = conn.cursor()
    print()
    try:
        if result is not None:
            if result.status or result.status == 1:
                msgret = 'SUCESSO'
            else:
                msgret = f'Falha ao integrar o cliente {identificador}: {result.message}'
            cursor.execute(queries.get_protocol_semaphore_id_command(db_config.db_type),
                           queries.get_command_parameter(db_config.db_type, [msgret, identificador]))
        count = cursor.rowcount
        cursor.close()
        conn.commit()
        conn.close()
        return count > 0

    except Exception as ex:
        send_log(
            job_config.get('job_name'),
            job_config.get('enviar_logs'),
            job_config.get('enviar_logs_debug'),
            f' Erro ao protocolar cpf/cnpj do cliente no banco semaforo: {str(ex)}',
            LogType.ERROR,
            'CLIENTE')


def job_send_points_to_okvendas(job_config: dict):
    with (lock):
        """
        Job para enviar pedido para okvendas
        Args:
            job_config: Configuração do job
        """
        # Exibe mensagem monstrando que a Thread foi Iniciada
        logger.info(f'==== THREAD INICIADA -job: ' + job_config.get('job_name'))

        # LOG de Inicialização do Método - Para acompanhamento de execução
        send_log(
            job_config.get('job_name'),
            job_config.get('enviar_logs'),
            job_config.get('enviar_logs_debug'),
            f'Envia pontos de fidelidade para Okvendas - Iniciado',
            LogType.EXEC,
            'PONTOS_PARA_OKVENDAS')

        db_config = utils.get_database_config(job_config)
        # Executa o Comando da Semaforo Antes do Query Principal
        if job_config['executar_query_semaforo'] == 'S':
            logger.info(f'Executando a query semáforo')
            executa_comando_sql(db_config, job_config)

        # Executa a query Principal
        logger.info(f'Executando a query principal')
        pontos_para_okvendas = query_points_to_okvendas(db_config, job_config)
        body = {'parceiros': []}
        try:
            for ponto in pontos_para_okvendas:
                if len(body['parceiros']) < 50:
                    body['parceiros'].append(ponto)

                else:
                    send_log(
                        job_config.get('job_name'),
                        False,
                        job_config.get('enviar_logs_debug'),
                        f"Enviando {body['parceiros'].__len__()} Pontos",
                        LogType.INFO,
                        'PONTOS_PARA_OKVENDAS')
                    if api_okvendas.post_send_points_to_okvendas(body, job_config):
                        if protocol_pontos_to_okvendas(job_config, db_config, body):
                            send_log(
                                job_config.get('job_name'),
                                job_config.get('enviar_logs'),
                                job_config.get('enviar_logs_debug'),
                                f'Pontos protocolados no banco semaforo',
                                LogType.INFO,
                                'PONTOS_PARA_OKVENDAS')

                    body = {'parceiros': []}

            if len(body['parceiros']) > 0:
                send_log(
                    job_config.get('job_name'),
                    False,
                    job_config.get('enviar_logs_debug'),
                    f"Enviando {body['parceiros'].__len__()} Pontos",
                    LogType.INFO,
                    'PONTOS_PARA_OKVENDAS')
                if api_okvendas.post_send_points_to_okvendas(body, job_config):
                    if protocol_pontos_to_okvendas(job_config, db_config, body):
                        send_log(
                            job_config.get('job_name'),
                            job_config.get('enviar_logs'),
                            job_config.get('enviar_logs_debug'),
                            f'Pontos protocolados no banco semaforo',
                            LogType.INFO,
                            'PONTOS_PARA_OKVENDAS')

        except Exception as ex:
            send_log(
                job_config.get('job_name'),
                job_config.get('enviar_logs'),
                job_config.get('enviar_logs_debug'),
                f'Erro {str(ex)}',
                LogType.ERROR,
                'PONTOS_PARA_OKVENDAS')


def query_points_to_okvendas(db_config, job_config):
    try:
        db = database.Connection(db_config)
        conn = db.get_conect()
        cursor = conn.cursor()
        newsql = utils.final_query(db_config)
        if src.print_payloads:
            print(newsql)
        cursor.execute(newsql)
        rows = cursor.fetchall()
        columns = [col[0].lower() for col in cursor.description]
        results = list(dict(zip(columns, row)) for row in rows)
        cursor.close()
        conn.close()
        pontos_to_okvendas = []
        if len(results) > 0:
            pontos_to_okvendas = (points_to_okvendas_dict(results))
        return pontos_to_okvendas
    except Exception as ex:
        send_log(
            job_config.get('job_name'),
            job_config.get('enviar_logs'),
            job_config.get('enviar_logs_debug'),
            f' Erro ao consultar pontos para okvendas: {str(ex)}',
            LogType.ERROR,
            'PONTOS_PARA_OKVENDAS')
        raise ex


def points_to_okvendas_dict(pontos_para_okvendas):
    retorno = []
    for i in pontos_para_okvendas:
        retorno.append({
            'codigo_parceiro': str(i['codparc']),
            'codigo_empresa': str(i['codemp']),
            'valor_cashback': i['valor'],
            'tipo_aplicacao': i['type']
        })
    return retorno


def protocol_pontos_to_okvendas(job_config, db_config, pontos):
    try:
        conexao = database.Connection(db_config)
        conn = conexao.get_conect()
        cursor = conn.cursor()
        for x in pontos['parceiros']:
            cursor.execute(queries.get_insert_update_semaphore_command(db_config.db_type),
                           queries.get_command_parameter(db_config.db_type,
                                                         [x['codigo_parceiro'],
                                                          f"{x['codigo_empresa']}-{x['tipo_aplicacao']}",
                                                          IntegrationType.PONTO_FIDELIDADE.value,
                                                          'SUCESSO']))
        count = cursor.rowcount
        cursor.close()
        conn.commit()
        conn.close()
        return count > 0
    except Exception as e:
        send_log(
            job_config.get('job_name'),
            job_config.get('enviar_logs'),
            job_config.get('enviar_logs_debug'),
            f'Erro ao protocolar Ponto Erro: {str(e)}',
            LogType.ERROR,
            'PONTOS_PARA_OKVENDAS')


def job_send_transportadora_to_okvendas(job_config: dict):
        """
        Job para enviar a transportadora
        Args:
            job_config: Configuração do job
        """
        with lock:
            db_config = utils.get_database_config(job_config)
            # Exibe mensagem monstrando que a Thread foi Iniciada
            logger.info(f'==== THREAD INICIADA -job: ' + job_config.get('job_name'))
            # LOG de Inicialização do Método - Para acompanhamento de execução
            send_log(
                job_config.get('job_name'),
                job_config.get('enviar_logs'),
                job_config.get('enviar_logs_debug'),
                f'Transportadora - Iniciado',
                LogType.EXEC,
                'TRANSPORTADORA_PARA_OKVENDAS')
            # Executa o Comando da Semaforo Antes do Query Principal
            if job_config['executar_query_semaforo'] == 'S':
                logger.info(f'Executando a query semáforo')
                executa_comando_sql(db_config, job_config)

            # Executa a query Principal
            logger.info(f'Executando a query principal')
            transportadoras = query_transportadora_to_okvendas(job_config, db_config)

            if transportadoras is not None and len(transportadoras) or 0 > 0:
                send_log(
                    job_config.get('job_name'),
                    job_config.get('enviar_logs'),
                    job_config.get('enviar_logs_debug'),
                    f'Transportadoras serem inseridas: {len(transportadoras)}',
                    LogType.INFO,
                    'TRANSPORTADORA_PARA_OKVENDAS')
                api_transportadora = []
                for transportadora in transportadoras:
                    try:
                        # time.sleep(1)
                        if api_transportadora.__len__() < 50:
                            api_transportadora.append(transportadora)
                        else:
                            send_log(
                                job_config.get('job_name'),
                                False,
                                job_config.get('enviar_logs_debug'),
                                f'Enviando Pacote: {api_transportadora.__len__()}',
                                LogType.INFO,
                                'TRANSPORTADORA_PARA_OKVENDAS')
                            response = api_okvendas. post_send_transportadora_parceiro(api_transportadora,
                                                                                       job_config)
                            api_transportadora = []
                            send_log(
                                job_config.get('job_name'),
                                False,
                                job_config.get('enviar_logs_debug'),
                                f'Tratando retorno',
                                LogType.INFO,
                                'TRANSPORTADORA_PARA_OKVENDAS')
                            validade_response_transportadora(response, db_config, job_config)

                    except Exception as e:
                        send_log(
                            job_config.get('job_name'),
                            job_config.get('enviar_logs'),
                            True,
                            f'Erro genérico ao enviar transportadora, Erro: {str(e)}',
                            LogType.ERROR,
                            'TRANSPORTADORA_PARA_OKVENDAS')

                # Se ficou algum sem processa
                if api_transportadora.__len__() > 0:
                    send_log(
                        job_config.get('job_name'),
                        False,
                        job_config.get('enviar_logs_debug'),
                        f'Enviando Pacote: {api_transportadora.__len__()}',
                        LogType.INFO,
                        'TRANSPORTADORA_PARA_OKVENDAS')
                    response = api_okvendas.post_send_transportadora_parceiro(api_transportadora, job_config)
                    send_log(
                        job_config.get('job_name'),
                        False,
                        job_config.get('enviar_logs_debug'),
                        f'Tratando retorno',
                        LogType.INFO,
                        'TRANSPORTADORA_PARA_OKVENDAS')
                    validade_response_transportadora(response, db_config, job_config)
            else:
                send_log(
                    job_config.get('job_name'),
                    job_config.get('enviar_logs'),
                    job_config.get('enviar_logs_debug'),
                    f'Nao ha unidades de distribuicao para inserir no momento',
                    LogType.WARNING,
                    'TRANSPORTADORA_PARA_OKVENDAS')


def query_transportadora_to_okvendas(job_config, db_config):
    try:
        db = database.Connection(db_config)
        conn = db.get_conect()
        cursor = conn.cursor()
        newsql = utils.final_query(db_config)
        if src.print_payloads:
            print(newsql)
        cursor.execute(newsql)
        rows = cursor.fetchall()
        columns = [col[0].lower() for col in cursor.description]
        results = list(dict(zip(columns, row)) for row in rows)
        cursor.close()
        conn.close()
        transportadora_to_okvendas = []
        if len(results) > 0:
            transportadora_to_okvendas = (transportadora_to_okvendas_dict(results))
        return transportadora_to_okvendas
    except Exception as ex:
        send_log(
            job_config.get('job_name'),
            job_config.get('enviar_logs'),
            job_config.get('enviar_logs_debug'),
            f' Erro ao consultar transportadora para okvendas: {str(ex)}',
            LogType.ERROR,
            'TRANSPORTADORA_PARA_OKVENDAS')
        raise ex


def transportadora_to_okvendas_dict(transportadora_para_okvendas):
    retorno = []
    for i in transportadora_para_okvendas:
        retorno.append({
            'codigo_externo': str(i['codigo_externo']),
            'nome': str(i['nome']),
            'razao_social': str(i['razao_social']),
            'cnpj': str(i['cnpj']),
            'data_aprovacao': i['data_aprovacao'],
            'data_desativacao': i['data_desativacao']
        })
    return retorno


def protocol_transportadora_to_okvendas(job_config, db_config, transportadora):
    try:
        conexao = database.Connection(db_config)
        conn = conexao.get_conect()
        cursor = conn.cursor()
        for x in transportadora['parceiros']:
            cursor.execute(queries.get_insert_update_semaphore_command(db_config.db_type),
                           queries.get_command_parameter(db_config.db_type,
                                                         [x['codigo_parceiro'],
                                                          f"{x['codigo_empresa']}-{x['tipo_aplicacao']}",
                                                          IntegrationType.TRANSPORTADORA.value,
                                                          'SUCESSO']))
        count = cursor.rowcount
        cursor.close()
        conn.commit()
        conn.close()
        return count > 0
    except Exception as e:
        send_log(
            job_config.get('job_name'),
            job_config.get('enviar_logs'),
            job_config.get('enviar_logs_debug'),
            f'Erro ao protocolar Transportadora Erro: {str(e)}',
            LogType.ERROR,
            'TRANSPORTADORA_PARA_OKVENDAS')


def validade_response_transportadora(response, db_config, job_config):
    logger.info("Validando o Response de Transportadora Parceiro")
    if response is not None:
        # Percorre todos os registros

        db = database.Connection(db_config)
        conn = db.get_conect()
        cursor = conn.cursor()
        try:
            for item in response:
                if item.sucesso == True:
                    msgret = 'SUCESSO'
                else:
                    msgret = item.message[:150]
                if item.identificador is not None:
                    if src.print_payloads:
                        print(f"Identificador = {item.identificador}")
                    cursor.execute(queries.get_semaphore_command_data_sincronizacao(db_config.db_type),
                                   queries.get_command_parameter(db_config.db_type,
                                                                 [item.identificador, "",
                                                                  IntegrationType.TRANSPORTADORA.value,
                                                                  msgret]))
            count = cursor.rowcount
            cursor.close()
            conn.commit()
            conn.close()
            return count > 0
        except Exception as e:
            send_log(
                job_config.get('job_name'),
                job_config.get('enviar_logs'),
                job_config.get('enviar_logs_debug'),
                f'Erro ao enviar transportadora,'
                f'Erro: {str(e)}',
                LogType.ERROR,
                'TRANSPORTADORA_PARA_OKVENDAS')

        cursor.close()
        conn.commit()
        conn.close()
