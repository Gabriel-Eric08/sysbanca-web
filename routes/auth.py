from flask import  Flask, Blueprint, render_template, request, redirect, url_for, flash, make_response
from models.models import Vendedor, User
from db_config import db
import os

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
    senha = data.get('password') # Lembre-se que o campo de senha no modelo é 'senha'

    if not username or not senha:
        return {"message": "Usuário e senha são obrigatórios!"}, 400

    # 1. Tenta autenticar como um Vendedor primeiro
    vendedor = Vendedor.query.filter_by(username=username).first()
    if vendedor and vendedor.senha == senha:
        # Se for um vendedor, define os cookies e redireciona
        response = make_response(redirect(url_for('Home.home')))
        response.set_cookie('username', username)
        response.set_cookie('senha', senha)
        return response

    # 2. Se não for um vendedor, tenta autenticar como um usuário comum
    user = User.query.filter_by(username=username).first()
    if user and user.senha == senha:
        # Se for um usuário comum, define os cookies e redireciona
        response = make_response(redirect(url_for('Home.home')))
        response.set_cookie('username', username)
        response.set_cookie('senha', senha)
        return response

    # Se nenhuma das verificações acima for bem-sucedida, retorna erro 401
    return {"message": "Credenciais inválidas!"}, 401

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
    nome_banca = os.environ.get("NOME_BANCA", "BANCA PADRÃO")
    token = os.environ.get("APP_TOKEN", "token-padrao-do-app")
    return {
        "message": "success!",
        "Validate": True,
        "Nome":user.nome,
        "Comissao":user.comissao,
        "Nome_banca": nome_banca,
        "cancelar_poule": user.cancelar_poule,
        "area": user.area,
        "exibe_premiacao": user.exibe_premiacao,
        "token": token
    }, 200

@auth_route.route('/validate/download', methods=['GET'])
def download():
    # Caminho para o arquivo que você quer que seja baixado
    # Este arquivo precisa estar na pasta 'static' do seu projeto Flask
    caminho_do_arquivo = 'SysApp.apk'
    return render_template('download.html', file_path=caminho_do_arquivo)