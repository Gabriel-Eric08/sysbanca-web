from flask import Blueprint, render_template, jsonify
from util.checkCreds import checkCreds
from datetime import datetime
import pytz

home_route = Blueprint('Home', __name__)

@home_route.route('/')
def home():
    check_creds = checkCreds()
    if check_creds['success'] == True:
        return render_template('principal.html')
    else:
        return check_creds['message']

# Rota que retorna data e hora do Nordeste
@home_route.route('/datetime')
def datetime_ne():
    tz = pytz.timezone("America/Recife")  # Fuso do Nordeste
    agora = datetime.now(tz)
    return jsonify({
        "data": agora.strftime("%d/%m/%Y"),
        "hora": agora.strftime("%H:%M:%S"),
        "timezone": str(tz)
    })
