from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config

# Inicializacao global das extensoes
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Vincula as extensoes ao app
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Rota de Health Check para monitoramento e recuperacao de desastres
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'ok', 
            'message': 'API do LabManager rodando com sucesso!'
        }), 200

    return app