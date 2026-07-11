import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from models import db, Ativo, Transacao, Provento, Usuario
from datetime import date
from services import (calcular_posicao, grafico_alocacao, grafico_evolucao,
                      comparacao_completa, grafico_patrimonio, graficos_ativo,
                      analise_risco)
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-chave-somente-para-estudo")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///carteira.db"
db.init_app(app)

with app.app_context():
    db.create_all()

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Faça login para acessar."
login_manager.login_message_category = "warning"


@login_manager.user_loader
def carregar_usuario(user_id):
    return db.session.get(Usuario, int(user_id))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = Usuario.query.filter_by(username=request.form["username"]).first()
        if usuario and check_password_hash(usuario.senha_hash, request.form["senha"]):
            login_user(usuario, remember=True)
            return redirect(url_for("pagina_inicial"))
        flash("Usuário ou senha incorretos.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    logout_user()
    flash("Você saiu do sistema.", "success")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def pagina_inicial():
    ativos = Ativo.query.all()
    posicoes = []
    for ativo in ativos:
        p = calcular_posicao(ativo)
        if p is not None:
            posicoes.append(p)

    total_custo = sum(p["custo"] for p in posicoes)
    total_atual = sum(p["valor_atual"] or 0 for p in posicoes)
    total_proventos = sum(p.valor for p in Provento.query.all())
    grafico_pizza = grafico_alocacao(posicoes)

    comparacao = comparacao_completa(ativos)
    grafico_linha = grafico_evolucao(comparacao)
    grafico_patr = grafico_patrimonio(ativos)
    rendimentos = None
    if comparacao is not None and len(comparacao) > 0:
        rendimentos = {coluna: comparacao[coluna].iloc[-1] - 100
                       for coluna in comparacao.columns}

    return render_template("ativos.html", ativos=ativos,
                           posicoes=posicoes,
                           total_custo=total_custo,
                           total_atual=total_atual,
                           total_proventos=total_proventos,
                           rendimentos=rendimentos,
                           grafico_pizza=grafico_pizza,
                           grafico_linha=grafico_linha,
                           grafico_patrimonio=grafico_patr)

@app.route("/novo", methods=["GET", "POST"])
@login_required
def novo_ativo():
    if request.method == "POST":
        ativo = Ativo(
            ticker=request.form["ticker"],
            nome=request.form["nome"],
            tipo=request.form["tipo"],
        )
        db.session.add(ativo)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Já existe um ativo com esse ticker.", "danger")
            return redirect(url_for("novo_ativo"))
        flash("Ativo cadastrado com sucesso!", "success")
        return redirect(url_for("pagina_inicial"))
    return render_template("novo_ativo.html")

@app.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_ativo(id):
    ativo = Ativo.query.get_or_404(id)
    if request.method == "POST":
        ativo.ticker = request.form["ticker"]
        ativo.nome = request.form["nome"]
        ativo.tipo = request.form["tipo"]
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Já existe um ativo com esse ticker.", "danger")
            return redirect(url_for("editar_ativo", id=id))
        flash("Ativo atualizado!", "success")
        return redirect(url_for("pagina_inicial"))
    return render_template("editar_ativo.html", ativo=ativo)


@app.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_ativo(id):
    ativo = Ativo.query.get_or_404(id)
    db.session.delete(ativo)
    db.session.commit()
    flash("Ativo excluído.", "success")
    return redirect(url_for("pagina_inicial"))


@app.route("/transacoes")
@login_required
def listar_transacoes():
    transacoes = Transacao.query.order_by(Transacao.data).all()
    return render_template("transacoes.html", transacoes=transacoes)


@app.route("/transacoes/nova", methods=["GET", "POST"])
@login_required
def nova_transacao():
    if request.method == "POST":
        transacao = Transacao(
            ativo_id=int(request.form["ativo_id"]),
            data=date.fromisoformat(request.form["data"]),
            tipo=request.form["tipo"],
            quantidade=float(request.form["quantidade"]),
            preco_unitario=float(request.form["preco_unitario"]),
        )
        db.session.add(transacao)
        db.session.commit()
        flash("Transação registrada!", "success")
        return redirect(url_for("listar_transacoes"))
    ativos = Ativo.query.all()
    return render_template("nova_transacao.html", ativos=ativos)

@app.route("/transacoes/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_transacao(id):
    transacao = Transacao.query.get_or_404(id)
    db.session.delete(transacao)
    db.session.commit()
    flash("Transação excluída.", "success")
    return redirect(url_for("listar_transacoes"))

@app.route("/ativo/<int:id>")
@login_required
def detalhe_ativo(id):
    ativo = Ativo.query.get_or_404(id)
    posicao = calcular_posicao(ativo)
    graficos = graficos_ativo(ativo)
    return render_template("ativo.html", ativo=ativo,
                           posicao=posicao, graficos=graficos)


@app.route("/analises")
@login_required
def analises():
    ativos = Ativo.query.all()
    linhas, correlacao = analise_risco(ativos)
    tabela_correlacao = None
    if correlacao is not None:
        tabela_correlacao = correlacao.to_html(classes="table table-striped",
                                               border=0)
    return render_template("analises.html", linhas=linhas,
                           tabela_correlacao=tabela_correlacao)


@app.route("/proventos")
@login_required
def listar_proventos():
    proventos = Provento.query.order_by(Provento.data).all()
    return render_template("proventos.html", proventos=proventos)


@app.route("/proventos/novo", methods=["GET", "POST"])
@login_required
def novo_provento():
    if request.method == "POST":
        provento = Provento(
            ativo_id=int(request.form["ativo_id"]),
            data=date.fromisoformat(request.form["data"]),
            tipo=request.form["tipo"],
            valor=float(request.form["valor"]),
        )
        db.session.add(provento)
        db.session.commit()
        flash("Provento registrado!", "success")
        return redirect(url_for("listar_proventos"))
    ativos = Ativo.query.all()
    return render_template("novo_provento.html", ativos=ativos)


@app.route("/proventos/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_provento(id):
    provento = Provento.query.get_or_404(id)
    db.session.delete(provento)
    db.session.commit()
    flash("Provento excluído.", "success")
    return redirect(url_for("listar_proventos"))


@app.route("/sobre")
def sobre():
    return "Projeto de estudo de Python para finanças"


if __name__ == "__main__":
    app.run(debug=True)
