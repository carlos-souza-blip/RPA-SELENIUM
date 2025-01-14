import os
import mysql.connector
import logging
from config import DB_CONFIG, ARQUIVOS_LOG, EPA_CONFIG
from acompanhamento import EpaAutomation
from anexos import processar_anexos  # Importando o processamento de anexos

# Configurações básicas de logging
logging.basicConfig(
    filename=ARQUIVOS_LOG['AUTOMATO_LOG'],
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class Automata:
    def __init__(self):
        self.db_config = DB_CONFIG
        self.processados_file = ARQUIVOS_LOG['PROCESSADOS_FILE']
        self.processados_links_file = ARQUIVOS_LOG['PROCESSADOS_LINKS_FILE']

    # Funções auxiliares
    def carregar_processados(self):
        """Carrega a lista de códigos já processados do arquivo."""
        if not os.path.exists(self.processados_file):
            with open(self.processados_file, 'w') as f:
                pass  # Cria o arquivo vazio
        with open(self.processados_file, 'r') as f:
            return set(f.read().splitlines())

    def salvar_processado(self, codigo):
        """Salva um código no arquivo de processados."""
        with open(self.processados_file, 'a') as f:
            f.write(f"{codigo}\n")
        logging.info(f"Código {codigo} salvo como processado.")

    def buscar_solicitacoes(self):
        """Busca solicitações do banco de dados que precisam de acompanhamento."""
        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT codigo, cliente, titulo, descricao, ultimo_encaminhamento, data_inicio, data_fim, solicitante,
        unidade_responsavel, tipo_servico
        FROM epa_dados
        WHERE ultimo_encaminhamento = 'Analisar'
        """
        cursor.execute(query)
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()
        return resultados

    def inserir_na_tabela_conteudo(self, dados):
        """Insere dados na tabela conteudo."""
        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor()
        query = """
        INSERT INTO conteudo (
            solicitacao, assunto, descricao, status, data_inicio, verificado, data_fim, cliente,
            unidade_solicitante, tipo_servico, solicitante
            
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(query, (
                dados['codigo'], # Solicitação
                dados['titulo'], # Titulo
                dados['descricao'], # Descrição
                'Executar', # Serviço analisado e em andamento
                dados['data_inicio'], # data de quando foi aberto o chamado
                0,  # controle para envio de emails.
                dados['data_fim'], # data de quando vai terminar a solicitacao
                dados['solicitante'], # cliente
                dados['unidade_responsavel'], # departamento que abriu a solicitacao
                dados['tipo_servico'], # Tipo de servico
                dados['cliente'], # nome do cliente completo
            ))
            conn.commit()
            logging.info(f"Dados inseridos na tabela conteudo para a solicitação {dados['codigo']}.")
        except Exception as e:
            logging.error(f"Erro ao inserir dados na tabela conteudo: {e}")
        finally:
            cursor.close()
            conn.close()
            
    def inserir_anexo_no_banco(num_solicitacao, link_anexo):
        """
        Insere o link do anexo no banco de dados na tabela `anexos`, evitando duplicatas.
        """
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        query = """
        INSERT INTO anexos (num_solicitacao, link_anexo)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE link_anexo=VALUES(link_anexo)
        """

        try:
            cursor.execute(query, (num_solicitacao, link_anexo))
            conn.commit()
            if cursor.rowcount > 0:
                logging.info(f"Anexo inserido ou atualizado no banco para a solicitação {num_solicitacao}: {link_anexo}")
                print(f"Anexo inserido ou atualizado no banco para a solicitação {num_solicitacao}: {link_anexo}")
            else:
                logging.info(f"Anexo já existente no banco para a solicitação {num_solicitacao}: {link_anexo}")
                print(f"Anexo já existente no banco para a solicitação {num_solicitacao}: {link_anexo}")
        except Exception as e:
            logging.error(f"Erro ao inserir anexo no banco para a solicitação {num_solicitacao}: {e}")
            print(f"Erro ao inserir anexo no banco para a solicitação {num_solicitacao}: {e}")
        finally:
            cursor.close()
            conn.close()


    def processar_solicitacoes(self):
        """Processa as solicitações encontradas no banco."""
        processados = self.carregar_processados()
        solicitacoes = self.buscar_solicitacoes()

        for solicitacao in solicitacoes:
            codigo = solicitacao['codigo']
            if codigo not in processados:
                automacao = EpaAutomation(EPA_CONFIG['USUARIO'], EPA_CONFIG['SENHA'], self.db_config)
                try:
                    automacao.iniciar_navegador()
                    automacao.acessar_pagina(EPA_CONFIG['LINK_LOGIN'])
                    automacao.fazer_login()
                    automacao.navegar_para_ordem_servico()

                    # Verifica e processa o acompanhamento no EPA
                    automacao.verificar_e_acessar_acompanhamento(codigo)
                    automacao.preencher_acompanhamento()

                    # Insere os dados na tabela conteudo
                    self.inserir_na_tabela_conteudo(solicitacao)
                    self.salvar_processado(codigo)

                except Exception as e:
                    logging.error(f"Erro no processamento da solicitação {codigo}: {e}")
                finally:
                    automacao.fechar_navegador()

        # Após processar solicitações, processar os anexos
        try:
            logging.info("Iniciando processamento de anexos...")
            processar_anexos(EPA_CONFIG['USUARIO'], EPA_CONFIG['SENHA'], self.db_config)  # Chama o processamento de anexos
            logging.info("Processamento de anexos concluído.")
        except Exception as e:
            logging.error(f"Erro no processamento de anexos: {e}")

if __name__ == "__main__":
    automata = Automata()
    automata.processar_solicitacoes()
