from flask import request
from models.models import User
from werkzeug.security import check_password_hash

def checkCreds():
    # Obtendo o username e senha dos cookies
    username = request.cookies.get('username')
    senha = request.cookies.get('senha')

    # Verificar se os cookies contêm os dados necessários
    if not username or not senha:
        return {"success": False, "message": "Usuário ou senha não encontrados nos cookies."}

    # Verificar se o usuário existe no banco de dados
    existing_user = User.query.filter_by(username=username).first()

    if not existing_user:
        return {"success": False, "message": "Usuário não encontrado."}

    # Verificar se a senha está correta
    if not existing_user.senha:
        return {"success": False, "message": "Senha incorreta."}

    # Caso tudo esteja correto
    return {"success": True, "message": "Login bem-sucedido!"}
