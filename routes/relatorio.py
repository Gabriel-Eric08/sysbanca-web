from flask import Blueprint, render_template, request, jsonify
from db_config import db
from models.models import Relatorio, Aposta, Extracao, Area, Vendedor, Cotado, ApostaExcluida
from collections import defaultdict
import ast

relatorio_route = Blueprint('Relatorio', __name__)

# GET - Página de cadastro
@relatorio_route.route('/', methods=['GET'])
def relatorio_page():
    relatorios = Relatorio.query.order_by(Relatorio.data).all()
    return render_template('relatorios.html', relatorios=relatorios)

@relatorio_route.route('/vendas/json', methods=['GET'])
def relatorio_vendas1():
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

@relatorio_route.route('/vendas/json', methods=['POST'])
def relatorio_vendas():
    data = request.get_json()
    nome_vendedor = data.get('Vendedor')

    if not nome_vendedor:
        return jsonify({'erro': 'Campo "Vendedor" é obrigatório.'}), 400

    apostas = Aposta.query.filter_by(vendedor=nome_vendedor).order_by(Aposta.data_atual.desc()).all()

    total_geral = sum(aposta.valor_total for aposta in apostas)

    # Soma por extração
    soma_por_extracao = defaultdict(float)
    for aposta in apostas:
        soma_por_extracao[aposta.extracao] += aposta.valor_total

    resultado = [{
        'relatorio_geral': True,
        'valor_total_apostas': round(total_geral, 2)
    }]

    # Adiciona as somas por extração
    for extracao, total in soma_por_extracao.items():
        resultado.append({
            'extracao': extracao,
            'valor_total': round(total, 2)
        })

    # Detalhe das apostas
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

@relatorio_route.route('/vendas/json/modalidades', methods=['POST'])
def relatorio_vendas_por_modalidade():
    data = request.get_json()
    nome_vendedor = data.get('Vendedor')

    if not nome_vendedor:
        return jsonify({'erro': 'Campo "Vendedor" é obrigatório.'}), 400

    # Filtra apostas pelo nome do vendedor
    apostas_bilhetes = Aposta.query.filter_by(vendedor=nome_vendedor).order_by(Aposta.data_atual.desc()).all()

    soma_por_modalidade = defaultdict(float)
    total_geral = 0.0
    resultado = []

    # Lista com os detalhes de todas as subapostas
    detalhes_apostas = []

    for bilhete in apostas_bilhetes:
        try:
            lista_apostas = ast.literal_eval(bilhete.apostas)  # Transforma a string em lista Python
        except Exception as e:
            continue  # pula se não conseguir converter

        for aposta in lista_apostas:
            if len(aposta) < 6:
                continue  # ignora se a estrutura estiver incorreta

            nome_aposta = aposta[0]
            numeros = aposta[1]
            modalidade = aposta[2]
            tipo = aposta[3]
            valor_total = aposta[4]  # Total dessa subaposta
            valor_unidade = aposta[5]

            soma_por_modalidade[modalidade] += valor_total
            total_geral += valor_total

            detalhes_apostas.append({
                'id': bilhete.id,
                'data': bilhete.data_atual.strftime('%Y-%m-%d'),
                'area': bilhete.area,
                'extracao': bilhete.extracao,
                'modalidade': modalidade,
                'tipo': tipo,
                'numeros': numeros,
                'valor_total': round(valor_total, 2),
                'valor_unidade': round(valor_unidade, 2),
                'vendedor': bilhete.vendedor
            })

    resultado.append({
        'relatorio_geral': True,
        'valor_total_apostas': round(total_geral, 2)
    })

    for modalidade, total in soma_por_modalidade.items():
        resultado.append({
            'modalidade': modalidade,
            'valor_total': round(total, 2)
        })

    resultado.extend(detalhes_apostas)

    return jsonify(resultado)

@relatorio_route.route('/vendas', methods=['GET'])
def relatorio_page1():
    apostas = Aposta.query.order_by(Aposta.data_atual.desc()).all()
    total_geral = sum(aposta.valor_total for aposta in apostas)

    areas= Area.query.all()
    extracoes=Extracao.query.all()
    vendedores=Vendedor.query.all()

    return render_template('relatoriovendas.html', apostas=apostas, total_geral=round(total_geral, 2), areas=areas,extracoes=extracoes,vendedores=vendedores)


@relatorio_route.route('/apostasexcluidas', methods=['GET'])
def relatorio_apostas_excluidas():
    apostas = ApostaExcluida.query.order_by(ApostaExcluida.data_atual.desc()).all()
    total_geral = sum(aposta.valor_total for aposta in apostas)

    areas = Area.query.all()
    extracoes = Extracao.query.all()
    vendedores = Vendedor.query.all()

    return render_template(
        'relatoriovendas_excluidas.html',
        apostas=apostas,
        total_geral=round(total_geral, 2),
        areas=areas,
        extracoes=extracoes,
        vendedores=vendedores,
        excluidas=True  # Flag para indicar se são apostas excluídas
    )

@relatorio_route.route('/cotados/', methods=['GET'])
def listar_numeros_cotados():
    cotados = Cotado.query.with_entities(Cotado.numero).all()
    numeros = [c.numero for c in cotados]
    return jsonify(numeros)