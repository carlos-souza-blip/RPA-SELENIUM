import smtplib
from config import DB_CONFIG, EMAIL_CONFIG
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mysql.connector
from datetime import datetime

def conectar_banco():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco: {e}")
        return None

def verificar_solicitacao_completa(solicitacao):
    """Verifica se uma solicitação tem todas as informações necessárias."""
    conn = conectar_banco()
    if not conn:
        return False
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM conteudo WHERE solicitacao = %s", (solicitacao,))
        conteudo = cursor.fetchone()

        if not conteudo:
            return False

        cursor.execute("SELECT * FROM anexos WHERE num_solicitacao = %s", (solicitacao,))
        anexos = cursor.fetchall()

        return {'conteudo': conteudo, 'anexos': anexos}

    except Exception as e:
        print(f"Erro ao verificar solicitação completa: {e}")
        return False
    finally:
        conn.close()

def registrar_envio(solicitacao, id_workspace, unidade_solicitante, solicitante, enviado_por):
    """Registra no banco que o e-mail foi enviado, evitando duplicações."""
    conn = conectar_banco()
    if not conn:
        return

    try:
        cursor = conn.cursor()

        # Verificar se a solicitação já foi registrada
        cursor.execute(
            "SELECT COUNT(*) FROM emails_enviados WHERE solicitacao = %s",
            (solicitacao,)
        )
        existe = cursor.fetchone()[0]

        if existe:
            print(f"Solicitação {solicitacao} já registrada, evitando duplicação.")
        else:
            cursor.execute(
                """
                INSERT INTO emails_enviados (solicitacao, enviado_em, id_workspace, unidade_solicitante, solicitante, enviado_por)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (solicitacao, datetime.now(), id_workspace, unidade_solicitante, solicitante, enviado_por)
            )
            conn.commit()
            print(f"Solicitação {solicitacao} registrada com sucesso.")

    except Exception as e:
        print(f"Erro ao registrar envio: {e}")
    finally:
        conn.close()

def escolher_workspace_id(x):
    match x:
        case 'Unimed Anápolis':
            unimed = ("87361")
        case 'Unimed Araguaína':
            unimed = ("87367")
        case 'Unimed Caldas Novas':
            unimed = ("87366")
        case 'Unimed Catalão':
            unimed = ("87359")
        case 'Unimed Gurupi':
            unimed = ("87368")
        case 'Unimed Jataí':
            unimed = ("82468")
        case 'Unimed Mineiros':
            unimed = ("87365")
        case 'Unimed Morrinhos':
            unimed = ("87364")
        case 'Unimed Palmas':
            unimed = ("87362")
        case 'Unimed Rio Verde':
            unimed = ("86186")
        case 'Unimed Vale do Corumbá':
            unimed = ("87369")
        case _:
            unimed = ("87360")
    return unimed

def enviar_email(conteudo, anexos):
    """Envia o e-mail com as informações da solicitação."""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['email']
        msg['To'] = EMAIL_CONFIG['email_destinatario']
        msg['Subject'] = f"{conteudo['solicitacao']} - {conteudo['assunto']}"

        body = f"""
        <!-- <h3>Detalhes da Solicitação</h3> -->
        <p><strong>descrição:</strong> {conteudo.get('descricao', 'N/A')}</p>
        <!-- <p><strong>data inicio:</strong> {conteudo.get('data_inicio', 'N/A')}</p> -->
        <p><strong>[entrega:</strong> {conteudo.get('data_fim', 'N/A')}]</p>
        <p><strong>[solicitante:</strong> {conteudo.get('solicitante', 'N/A')}]</p>
        <p><strong>[tags:</strong> {conteudo.get('cliente', 'N/A')}, {conteudo.get('tipo_servico', 'N/A')}]</p>
        <p><strong>[workspace:</strong> {escolher_workspace_id(conteudo.get('unidade_solicitante', 'N/A'))}]</p>
        """

        if anexos:
            body += "<h3>Anexos</h3><ul>"
            for anexo in anexos:
                body += f"<li><a href=\"{anexo['link_anexo']}\">Baixar Arquivo</a></li>"
            body += "</ul>"

        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
            server.send_message(msg)
            print(f"E-mail enviado para {msg['To']} com sucesso.")

    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

def processar_envio():
    """Verifica as solicitações completas e envia os e-mails necessários."""
    conn = conectar_banco()
    if not conn:
        return

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT solicitacao 
            FROM conteudo 
            WHERE solicitacao NOT IN (SELECT solicitacao FROM emails_enviados)
        """)

        solicitacoes_pendentes = cursor.fetchall()
        print(f"Solicitações pendentes: {solicitacoes_pendentes} \n")

        for solicitacao in solicitacoes_pendentes:
            dados = verificar_solicitacao_completa(solicitacao['solicitacao'])
            if dados and dados['conteudo']:
                print(f"Enviando e-mail para solicitação {solicitacao['solicitacao']}")
                enviar_email(dados['conteudo'], dados['anexos'])
                registrar_envio(
                    solicitacao['solicitacao'],
                    escolher_workspace_id(dados['conteudo']['unidade_solicitante']),
                    dados['conteudo']['unidade_solicitante'],
                    dados['conteudo']['solicitante'],
                    EMAIL_CONFIG['email']
                )
            else:
                print(f"Solicitação {solicitacao['solicitacao']} incompleta ou sem anexos.")

    except Exception as e:
        print(f"Erro ao processar envio: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    processar_envio()
