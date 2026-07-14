import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from models import db, Ativo, Transacao, Provento, Controle, Usuario
from datetime import date
from services import (calcular_posicao, quantidade_em_posicao, grafico_alocacao,
                      grafico_evolucao, comparacao_completa, grafico_patrimonio,
                      graficos_ativo, analise_risco)
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
    return render_template("ativos.html", ativos=ativos)


@app.route("/dashboard")
@login_required
def dashboard():
    ativos = Ativo.query.all()
    posicoes = []
    for ativo in ativos:
        p = calcular_posicao(ativo)
        if p is not None:
            posicoes.append(p)

    total_custo = sum(p["custo"] for p in posicoes)
    total_atual = sum(p["valor_atual"] or 0 for p in posicoes)
    total_proventos = sum(p.valor for p in Provento.query.all())

    tema = request.cookies.get("tema", "escuro")
    grafico_pizza = grafico_alocacao(posicoes, tema)

    comparacao = comparacao_completa(ativos)
    grafico_linha = grafico_evolucao(comparacao, tema)
    grafico_patr = grafico_patrimonio(ativos, tema)
    rendimentos = None
    if comparacao is not None and len(comparacao) > 0:
        rendimentos = {coluna: comparacao[coluna].iloc[-1] - 100
                       for coluna in comparacao.columns}

    return render_template("_dashboard.html",
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
            corretora=request.form.get("corretora", "").strip() or None,
        )
        db.session.add(transacao)
        db.session.commit()
        flash("Transação registrada!", "success")
        return redirect(url_for("listar_transacoes"))
    ativos = Ativo.query.all()
    return render_template("nova_transacao.html", ativos=ativos)

@app.route("/transacoes/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_transacao(id):
    transacao = Transacao.query.get_or_404(id)
    if request.method == "POST":
        transacao.ativo_id = int(request.form["ativo_id"])
        transacao.data = date.fromisoformat(request.form["data"])
        transacao.tipo = request.form["tipo"]
        transacao.quantidade = float(request.form["quantidade"])
        transacao.preco_unitario = float(request.form["preco_unitario"])
        transacao.corretora = request.form.get("corretora", "").strip() or None
        db.session.commit()
        flash("Transação atualizada!", "success")
        return redirect(url_for("listar_transacoes"))
    ativos = Ativo.query.all()
    return render_template("editar_transacao.html",
                           transacao=transacao, ativos=ativos)


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
    salvos = session.get(f"graficos_ativo_{id}", {})
    return render_template("ativo.html", ativo=ativo, posicao=posicao,
                           mm1=salvos.get("mm1", 20),
                           mm2=salvos.get("mm2", 50),
                           rsi_periodo=salvos.get("rsi", 14),
                           tipo_grafico=salvos.get("grafico", "linha"))


@app.route("/ativo/<int:id>/graficos")
@login_required
def graficos_do_ativo(id):
    ativo = Ativo.query.get_or_404(id)

    chave_sessao = f"graficos_ativo_{id}"
    salvos = session.get(chave_sessao, {})

    mm1 = min(max(request.args.get("mm1", salvos.get("mm1", 20), type=int), 1), 200)
    mm2 = min(max(request.args.get("mm2", salvos.get("mm2", 50), type=int), 1), 200)
    rsi_periodo = min(max(request.args.get("rsi", salvos.get("rsi", 14), type=int), 2), 50)
    tipo_grafico = request.args.get("grafico", salvos.get("grafico", "linha"))

    session[chave_sessao] = {"mm1": mm1, "mm2": mm2,
                             "rsi": rsi_periodo, "grafico": tipo_grafico}

    tema = request.cookies.get("tema", "escuro")
    graficos = graficos_ativo(ativo, mm1, mm2, tipo_grafico, rsi_periodo, tema)
    return render_template("_graficos_ativo.html", graficos=graficos)


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


def _data_ou_none(texto):
    return date.fromisoformat(texto) if texto else None


def _valor_ou_none(texto):
    return float(texto) if texto else None


def _posicoes_disponiveis():
    itens = []
    for ativo in Ativo.query.order_by(Ativo.ticker).all():
        q = quantidade_em_posicao(ativo)
        if q is not None:
            itens.append((ativo, q))
    return itens


@app.route("/controle")
@login_required
def listar_controle():
    itens = Controle.query.order_by(Controle.data_com).all()
    return render_template("controle.html", itens=itens)


@app.route("/controle/novo", methods=["GET", "POST"])
@login_required
def novo_controle():
    if request.method == "POST":
        ativo = Ativo.query.get_or_404(int(request.form["ativo_id"]))
        item = Controle(
            ativo_id=ativo.id,
            quantidade=quantidade_em_posicao(ativo) or 0,
            data_com=_data_ou_none(request.form.get("data_com")),
            data_pagamento=_data_ou_none(request.form.get("data_pagamento")),
            valor=_valor_ou_none(request.form.get("valor")),
        )
        db.session.add(item)
        db.session.commit()
        flash("Lançamento de controle registrado!", "success")
        return redirect(url_for("listar_controle"))
    return render_template("novo_controle.html", posicoes=_posicoes_disponiveis())


@app.route("/controle/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_controle(id):
    item = Controle.query.get_or_404(id)
    if request.method == "POST":
        item.data_com = _data_ou_none(request.form.get("data_com"))
        item.data_pagamento = _data_ou_none(request.form.get("data_pagamento"))
        item.valor = _valor_ou_none(request.form.get("valor"))
        db.session.commit()
        flash("Lançamento atualizado!", "success")
        return redirect(url_for("listar_controle"))
    return render_template("editar_controle.html", item=item)


@app.route("/controle/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_controle(id):
    item = Controle.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash("Lançamento excluído.", "success")
    return redirect(url_for("listar_controle"))


@app.route("/sw.js")
def service_worker():
    return app.send_static_file("sw.js")


@app.route("/sobre")
def sobre():
    return "Projeto de estudo de Python para finanças"


if __name__ == "__main__":
    app.run(debug=True)
