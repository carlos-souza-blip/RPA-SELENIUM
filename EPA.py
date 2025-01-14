import time
import logging
import mysql.connector
from config import DB_CONFIG, EPA_CONFIG, ARQUIVOS_LOG
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
from selenium.common.exceptions import TimeoutException

# Configurações de log
logging.basicConfig(
    filename=ARQUIVOS_LOG['EPA_LOG'],
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Epa:
    def __init__(self, usuario, senha):
        self.usuario = usuario
        self.senha = senha
        self.navegador = None

    def iniciar_navegador(self):
        """Iniciar o navegador Chrome."""
        servico = Service(ChromeDriverManager().install())
        self.navegador = webdriver.Chrome(service=servico)
        logging.info("Navegador iniciado.")

    def acessar_pagina(self, url):
        """Acessar página de login."""
        self.navegador.get(url)
        logging.info(f"Acessando página: {url}")

    def fazer_login(self):
        """Realizar o login no sistema EPA."""
        try:
            WebDriverWait(self.navegador, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="cbousuario"]'))
            ).send_keys(self.usuario)
            self.navegador.find_element(By.XPATH, '//*[@id="txtsenha"]').send_keys(self.senha)
            self.navegador.find_element(By.XPATH, '//*[@id="form"]/div[5]/div[1]/button/strong').click()
            time.sleep(3)
            logging.info("Login realizado com sucesso!")
        except Exception as e:
            logging.error(f"Erro ao realizar login: {e}")
            
    def redirecionar_pagina_principal(self):
        self.navegador.get(EPA_CONFIG['LINK_PRINCIPAL'])
        time.sleep(5)
        
        
    def navegar_para_ordem_servico(self):
        """Navegar até a tela de ordens de serviço."""
        try:
            elemento = WebDriverWait(self.navegador, 20).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="mostrar-OS-ordem-servico"]'))
            )
            elemento.click()
            logging.info("Navegação para Ordens de Serviço concluída.")
            time.sleep(5)
        except TimeoutException:
            logging.error("Erro: O elemento 'mostrar-OS-ordem-servico' não foi encontrado dentro do tempo limite.")
        except Exception as e:
            logging.error(f"Erro ao navegar para Ordens de Serviço: {e}")

    def select_info_epa(self):
        """Selecionar todas as informações necessárias na tabela."""
        try:
            configuracoes_tabela = WebDriverWait(self.navegador, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="conteudo_tabela_Ordem_servico_wrapper"]/div[2]/div/button[1]'))
            )
            configuracoes_tabela.click()
            time.sleep(5)

            colunas_xpath = [
                '//*[@id="conteudo_tabela_Ordem_servico_wrapper"]/div[2]/div/div[2]/button[10]',
                '//*[@id="conteudo_tabela_Ordem_servico_wrapper"]/div[2]/div/div[2]/button[11]',
                '//*[@id="conteudo_tabela_Ordem_servico_wrapper"]/div[2]/div/div[2]/button[12]',
                '//*[@id="conteudo_tabela_Ordem_servico_wrapper"]/div[2]/div/div[2]/button[13]'
            ]

            for xpath in colunas_xpath:
                coluna = WebDriverWait(self.navegador, 10).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                coluna.click()
                time.sleep(3)

            dropdown = WebDriverWait(self.navegador, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="conteudo_tabela_Ordem_servico_length"]/label/select'))
            )
            self.navegador.execute_script("arguments[0].click();", dropdown)
            time.sleep(3)

            opcao_todos = WebDriverWait(self.navegador, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="conteudo_tabela_Ordem_servico_length"]/label/select/option[text()="Todos"]'))
            )
            opcao_todos.click()
            time.sleep(5)

            logging.info("Configurações da tabela ajustadas com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao ajustar configurações da tabela: {e}")

    def ler_tabela(self):
        """Ler as informações da tabela."""
        print("Lendo dados da tabela...")
        linhas = self.navegador.find_elements(By.XPATH, '//*[@id="conteudo_tabela_Ordem_servico"]/tbody/tr')

        dados_tabela = []

        for linha in linhas:
            try:
                titulo_descricao = linha.find_element(By.XPATH, './td[3]').text.strip()
                # Divide o campo pelo separador de linha
                partes = titulo_descricao.split("\n", 1)  # Divide na primeira ocorrência de nova linha
                if len(partes) == 2:
                    # Processa o título e a descrição
                    titulo_completo = partes[0].strip()
                    descricao = partes[1].strip()
                else:
                    titulo_completo = titulo_descricao.strip()
                    descricao = ""

                # Divide o título completo em cliente e título, se houver " - "
                titulo_partes = titulo_completo.split(" - ", 1)
                if len(titulo_partes) == 2:
                    cliente = titulo_partes[0].strip()  # Parte antes de " - " é o cliente
                    titulo = titulo_partes[1].strip()   # Parte depois de " - " é o título
                else:
                    cliente = ""
                    titulo = titulo_completo

                dados = {
                    'codigo': linha.find_element(By.XPATH, './td[2]').text.strip(),
                    'cliente': cliente,  # Nome do cliente extraído
                    'titulo': titulo,  # Título extraído
                    'descricao': descricao,  # Descrição extraída
                    'data_ultimo_encaminhamento': linha.find_element(By.XPATH, './td[4]').text.strip(),
                    'ultimo_encaminhamento': linha.find_element(By.XPATH, './td[5]').text.strip(),
                    'data_inicio': linha.find_element(By.XPATH, './td[6]').text.strip(),
                    'data_fim': linha.find_element(By.XPATH, './td[7]').text.strip(),
                    'tipo_servico': linha.find_element(By.XPATH, './td[9]').text.strip(),
                    'responsavel': linha.find_element(By.XPATH, './td[10]').text.strip(),
                    'solicitante': linha.find_element(By.XPATH, './td[11]').text.strip(),
                    'unidade_responsavel': linha.find_element(By.XPATH, './td[12]').text.strip(),
                    'unidade_solicitante': linha.find_element(By.XPATH, './td[13]').text.strip(),
                    'tempo_restante_fase': linha.find_element(By.XPATH, './td[14]').text.strip(),
                    'dias_restantes': linha.find_element(By.XPATH, './td[15]').text.strip()
                }
                dados_tabela.append(dados)

            except Exception as e:
                print(f"Erro ao processar linha: {e}")

        print(f"Total de linhas lidas: {len(dados_tabela)}")
        return dados_tabela

    def fechar_navegador(self):
        """Fechar o navegador."""
        self.navegador.quit()
        print("Navegador fechado.")

