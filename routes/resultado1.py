from flask import Blueprint, render_template, jsonify, request
from util.checkCreds import checkCreds
from util.get_animal_grupo import num_animal_grupo
from db_config import db
from models.models import Resultado, Extracao
from datetime import datetime

resultado1_route = Blueprint('Resultado1', __name__)

@resultado1_route.route('/')
def resultado1_page():
    check_result = checkCreds()
    
    if not check_result['success']:
        return check_result['message'], 401
    
    user = check_result['user']
    
    try:
        if int(user.acesso_modalidade) != 1:
            return "Usuário não autorizado", 403
    except (AttributeError, ValueError):
        return "Configuração de permissão inválida", 500

    extracoes = Extracao.query.all()
    # A rota "/" deve ter o mesmo comportamento de uma consulta vazia
    return render_template('resultados.html', 
                           extracoes=extracoes, 
                           resultado=None,
                           extracao_selecionada=None, 
                           data_selecionada=None,
                           pode_salvar=False)

@resultado1_route.route('consultar/<extracao>/<data>/', methods=['GET'])
def consultar_resultado(extracao, data):
    try:
        data_formatada = datetime.strptime(data, '%Y-%m-%d').date()

        resultado = Resultado.query.filter_by(extracao=extracao).filter(
            db.func.date(Resultado.data) == data_formatada
        ).first()

        extracoes = Extracao.query.all()

        if resultado:
            premios = {
                'premio_1': resultado.premio_1,
                'premio_2': resultado.premio_2,
                'premio_3': resultado.premio_3,
                'premio_4': resultado.premio_4,
                'premio_5': resultado.premio_5,
                'premio_6': resultado.premio_6,
                'premio_7': resultado.premio_7,
                'premio_8': resultado.premio_8,
                'premio_9': resultado.premio_9,
                'premio_10': resultado.premio_10,
            }
            return render_template('resultados.html', extracoes=extracoes, resultado=premios, extracao_selecionada=extracao, data_selecionada=data, pode_salvar=False)
        else:
            return render_template('resultados.html', extracoes=extracoes, resultado=None, extracao_selecionada=extracao, data_selecionada=data, pode_salvar=False)
    except Exception as e:
        return f"Erro: {str(e)}", 500