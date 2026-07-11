from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)


class Ativo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(60), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(30), nullable=False)
    transacoes = db.relationship("Transacao", backref="ativo", lazy=True, cascade="all, delete-orphan")
    proventos = db.relationship("Provento", backref="ativo", lazy=True, cascade="all, delete-orphan")


class Transacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ativo_id = db.Column(db.Integer, db.ForeignKey("ativo.id"), nullable=False)
    data = db.Column(db.Date, nullable=False)
    tipo = db.Column(db.String(10), nullable=False)
    quantidade = db.Column(db.Float, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)


class Provento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ativo_id = db.Column(db.Integer, db.ForeignKey("ativo.id"), nullable=False)
    data = db.Column(db.Date, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    valor = db.Column(db.Float, nullable=False)