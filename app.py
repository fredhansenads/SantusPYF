from flask import Flask

app = Flask(__name__)


@app.route("/")
def pagina_inicial():
    return "Minha carteira de investimentos"


@app.route("/sobre")
def sobre():
    return "Projeto de estudo de Python para finanças"


if __name__ == "__main__":
    app.run(debug=True)
    