from flask import Blueprint, render_template, request, jsonify
from db_config import db  # ajuste se o seu SQLAlchemy for importado de outro lugar
from models.models import Relatorio, Aposta  # modelo Area já criado

relatorio_route = Blueprint('Relatorio', __name__)

# GET - Página de cadastro
@relatorio_route.route('/', methods=['GET'])
def relatorio_page():
    relatorios = Relatorio.query.order_by(Relatorio.data).all()
    return render_template('relatorios.html', relatorios=relatorios)

@relatorio_route.route('/vendas/json', methods=['GET'])
def relatorio_vendas():
    apostas = Aposta.query.order_by(Aposta.data_atual.desc()).all()

    total_geral = sum(aposta.valor_total for aposta in apostas)

    resultado = [{
        'relatorio_geral': True,
        'valor_total_apostas': round(total_geral, 2)
    }]

    for aposta in apostas:
        resultado.append({
            'id': aposta.id,
            'data': aposta.data_atual.strftime('%Y-%m-%d'),
            'area': aposta.area,
            'extracao': aposta.extracao,
            'valor_total': round(aposta.valor_total, 2),
            'vendedor': aposta.vendedor
        })

    return jsonify(resultado)

@relatorio_route.route('/vendas', methods=['GET'])
def relatorio_page():
    apostas = Aposta.query.order_by(Aposta.data_atual.desc()).all()
    total_geral = sum(aposta.valor_total for aposta in apostas)

    return render_template('relatorios.html', apostas=apostas, total_geral=round(total_geral, 2))