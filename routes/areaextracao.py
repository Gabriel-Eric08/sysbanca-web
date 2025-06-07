from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from util.checkCreds import checkCreds
from db_config import db

area_extracao_route = Blueprint('AreaExtracao', __name__)

@area_extracao_route.route('/')
def area_extracao_page():

    check_creds = checkCreds()
    if check_creds['success'] == True:
        return render_template('CadastroAreaExtracao.html')
    else:
        return check_creds['message']