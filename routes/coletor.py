from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from util.checkCreds import checkCreds
from db_config import db

coletor_route = Blueprint('Coletor', __name__)

@coletor_route.route('/')
def coletor_page():

    check_creds = checkCreds()
    if check_creds['success'] == True:
        return render_template('CadastroColetor.html')
    else:
        return check_creds['message']