from app import db

class Fila(db.Model):
    __tablename__ = 'filas'
    
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(50), nullable=False)
    sigla = db.Column(db.String(2), unique=True, nullable=False)