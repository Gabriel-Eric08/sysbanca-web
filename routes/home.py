from flask import Blueprint, render_template, jsonify, request
from util.checkCreds import checkCreds
from datetime import datetime
from models.models import Vendedor, User
import pytz

home_route = Blueprint('Home', __name__)

@home_route.route('/')
def home():
    username = request.cookies.get('username')
    senha = request.cookies.get('senha')

    print(f"Rota 'home' recebendo cookies - Username: {username}, Senha: {senha}")

    # Passa as credenciais para a função de verificação
    check_creds = checkCreds(username, senha)

    if check_creds and check_creds['success']:
        print("Login bem-sucedido na rota 'home'.")
        if check_creds['is_vendedor']:
         return render_template('home_apk.html')
        
        return render_template('principal.html')
    else:
        print("Login falhou na rota 'home'.")
        return check_creds['message']


# Rota que retorna data e hora do Nordeste
@home_route.route('/datetime')
def datetime_ne():
    tz = pytz.timezone("America/Recife")
    agora = datetime.now(tz)
    return jsonify({ "data": agora.strftime("%d/%m/%Y"), "hora": agora.strftime("%H:%M:%S"), "timezone": str(tz)})