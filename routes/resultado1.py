from flask import Blueprint, render_template, jsonify, request
from util.checkCreds import checkCreds
from util.get_animal_grupo import num_animal_grupo
from db_config import db
from models.models import Resultado, Extracao
from datetime import datetime

resultado1_route = Blueprint('Resultado1', __name__)

@resultado1_route.route('/')
def resultado_page():

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
    return render_template('resultados.html', extracoes=extracoes)