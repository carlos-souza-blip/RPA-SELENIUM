import mysql.connector
from config import EPA_CONFIG, ARQUIVOS_LOG
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
# Arquivo de links processados

# Função para carregar links processados
def carregar_processados_anexos():
    if not os.path.exists(ARQUIVOS_LOG['PROCESSADOS_ANEXOS_FILE']):
        with open(ARQUIVOS_LOG['PROCESSADOS_ANEXOS_FILE'], 'w') as f:
            pass
    with open(ARQUIVOS_LOG['PROCESSADOS_ANEXOS_FILE'], 'r') as f:
        return set(f.read().splitlines())

# Função para salvar link como processado
def salvar_anexo_processado(codigo, link):
    with open(ARQUIVOS_LOG['PROCESSADOS_ANEXOS_FILE'], 'a') as f:
        f.write(f"{codigo} - {link}\n")

class AnexosAutomation:
    def __init__(self, usuario, senha, db_config):
        self.usuario = usuario
        self.senha = senha
        self.db_config = db_config
        self.navegador = None

    def iniciar_navegador(self):
        servico = Service(ChromeDriverManager().install())
        self.navegador = webdriver.Chrome(service=servico)
        print("Navegador iniciado.")

    def acessar_pagina(self, url):
        self.navegador.get(url)
        print(f"Acessando página: {url}")

    def fazer_login(self):
        print("Realizando login...")
        WebDriverWait(self.navegador, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="cbousuario"]'))
        ).send_keys(self.usuario)
        self.navegador.find_element(By.XPATH, '//*[@id="txtsenha"]').send_keys(self.senha)
        self.navegador.find_element(By.XPATH, '//*[@id="form"]/div[5]/div[1]/button/strong').click()
        time.sleep(5)
        print("Login realizado com sucesso!")

    def buscar_solicitacoes_analisar(self):
        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT codigo
        FROM epa_dados
        WHERE ultimo_encaminhamento = 'Analisar'
        """
        cursor.execute(query)
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()
        return [r['codigo'] for r in resultados]

    def acessar_solicitacao_por_codigo(self, codigo):
        url = f"{EPA_CONFIG['LINK_ANEXO']}{codigo}"
        self.navegador.get(url)
        time.sleep(5)

    def acessar_aba_anexos(self):
        try:
            # Aguarda que o overlay desapareça
            WebDriverWait(self.navegador, 10).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "loading"))
            )
            print("Overlay de carregamento desapareceu.")

            # Tenta clicar na aba de anexos
            aba_anexo = WebDriverWait(self.navegador, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="myTab"]/li[4]/a'))
            )
            aba_anexo.click()
            time.sleep(5)
            print("Aba de anexos acessada com sucesso.")
        except Exception as e:
            print(f"Erro ao acessar aba de anexos: {e}")
            raise

    def verificar_anexos(self):
        try:
            anexos = WebDriverWait(self.navegador, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, '//a[contains(@class, "btn-mini") and contains(@data-original-title, "Download Arquivo")]'))
            )
            return [anexo.get_attribute('href') for anexo in anexos]
        except Exception as e:
            print(f"Erro ao verificar anexos: {e}")
            return []

    def salvar_anexos_no_banco(self, codigo, links):
        """Salvar os links no banco de dados."""
        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor()
        query = """
        INSERT INTO anexos (num_solicitacao, link_anexo)
        VALUES (%s, %s)
        """
        try:
            for link in links:
                cursor.execute(query, (codigo, link))
            conn.commit()
            print(f"Anexos salvos no banco para a solicitação {codigo}.")
        except Exception as e:
            print(f"Erro ao salvar anexos no banco para {codigo}: {e}")
        finally:
            cursor.close()
            conn.close()

    def fechar_navegador(self):
        if self.navegador:
            self.navegador.quit()
            print("Navegador fechado.")
        else:
            print("Navegador já estava fechado.")

def processar_anexos(usuario, senha, db_config):
    anexos_automation = AnexosAutomation(usuario, senha, db_config)
    processados_anexos = carregar_processados_anexos()

    try:
        anexos_automation.iniciar_navegador()
        anexos_automation.acessar_pagina(EPA_CONFIG['LINK_LOGIN'])
        anexos_automation.fazer_login()

        solicitacoes_analisar = anexos_automation.buscar_solicitacoes_analisar()
        for codigo in solicitacoes_analisar:
            print(f"Processando anexos da solicitação {codigo}...")

            if any(f"{codigo} - " in link for link in processados_anexos):
                print(f"Anexos já processados para a solicitação {codigo}. Pulando.")
                continue

            anexos_automation.acessar_solicitacao_por_codigo(codigo)
            anexos_automation.acessar_aba_anexos()
            anexos = anexos_automation.verificar_anexos()

            if anexos:
                print(f"Anexos encontrados para {codigo}: {anexos}")
                anexos_automation.salvar_anexos_no_banco(codigo, anexos)
                for link in anexos:
                    salvar_anexo_processado(codigo, link)
            else:
                print(f"Sem anexos para a solicitação {codigo}.")

    except Exception as e:
        print(f"Erro no processamento de anexos: {e}")
    finally:
        anexos_automation.fechar_navegador()
