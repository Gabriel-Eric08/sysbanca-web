from flask import request
from models.models import User, Vendedor

def checkCreds(username=None, senha=None):
    """
    Função para verificar credenciais de usuário ou vendedor.
    Recebe username e senha como argumentos.
    """
    # Se username e senha não foram passados, tenta pegá-los dos cookies
    if username is None and senha is None:
        username = request.cookies.get("username")
        senha = request.cookies.get("senha")

    # Adicionando prints para verificar os dados que chegam à função
    print(f"Dentro de checkCreds - Username recebido: '{username}', Senha recebida: '{senha}'")

    if not username or not senha:
        print("Credenciais ausentes.")
        return {"success": False, "message": "Usuário ou senha não encontrados."}

    # Tentando autenticar como Vendedor
    print(f"Buscando por vendedor com username: {username}")
    vendedor = Vendedor.query.filter_by(username=username).first()
    
    if vendedor:
        print(f"Vendedor encontrado. Senha do banco: '{vendedor.senha}'")
        
        if vendedor.senha == senha:
            print("Sucesso: Senhas de vendedor correspondem.")
            return {
                "success": True, 
                "message": "Login de vendedor bem-sucedido!",
                "is_vendedor": True
            }
        else:
            print("Falha: Senha de vendedor incorreta.")
            return {"success": False, "message": "Senha incorreta."}
    else:
        print(f"Nenhum vendedor encontrado com o username: {username}")
        
    # Tentando autenticar como usuário comum
    print(f"Buscando por usuário comum com username: {username}")
    user = User.query.filter_by(username=username).first()
    
    if user:
        print(f"Usuário comum encontrado. Senha do banco: '{user.senha}'")
        
        if user.senha == senha:
            print("Sucesso: Senhas de usuário comum correspondem.")
            return {
                "success": True, 
                "message": "Login de usuário bem-sucedido!",
                "is_vendedor": False
            }
        else:
            print("Falha: Senha de usuário comum incorreta.")
            return {"success": False, "message": "Senha incorreta."}
    else:
        print(f"Nenhum usuário comum encontrado com o username: {username}")

    # Se nenhum dos dois for encontrado ou a senha estiver errada
    print("Falha geral: Credenciais inválidas.")
    return {"success": False, "message": "Credenciais inválidas."}