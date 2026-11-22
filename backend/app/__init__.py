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

    # Importa os models para o SQLAlchemy reconhecer as tabelas antes de criar o banco
    with app.app_context():
        from .models.usuario import Usuario
        from .models.senha import Senha
        from .models.historico import HistoricoEstado
        from .models.paciente import Paciente
        from .models.fila import Fila

    # Registra os blueprints de rotas
    from .routes.auth_routes import auth_bp
    from .routes.senha_routes import senha_bp
    from .routes.relatorio_routes import relatorio_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(senha_bp)
    app.register_blueprint(relatorio_bp)
    
    # Rota de Health Check para monitoramento e recuperacao de desastres
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'ok', 
            'message': 'API do LabManager rodando com sucesso!'
        }), 200

    # Comando personalizado para popular o banco de dados
    @app.cli.command("seed")
    def seed_data():
        """Popula o banco com os usuarios de teste."""
        from .models.usuario import Usuario
        from werkzeug.security import generate_password_hash
        
        # Só cria se o atendente ainda não existir no banco
        if not Usuario.query.filter_by(email='atendente@labflow.com').first():
            senha_padrao = generate_password_hash('password123')
            
            atendente = Usuario(
                nome='Atendente de Teste', 
                email='atendente@labflow.com', 
                senha_hash=senha_padrao, 
                perfil='ATENDENTE'
            )
            gestor = Usuario(
                nome='Gestor de Teste', 
                email='gestor@labflow.com', 
                senha_hash=senha_padrao, 
                perfil='GESTOR'
            )
            
            db.session.add(atendente)
            db.session.add(gestor)
            db.session.commit()
            print("✅ Usuários de teste (Atendente e Gestor) criados com sucesso!")
        else:
            print("⚠️ Os usuários já existem no banco de dados.")

    return app