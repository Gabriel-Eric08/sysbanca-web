from flask import Flask, Blueprint
from routes.home import home_route
from routes.users import users_route
from routes.modalidade import modalidade_route
from routes.regiao import regiao_route
from routes.area import area_route
from routes.extracao import extracao_route
from db_config import init_db

app = Flask(__name__)
init_db(app)

@app.route("/health")
def health():
    return "OK"

app.register_blueprint(home_route)
app.register_blueprint(modalidade_route, url_prefix='/modalidade')
app.register_blueprint(regiao_route, url_prefix='/regiao')
app.register_blueprint(area_route, url_prefix='/area')
app.register_blueprint(users_route, url_prefix='/users')
app.register_blueprint(extracao_route, url_prefix='/extracao')

if __name__ == "__main__":
    app.run(debug=True)