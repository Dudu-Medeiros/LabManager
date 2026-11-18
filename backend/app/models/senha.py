from app import db
from datetime import datetime, timezone

class Senha(db.Model):
    __tablename__ = 'senhas'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    tipo = db.Column(db.String(2), nullable=False) 
    estado_atual = db.Column(db.String(30), default='EMITIDA', nullable=False)
    data_emissao = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    guiche = db.Column(db.String(10), nullable=True)
    versao = db.Column(db.Integer, default=1, nullable=False)
    
    # Relacionamentos (Chaves Estrangeiras)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    usuario = db.relationship('Usuario', backref='senhas_atendidas')
    
    # Para respeitar o edital de totem anônimo
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=True)
    paciente = db.relationship('Paciente', backref='historico_senhas')
    
    fila_id = db.Column(db.Integer, db.ForeignKey('filas.id'), nullable=True)
    fila = db.relationship('Fila', backref='senhas_vinculadas')