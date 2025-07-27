# web_finance/config.py

import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()


# Classe de configuração para a aplicação Flask
class Config:
    # Chave secreta para segurança da aplicação (sessões, CSRF, etc.)
    SECRET_KEY = os.environ.get("SECRET_KEY")
    # URI de conexão com o banco de dados PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    # Desabilita o rastreamento de modificações do SQLAlchemy (economiza memória)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Define o ambiente do Flask (e.g., 'development', 'production')
    FLASK_ENV = os.environ.get("FLASK_ENV")

    # Configuração para direcionar logs para o console em ambientes de deploy
    LOG_TO_STDOUT = os.environ.get("LOG_TO_STDOUT")
    # Caminho completo para o arquivo de log
    LOG_FILE = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "logs", "web_finance.log"
    )
    # Nível mínimo de mensagens de log a serem registradas (INFO, WARNING, ERROR, etc.)
    LOG_LEVEL = logging.INFO

    # Tamanho máximo do arquivo de log antes de ser rotacionado (5 MB)
    LOG_MAX_BYTES = 1024 * 1024 * 5
    # Número de arquivos de log de backup a serem mantidos
    LOG_BACKUP_COUNT = 5
