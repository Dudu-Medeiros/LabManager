import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Chaves de seguranca e configuracao do banco
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave-secreta-padrao-dev'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///labmanager.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-chave-secreta-dev'