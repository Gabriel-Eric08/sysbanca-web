from flask import Blueprint, render_template, request, jsonify
from db_config import db
from models.models import Relatorio, Aposta, Extracao, Area, Vendedor  

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
def relatorio_page1():
    apostas = Aposta.query.order_by(Aposta.data_atual.desc()).all()
    total_geral = sum(aposta.valor_total for aposta in apostas)

    areas= Area.query.all()
    extracoes=Extracao.query.all()
    vendedores=Vendedor.query.all()

    return render_template('relatoriovendas.html', apostas=apostas, total_geral=round(total_geral, 2), areas=areas,extracoes=extracoes,vendedores=vendedores)