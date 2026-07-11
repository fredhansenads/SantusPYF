"""Aplica migrações pendentes no banco de dados (seguro rodar mais de uma vez).

Uso: python migrar_banco.py
"""
from sqlalchemy import text

from app import app
from models import db

with app.app_context():
    colunas = [linha[1] for linha in
               db.session.execute(text("PRAGMA table_info(transacao)"))]

    if "corretora" not in colunas:
        db.session.execute(text(
            "ALTER TABLE transacao ADD COLUMN corretora VARCHAR(50)"))
        db.session.commit()
        print("Coluna 'corretora' adicionada à tabela transacao.")
    else:
        print("Coluna 'corretora' já existe. Nada a fazer.")

    print("Migração concluída.")
