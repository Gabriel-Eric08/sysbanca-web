# usuario_route.py (versão atualizada)
from flask import Blueprint, request, jsonify
from models.models import Usuario, Relatorio
from db_config import db
from datetime import datetime
from util.checkCreds import checkCreds

usuario_route = Blueprint('Usuarios', __name__, url_prefix='/usuarios')

@usuario_route.route('/save', methods=['POST'])
def save_usuario():
    # Verifica as credenciais do usuário logado antes de permitir a operação
    check_result = checkCreds()
    if not check_result['success']:
        return check_result['message'], 401

    usuario_logado = check_result['user']

    # Opcional: verifique se o usuário logado tem permissão para adicionar outros usuários
    if int(usuario_logado.acesso_administrador) != 1:
        return "Usuário não autorizado a criar novos usuários", 403

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Dados inválidos ou ausentes."}), 400

    cpf = data.get('cpf')
    email = data.get('email')
    celular = data.get('celular')
    senha = data.get('senha')

    # Verificação de campos obrigatórios
    if not all([cpf, email, senha]):
        return jsonify({"success": False, "message": "Campos 'cpf', 'email' e 'senha' são obrigatórios."}), 400

    # Verifica se o CPF ou e-mail já existem
    existente_cpf = Usuario.query.filter_by(cpf=cpf).first()
    existente_email = Usuario.query.filter_by(email=email).first()
    
    if existente_cpf:
        return jsonify({"success": False, "message": "CPF já cadastrado."}), 409
    
    if existente_email:
        return jsonify({"success": False, "message": "E-mail já cadastrado."}), 409

    try:
        novo_usuario = Usuario(
            cpf=cpf,
            email=email,
            celular=celular,
            senha=senha  # Lembre-se de criptografar a senha na prática
        )

        db.session.add(novo_usuario)
        db.session.flush()

        # Cria o registro no relatório de ações
        relatorio = Relatorio(
            usuario=usuario_logado.username,
            tabela="tb_usuario",
            acao="Inserção (API)",
            id_linha=novo_usuario.id,
            linha=str(novo_usuario.__dict__),
            data=datetime.now().date(),
            horario=datetime.now().time()
        )
        db.session.add(relatorio)

        db.session.commit()

        return jsonify({
            "success": True, 
            "message": "Usuário criado com sucesso!", 
            "id": novo_usuario.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro ao salvar usuário: {str(e)}"}), 500