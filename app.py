import logging
from flask import Flask, request, redirect
from routes.home import home_route
from routes.modalidade import modalidade_route
from routes.regiao import regiao_route
from routes.area import area_route
from routes.auth import auth_route
from routes.areacotacao import area_cotacao_route
from routes.extracao import extracao_route
from routes.vendedores import vendedor_route
from db_config import init_db
from routes.resultado import resultado_route
from routes.resultado1 import resultado1_route
from routes.coletor import coletor_route
from routes.areaextracao import area_extracao_route
from routes.areacomissaomodalidade import area_comissao_route
from routes.apostas import aposta_route
from routes.relatorio import relatorio_route
from routes.admin import admin_route
from routes.cadastro_descarrego import cadastro_descarrego_route
from routes.descarrego import descarrego_route
import unicodedata
import re
import json

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

def from_json_filter(value):
    """Filtro personalizado para converter string JSON em objeto Python."""
    return json.loads(value)

# Registra o filtro no ambiente do Jinja2
app.jinja_env.filters['from_json'] = from_json_filter

app.register_blueprint(auth_route)
app.register_blueprint(admin_route, url_prefix='/admin')
app.register_blueprint(relatorio_route, url_prefix='/relatorio')
app.register_blueprint(aposta_route, url_prefix='/aposta')
app.register_blueprint(area_comissao_route, url_prefix='/area-comissao')
app.register_blueprint(cadastro_descarrego_route, url_prefix='/cadastrodescarrego')
app.register_blueprint(descarrego_route, url_prefix='/descarrego')
app.register_blueprint(area_extracao_route, url_prefix='/areaextracao')
app.register_blueprint(coletor_route, url_prefix='/coletor')
app.register_blueprint(resultado_route, url_prefix='/resultado')
app.register_blueprint(resultado1_route, url_prefix='/resultado1')
app.register_blueprint(vendedor_route, url_prefix='/vendedor')
app.register_blueprint(area_cotacao_route, url_prefix='/areacotacao')
app.register_blueprint(home_route, url_prefix='/home')
app.register_blueprint(modalidade_route, url_prefix='/modalidade')
app.register_blueprint(regiao_route, url_prefix='/regiao')
app.register_blueprint(area_route, url_prefix='/area')
app.register_blueprint(extracao_route, url_prefix='/extracao')

def normalize_extracao(value):
    if not value:
        return ''
    value = unicodedata.normalize('NFD', value).encode('ascii', 'ignore').decode('utf-8')
    value = value.lower()
    value = re.sub(r'[:\-\.\s]', '_', value)
    value = re.sub(r'[^a-z0-9_]', '', value)
    return f"extracao_{value}"

app.jinja_env.filters['normalize'] = normalize_extracao

def remover_acentos(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

# No Flask, registre o filtro
app.jinja_env.filters['remover_acentos'] = remover_acentos

if __name__ == "__main__":
    app.run(debug=True)
