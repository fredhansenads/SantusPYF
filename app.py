from flask import Flask, render_template, request, redirect, url_for
from models import db, Ativo, Transacao
from datetime import date
from services import calcular_posicao


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///carteira.db"
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/")
def pagina_inicial():
    ativos = Ativo.query.all()
    posicoes = []
    for ativo in ativos:
        p = calcular_posicao(ativo)
        if p is not None:
            posicoes.append(p)

    total_custo = sum(p["custo"] for p in posicoes)
    total_atual = sum(p["valor_atual"] or 0 for p in posicoes)

    return render_template("ativos.html", ativos=ativos,
                           posicoes=posicoes,
                           total_custo=total_custo,
                           total_atual=total_atual)

@app.route("/novo", methods=["GET", "POST"])
def novo_ativo():
    if request.method == "POST":
        ativo = Ativo(
            ticker=request.form["ticker"],
            nome=request.form["nome"],
            tipo=request.form["tipo"],
        )
        db.session.add(ativo)
        db.session.commit()
        return redirect(url_for("pagina_inicial"))
    return render_template("novo_ativo.html")

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar_ativo(id):
    ativo = Ativo.query.get_or_404(id)
    if request.method == "POST":
        ativo.ticker = request.form["ticker"]
        ativo.nome = request.form["nome"]
        ativo.tipo = request.form["tipo"]
        db.session.commit()
        return redirect(url_for("pagina_inicial"))
    return render_template("editar_ativo.html", ativo=ativo)


@app.route("/excluir/<int:id>", methods=["POST"])
def excluir_ativo(id):
    ativo = Ativo.query.get_or_404(id)
    db.session.delete(ativo)
    db.session.commit()
    return redirect(url_for("pagina_inicial"))


@app.route("/transacoes")
def listar_transacoes():
    transacoes = Transacao.query.order_by(Transacao.data).all()
    return render_template("transacoes.html", transacoes=transacoes)


@app.route("/transacoes/nova", methods=["GET", "POST"])
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
        return redirect(url_for("listar_transacoes"))
    ativos = Ativo.query.all()
    return render_template("nova_transacao.html", ativos=ativos)

@app.route("/transacoes/excluir/<int:id>", methods=["POST"])
def excluir_transacao(id):
    transacao = Transacao.query.get_or_404(id)
    db.session.delete(transacao)
    db.session.commit()
    return redirect(url_for("listar_transacoes"))

@app.route("/sobre")
def sobre():
    return "Projeto de estudo de Python para finanças"


if __name__ == "__main__":
    app.run(debug=True)
