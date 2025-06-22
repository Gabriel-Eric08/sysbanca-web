from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from util.checkCreds import checkCreds
from db_config import db

coletor_route = Blueprint('Coletor', __name__)

@coletor_route.route('/')
def coletor_page():

    check_result = checkCreds()

    if not check_result['success']:
        return check_result['message'], 401  
    
    user = check_result['user']

    try:
        if int(user.acesso_coletor) != 1:
            return "Usuário não autorizado", 403
    except (AttributeError, ValueError):
        return "Configuração de permissão inválida", 500
    
    return render_template('CadastroColetor.html')