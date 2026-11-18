from app import db
from datetime import datetime, timezone

class HistoricoEstado(db.Model):
    __tablename__ = 'historico_estados'
    
    id = db.Column(db.Integer, primary_key=True)
    senha_id = db.Column(db.Integer, db.ForeignKey('senhas.id'), nullable=False)
    estado = db.Column(db.String(30), nullable=False)
    data_hora = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    senha = db.relationship('Senha', backref=db.backref('historico', lazy=True))