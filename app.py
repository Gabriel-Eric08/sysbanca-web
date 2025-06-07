import logging
from flask import Flask, request, redirect
from routes.home import home_route
from routes.users import users_route
from routes.modalidade import modalidade_route
from routes.regiao import regiao_route
from routes.area import area_route
from routes.auth import auth_route
from routes.areacotacao import area_cotacao_route
from routes.extracao import extracao_route
from routes.operador import operadores_route
from db_config import init_db
from routes.resultado import resultado_route
from routes.coletor import coletor_route
from routes.areaextracao import area_extracao_route
from routes.areacomissaomodalidade import area_comissao_route

app = Flask(__name__)
init_db(app)

# Configuração básica do logger
logging.basicConfig(level=logging.INFO)

# Log antes de cada requisição
@app.before_request
def before_request_func():
    logging.info(f"Handling request: {request.method} {request.path}")

# Log após cada requisição
@app.after_request
def after_request_func(response):
    logging.info(f"Response status: {response.status_code}")
    return response

@app.route("/health")
def health():
    return "OK"
    
app.register_blueprint(auth_route)
app.register_blueprint(area_comissao_route, url_prefix='/areacomissaomodalidade')
app.register_blueprint(area_extracao_route, url_prefix='/areaextracao')
app.register_blueprint(coletor_route, url_prefix='/coletor')
app.register_blueprint(resultado_route, url_prefix='/resultado')
app.register_blueprint(operadores_route, url_prefix='/operador')
app.register_blueprint(area_cotacao_route, url_prefix='/areacotacao')
app.register_blueprint(home_route, url_prefix='/home')
app.register_blueprint(modalidade_route, url_prefix='/modalidade')
app.register_blueprint(regiao_route, url_prefix='/regiao')
app.register_blueprint(area_route, url_prefix='/area')
app.register_blueprint(users_route, url_prefix='/users')
app.register_blueprint(extracao_route, url_prefix='/extracao')

if __name__ == "__main__":
    app.run(debug=True)
