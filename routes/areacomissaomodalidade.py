from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from util.checkCreds import checkCreds
from db_config import db

area_comissao_route = Blueprint('AreaComissaoModalidade', __name__)

@area_comissao_route.route('/')
def area_comissao_page():

    check_creds = checkCreds()
    if check_creds['success'] == True:
        return render_template('AreaComissaoModalidade.html')
    else:
        return check_creds['message']