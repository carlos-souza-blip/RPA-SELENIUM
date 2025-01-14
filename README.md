# Automação para Gerenciamento e Validação de Solicitações

Este projeto tem como objetivo otimizar o tempo de execução manual da equipe de marketing, automatizando o gerenciamento e validação de solicitações com status "Em Execução". A automação captura informações diretamente de um sistema web utilizado pela empresa, armazena os dados em um banco de dados relacional e dispara e-mails para integração com uma página de terceiros, visando o cálculo de indicadores de desempenho.

## Funcionalidades Principais

- **Captura de dados do sistema web**: Utiliza Selenium para acessar o site, navegar até a seção de solicitações e extrair informações relevantes.
- **Armazenamento em banco de dados**: Insere os dados capturados em uma tabela MySQL, com verificações para evitar duplicidades.
- **Disparo de e-mails**: Gera e-mails automaticamente com os detalhes das solicitações e anexos, enviando para o destinatário correto.
- **Cálculo de indicadores**: Integra-se com uma página de terceiros para facilitar o cálculo de indicadores de performance.

## Benefícios

- Redução significativa do tempo gasto em tarefas manuais.
- Garantia de consistência e organização dos dados.
- Facilidade no acompanhamento e análise de indicadores de desempenho.
- Automação de processos repetitivos, permitindo que a equipe se concentre em tarefas mais estratégicas.

---

## Tecnologias Utilizadas

- **Python**: Para desenvolvimento do script de automação.
- **Selenium**: Para interação com o sistema web.
- **MySQL**: Para armazenamento e gerenciamento dos dados.
- **SMTP**: Para envio automatizado de e-mails.
---
