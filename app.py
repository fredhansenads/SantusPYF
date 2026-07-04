from flask import Flask
from models import db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///carteira.db"
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/")
def pagina_inicial():
    return "Minha carteira de investimentos"


@app.route("/sobre")
def sobre():
    return "Projeto de estudo de Python para finanças"


if __name__ == "__main__":
    app.run(debug=True)
