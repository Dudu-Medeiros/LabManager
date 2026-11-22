import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Chaves de seguranca e configuracao do banco
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave-secreta-padrao-dev'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///labmanager.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-chave-secreta-dev'

    # Logs: nivel, pasta e se grava em arquivo (LOG_TO_FILE=0 desliga o arquivo)
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = os.environ.get('LOG_DIR') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    LOG_TO_FILE = os.environ.get('LOG_TO_FILE', '1') != '0'