from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Ativo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(30), nullable=False)
    transacoes = db.relationship("Transacao", backref="ativo", lazy=True)


class Transacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ativo_id = db.Column(db.Integer, db.ForeignKey("ativo.id"), nullable=False)
    data = db.Column(db.Date, nullable=False)
    tipo = db.Column(db.String(10), nullable=False)
    quantidade = db.Column(db.Float, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)