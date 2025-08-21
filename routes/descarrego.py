from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models.models import Descarrego, Extracao # Importe o modelo Extracao
from util.checkCreds import checkCreds
from db_config import db
from datetime import datetime

descarrego_route = Blueprint('Descarrego', __name__)

@descarrego_route.route('/')
def descarrego_page():
    check_result = checkCreds()

    if not check_result['success']:
        return check_result['message'], 401

    user = check_result['user']

    try:
        if int(user.acesso_descarrego) != 1:
            return "Usuário não autorizado", 403
    except (AttributeError, ValueError):
        return "Configuração de permissão inválida", 500

    descarregos = Descarrego.query.order_by(Descarrego.data.desc()).all()
    extracoes = Extracao.query.order_by(Extracao.extracao).all() # Consulta todas as extrações

    # Formatar campo extracao para "DD-MM-YYYY HH:MM:SS"
    for d in descarregos:
        if isinstance(d.extracao, str):
            try:
                dt = datetime.strptime(d.extracao, "%Y-%m-%d")
                d.extracao = dt.strftime("%d-%m-%Y")
            except ValueError:
               pass  # já está formatado ou não é uma data válida

    # Passe a lista de extrações para o template
    return render_template('descarrego.html', descarregos=descarregos, extracoes=extracoes)