import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class EpaAutomation:
    def __init__(self, usuario, senha, db_config):
        self.usuario = usuario
        self.senha = senha
        self.db_config = db_config
        self.navegador = None

    def iniciar_navegador(self):
        """Iniciar o navegador Chrome."""
        servico = Service(ChromeDriverManager().install())
        self.navegador = webdriver.Chrome(service=servico)
        print("Navegador iniciado.")

    def acessar_pagina(self, url):
        """Acessar página de login."""
        self.navegador.get(url)
        print(f"Acessando página: {url}")

    def fazer_login(self):
        """Realizar o login no sistema EPA."""
        print("Realizando login...")
        self.navegador.find_element(By.XPATH, '//*[@id="cbousuario"]').send_keys(self.usuario)
        self.navegador.find_element(By.XPATH, '//*[@id="txtsenha"]').send_keys(self.senha)
        self.navegador.find_element(By.XPATH, '//*[@id="form"]/div[5]/div[1]/button/strong').click()
        time.sleep(5)
        print("Login realizado com sucesso!")

    def navegar_para_ordem_servico(self):
        """Navegar até a tela de ordens de serviço."""
        print("Navegando para Ordens de Serviço...")
        try:
            self.navegador.find_element(By.XPATH, '//*[@id="mostrar-OS-ordem-servico"]').click()
            time.sleep(3)
            
            opcao_todos = WebDriverWait(self.navegador, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="conteudo_tabela_Ordem_servico_length"]/label/select/option[text()="Todos"]'))
            )
            opcao_todos.click()
            time.sleep(1)
        except Exception as e:
            print(f"Erro ao navegar para Ordens de Serviço: {e}")
            raise

    def verificar_e_acessar_acompanhamento(self, solicitacao):
        """Verificando o código e acessando acompanhamento para averiguar correspondência."""
        print(f"Verificando código: {solicitacao} e acessando acompanhamento...")
        wait = WebDriverWait(self.navegador, 10)

        try:
            linhas = wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, '//*[@id="conteudo_tabela_Ordem_servico"]/tbody/tr')
            ))

            for linha in linhas:
                try:
                    # Captura o código na coluna 2 
                    codigo_elemento = linha.find_element(By.XPATH, './/td[2]').text.strip()
                    print(f"Verificando código na linha: {codigo_elemento}")

                    if codigo_elemento == solicitacao:
                        print(f"Código correspondente encontrado: {codigo_elemento}")

                        # Clicando no botão Ação
                        linha.find_element(By.XPATH, './/td[1]/span/li/a').click()
                        time.sleep(20)

                        # Clicando em Acompanhamento
                        acompanhamento = linha.find_element(By.XPATH, './/td[1]/span/li/ul/li[3]/a')
                        acompanhamento.click()
                        print("Acompanhamento acessado com sucesso!")
                        time.sleep(3)
                        return  # Sai após encontrar o código
                except Exception as e:
                    print(f"Erro ao verificar linha: {e}")
        except Exception as e:
            print(f"Erro durante a verificação e acesso de acompanhamento: {e}")
            raise

    def preencher_acompanhamento(self):
        """Preenche o acompanhamento no iframe."""
        print("Preenchendo acompanhamento no iframe...")
        wait = WebDriverWait(self.navegador, 30)
        try:
            wait.until(EC.presence_of_element_located((By.ID, "cboxLoadedContent")))
            iframe = self.navegador.find_element(By.CSS_SELECTOR, "iframe.cboxIframe")  # Verifique o seletor
            self.navegador.switch_to.frame(iframe)
            print("Foco no iframe.")
            time.sleep(2)

            # Preenche o campo de texto
            campo_texto = wait.until(EC.element_to_be_clickable((By.ID, "txtobs")))
            campo_texto.clear()
            campo_texto.send_keys('Processo encaminhado para Ekyte')
            time.sleep(2)
            
            # Clica no botão de E-mail
            ClikEmail = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="accordion1"]/div[2]/div[1]/div')))
            ClikEmail.click()

            # Verifica a presença dos elementos "todosEnvolvidos" e "todosAnexos"
            try:
                todos_envolvidos = wait.until(EC.element_to_be_clickable((By.ID, "todosEnvolvidos")))
                todos_envolvidos.click()
                print("Marcado 'todosEnvolvidos'.")
            except Exception as e:
                print("Elemento 'todosEnvolvidos' não encontrado:", e)
            time.sleep(3)

            try:
                todos_anexos = wait.until(EC.element_to_be_clickable((By.ID, "todosAnexo")))
                todos_anexos.click()
                print("Marcado 'todosAnexos'.")
            except Exception as e:
                print("Elemento 'todosAnexos' não encontrado. Continuando...")
                
            time.sleep(3)
            
            # Continua com o bloco de Encaminhamento
            try:
                ClikEncaminhamento = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="accordion1"]/div[3]/div[1]/div')))
                ClikEncaminhamento.click()
                print("Encaminhamento acessado com sucesso.")
                
                CampoSelect = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="encaminhamento"]/div/div[2]/div[1]/div/div/div/button')))
                CampoSelect.click()
                time.sleep(3)
                wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[7]/div/ul/li[3]/a'))).click()
                time.sleep(3)
                
                CampoSelectPara = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="encaminhamento"]/div/div[2]/div[2]/div/div/div/button')))
                CampoSelectPara.click()
                time.sleep(3)
                wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[8]/div/ul/li[75]/a'))).click()
                
                print("Encaminhamento configurado com sucesso.")
            except Exception as e:
                print(f"Erro no bloco de Encaminhamento: {e}")

            # Fecha o modal
            #wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="forward-form"]/div/div[2]/div/div/button[1]'))).click()
            print("Acompanhamento preenchido com sucesso.")
            time.sleep(10)
            
        except Exception as e:
            print(f"Erro ao preencher acompanhamento: {e}")
            raise


    def fechar_navegador(self):
        """Fecha o navegador."""
        print("Fechando navegador...")
        if self.navegador:
            self.navegador.quit()
            print("Navegador fechado.")
        else:
            print("Navegador já estava fechado.")
