from flask import  Flask, Blueprint, render_template, request, redirect, url_for, flash, make_response
from models.models import Vendedor, User
from db_config import db

auth_route = Blueprint('Auth', __name__)

@auth_route.route('/')
def auth_page():

    return render_template('Login.html')

@auth_route.route('/', methods=['POST'])
def create_account():
    data = request.get_json()

    username = data.get('username')
    senha = data.get('password')
    nome = data.get('name')
    serial = data.get('serial')

    # Verificar campos obrigatórios
    if not username or not senha or not nome or not serial:
        return {"message": "Todos os campos são obrigatórios!"}, 400

    # Verificar se usuário já existe
    existing_user = Vendedor.query.filter_by(username=username).first()
    if existing_user:
        return {"message": "Nome de usuário já está em uso."}, 409

    nova_conta = Vendedor(
        nome=nome,
        username=username,
        senha=senha,
        serial=serial
    )

    db.session.add(nova_conta)
    db.session.commit()

    return {"message": "Conta registrada com sucesso!"}, 201

@auth_route.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    username = data.get('username')
    senha = data.get('password')

    if not username or not senha:
        return {"message": "Usuário e senha são obrigatórios!"}, 400

    user = User.query.filter_by(username=username).first()

    if not user or user.senha != senha:
        return {"message": "Credenciais inválidas!"}, 401

    # Credenciais válidas — define os cookies e redireciona
    response = make_response(redirect(url_for('Home.home')))
    response.set_cookie('username', username)
    response.set_cookie('senha', senha)

    return response

@auth_route.route('/validate', methods=['POST'])
def validate_credentials():
    data = request.get_json()

    if not data:
        return {
            "Validate": False,
            "message": "Dados JSON ausentes ou inválidos!"
        }, 400

    deviceId = str(data.get('deviceId', '')).strip()
    username = str(data.get('username', '')).strip()
    senha = str(data.get('password', '')).strip()

    if not username or not senha:
        return {
            "Validate": False,
            "message": "Usuário e senha são obrigatórios!"
        }, 400

    user = Vendedor.query.filter_by(username=username).first()

    if not user:
        return {
            "Validate": False,
            "message": "Usuário não encontrado!"
        }, 401

    if user.senha != senha:
        return {
            "Validate": False,
            "message": "Senha incorreta!"
        }, 401

    if user.serial.strip() != deviceId:
        return {
            "Validate": False,
            "message": "Device não autorizado!"
        }, 403

    return {
        "message": "success!",
        "Validate": True
    }, 200