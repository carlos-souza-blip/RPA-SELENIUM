import time
import logging
from config import EPA_CONFIG, ARQUIVOS_LOG
from EPA import Epa, verificar_novas_solicitacoes, inserir_dados
from automata import Automata
from enviar_emails import processar_envio

# Configurações básicas de logging
logging.basicConfig(
    filename=ARQUIVOS_LOG['PRINCIPAL_LOG'],
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def executar_epa():
    """
    Executa o processo de busca de novas solicitações utilizando o EPA.
    """
    try:
        logging.info("Iniciando processo no EPA...")
        print("Iniciando processo no EPA...\n")
        
        epa = Epa(EPA_CONFIG['USUARIO'], EPA_CONFIG['SENHA'])
        epa.iniciar_navegador()
        epa.acessar_pagina(EPA_CONFIG['LINK_LOGIN'])
        epa.fazer_login()
        epa.navegar_para_ordem_servico()
        epa.select_info_epa()

        dados_tabela = epa.ler_tabela()
        if dados_tabela:
            novas_solicitacoes = verificar_novas_solicitacoes(dados_tabela)
            if novas_solicitacoes:
                inserir_dados(novas_solicitacoes)
                logging.info("Novas solicitações processadas e inseridas no banco.")
                print("Novas solicitações processadas e inseridas no banco.\n")
            else:
                logging.info("Nenhuma nova solicitação encontrada.")
                print("Nenhuma nova solicitação encontrada.\n")
        else:
            logging.info("Nenhum dado encontrado na tabela do EPA.")
            print("Nenhum dado encontrado na tabela do EPA.\n")
    except Exception as e:
        logging.error(f"Erro ao executar o EPA: {e}")
        print(f"Erro ao executar o EPA: {e}\n")
    finally:
        epa.fechar_navegador()

def executar_automata():
    """
    Executa o processo de acompanhamento e anexos utilizando o Automata.
    """
    try:
        logging.info("Iniciando processamento de acompanhamentos e anexos...")
        print("Iniciando processamento de acompanhamentos e anexos...\n")
        
        automata = Automata()
        automata.processar_solicitacoes()
        
        logging.info("Processamento de acompanhamentos e anexos concluído.")
        print("Processamento de acompanhamentos e anexos concluído.\n")
    except Exception as e:
        logging.error(f"Erro ao executar o Automata: {e}")
        print(f"Erro ao executar o Automata: {e}\n")
        
def enviar_email():
    """
    Envia e-mails para os solicitantes com as informações necessárias.
    """
    try:
        logging.info("Iniciando envio de e-mails...")
        print("Iniciando envio de e-mails...\n")
        
        # processar_envio()
        
        logging.info("Envio de e-mails concluído.")
        print("Envio de e-mails concluído.\n")
    except Exception as e:
        logging.error(f"Erro ao enviar e-mails: {e}")
        print(f"Erro ao enviar e-mails: {e}\n")

if __name__ == "__main__":
    while True:
        print("Iniciando processo principal...\n")
        logging.info("Iniciando processo principal...")

        # Executar EPA
        executar_epa()

        # Executar Automata
        executar_automata()
        
        # Enviar e-mails
        enviar_email()

        # Aguardar 1 hora antes da próxima execução
        print("Aguardando 1 hora para a próxima execução...\n")
        logging.info("Aguardando 1 hora para a próxima execução...")
        time.sleep(3600)