def verificar_novas_solicitacoes(dados):
    """Verificar se existem novas solicitações no banco de dados."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    query = "SELECT codigo FROM epa_dados"
    cursor.execute(query)
    codigos_existentes = {row['codigo'] for row in cursor.fetchall()}
    cursor.close()
    conn.close()

    novas_solicitacoes = [dado for dado in dados if dado['codigo'] not in codigos_existentes]
    return novas_solicitacoes

def inserir_dados(dados):
    """Insere os dados no banco."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    query = """
    INSERT INTO epa_dados (
        codigo, cliente, titulo, descricao, data_ultimo_encaminhamento, ultimo_encaminhamento,
        data_inicio, data_fim, tipo_servico, responsavel, solicitante,
        unidade_responsavel, unidade_solicitante, tempo_restante_fase, dias_restantes
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    try:
        for dado in dados:
            
            data_ultimo_encaminhamento = datetime.strptime(dado['data_ultimo_encaminhamento'], "%d/%m/%Y %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
            data_inicio = datetime.strptime(dado['data_inicio'], "%d/%m/%Y %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
            data_fim = datetime.strptime(dado['data_fim'], "%d/%m/%Y %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute(query, (
                dado['codigo'],
                dado['cliente'],
                dado['titulo'],
                dado['descricao'],
                data_ultimo_encaminhamento,
                dado['ultimo_encaminhamento'],
                data_inicio,
                data_fim,
                dado['tipo_servico'],
                dado['responsavel'],
                dado['solicitante'],
                dado['unidade_responsavel'],
                dado['unidade_solicitante'],
                dado['tempo_restante_fase'],
                int(dado['dias_restantes'])
            ))
        conn.commit()
        print("Dados inseridos com sucesso!")
    except Exception as e:
        print(f"Erro ao inserir dados no banco: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":

    while True:
        epa = Epa(EPA_CONFIG['USUARIO'], EPA_CONFIG['SENHA'])
        epa.iniciar_navegador()
        epa.acessar_pagina(EPA_CONFIG['LINK_LOGIN'])
        epa.fazer_login()
        epa.redirecionar_pagina_principal()
        epa.navegar_para_ordem_servico()
        epa.select_info_epa()

        dados_tabela = epa.ler_tabela()
        if dados_tabela:
            novas_solicitacoes = verificar_novas_solicitacoes(dados_tabela)
            if novas_solicitacoes:
                inserir_dados(novas_solicitacoes)
            else:
                print("Nenhuma nova solicitação encontrada.")
        else:
            print("Nenhum dado na tabela.")

        epa.fechar_navegador()
        print("Aguardando 1 hora para próxima execução...")
        time.sleep(3600)  # Aguardar 1 hora
