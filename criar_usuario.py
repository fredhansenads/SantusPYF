"""Cria (ou atualiza a senha de) um usuário do sistema.

Uso: python criar_usuario.py
"""
from getpass import getpass

from werkzeug.security import generate_password_hash

from app import app
from models import db, Usuario

with app.app_context():
    username = input("Nome de usuário: ").strip()
    senha = getpass("Senha (não aparece ao digitar): ")
    confirma = getpass("Confirme a senha: ")

    if not username or not senha:
        print("Usuário e senha não podem ser vazios. Nada foi criado.")
        raise SystemExit(1)
    if senha != confirma:
        print("As senhas não conferem. Nada foi criado.")
        raise SystemExit(1)

    usuario = Usuario.query.filter_by(username=username).first()
    if usuario:
        usuario.senha_hash = generate_password_hash(senha)
        print(f"Senha atualizada para o usuário '{username}'.")
    else:
        db.session.add(Usuario(username=username,
                               senha_hash=generate_password_hash(senha)))
        print(f"Usuário '{username}' criado.")
    db.session.commit()
