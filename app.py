from flask import Flask, render_template, request, redirect, url_for
from models import db, Ativo

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///carteira.db"
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/")
def pagina_inicial():
    ativos = Ativo.query.all()
    return render_template("ativos.html", ativos=ativos)

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

@app.route("/sobre")
def sobre():
    return "Projeto de estudo de Python para finanças"


if __name__ == "__main__":
    app.run(debug=True)
