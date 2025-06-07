from flask import Blueprint, render_template, jsonify, request
from util.checkCreds import checkCreds
from util.get_animal_grupo import num_animal_grupo
from db_config import db
from models.models import Resultado
from datetime import datetime

resultado_route = Blueprint('Resultado', __name__)

@resultado_route.route('/')
def resultado_page():
    check_creds = checkCreds()
    if check_creds['success'] == True:
        return render_template('resultados.html')
    else:
        return check_creds['message']
    
@resultado_route.route('/json')
def json_resultados():
    resultados = Resultado.query.all()

    resultado = []

    for r in resultados:
        linha = {
            'id': r.id,
            'extracao': r.extracao,
            'data': r.data.strftime('%Y-%m-%d'),  # formatando datetime
            'premio_1': num_animal_grupo(r.premio_1),
            'premio_2': num_animal_grupo(r.premio_2),
            'premio_3': num_animal_grupo(r.premio_3),
            'premio_4': num_animal_grupo(r.premio_4),
            'premio_5': num_animal_grupo(r.premio_5),
            'premio_6': num_animal_grupo(r.premio_6),
            'premio_7': num_animal_grupo(r.premio_7),
            'premio_8': num_animal_grupo(r.premio_8),
            'premio_9': num_animal_grupo(r.premio_9),
            'premio_10': num_animal_grupo(r.premio_10)
        }
        resultado.append(linha)

    return jsonify(resultado)

@resultado_route.route('/salvar', methods=['POST'])
def salvar_resultado():
    data = request.get_json()

    extracao = data.get('extracao')
    data_str = data.get('data')
    premios = data.get('premios')  # Lista com 10 elementos

    if not extracao or not data_str or not premios or len(premios) != 10:
        return jsonify({'message': 'Dados inválidos'}), 400

    try:
        data_formatada = datetime.strptime(data_str, '%Y-%m-%d')

        novo_resultado = Resultado(
            extracao=extracao,
            data=data_formatada,
            premio_1=premios[0],
            premio_2=premios[1],
            premio_3=premios[2],
            premio_4=premios[3],
            premio_5=premios[4],
            premio_6=premios[5],
            premio_7=premios[6],
            premio_8=premios[7],
            premio_9=premios[8],
            premio_10=premios[9]
        )

        db.session.add(novo_resultado)
        db.session.commit()

        return jsonify({'message': 'Resultado salvo com sucesso!'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao salvar: {str(e)}'}), 500