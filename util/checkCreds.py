from flask import request, session
from models.models import User

def checkCreds():
    # Obtém credenciais dos cookies
    username = request.cookies.get('username')
    senha = request.cookies.get('senha')

    if not username or not senha:
        return {"success": False, "message": "Credenciais não encontradas nos cookies"}

    # Busca usuário no banco de dados
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return {"success": False, "message": "Usuário não encontrado"}
    
    # Verificação de senha (idealmente deveria usar hash)
    if user.senha != senha:
        return {"success": False, "message": "Senha incorreta"}
    
    return {
        "success": True,
        "message": "Autenticado com sucesso",
        "user": user  # Retorna todos os dados do usuário
    }