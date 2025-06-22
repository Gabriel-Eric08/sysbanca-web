from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from util.checkCreds import checkCreds
from db_config import db

area_comissao_route = Blueprint('AreaComissaoModalidade', __name__)

@area_comissao_route.route('/')
def area_comissao_page():

    check_result = checkCreds()

    if not check_result['success']:
        return check_result['message'], 401  
    
    user = check_result['user']

    try:
        if int(user.acesso_area_comissao_modalidade) != 1:
            return "Usuário não autorizado", 403
    except (AttributeError, ValueError):
        return "Configuração de permissão inválida", 500
    
    return render_template('AreaComissaoModalidade.html')