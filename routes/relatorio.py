from flask import Blueprint, render_template, request, jsonify
from db_config import db  # ajuste se o seu SQLAlchemy for importado de outro lugar
from models.models import Relatorio  # modelo Area já criado

relatorio_route = Blueprint('Relatorio', __name__)

# GET - Página de cadastro
@relatorio_route.route('/', methods=['GET'])
def relatorio_page():
    relatorios = Relatorio.query.order_by(Relatorio.data).all()
    return render_template('relatorios.html', relatorios=relatorios)