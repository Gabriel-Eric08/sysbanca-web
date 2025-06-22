from flask import Blueprint, render_template, jsonify, request
from models.models import User
from db_config import db
from util.checkCreds import checkCreds

admin_route = Blueprint('Admin', __name__)

@admin_route.route('/')
def admin_page():

    check_result = checkCreds()
    

    if not check_result['success']:
        return check_result['message'], 401
    
    user = check_result['user']
    
    try:
        if int(user.acesso_usuario) != 1:
            return "Usuário não autorizado", 403
    except (AttributeError, ValueError):
        return "Configuração de permissão inválida", 500

    usuarios = User.query.all()

    usuarios_permissoes = []

    for user in usuarios:
        permissoes = []

        if user.acesso_usuario == 1:
            permissoes.append(" Usuário")
        if user.acesso_modalidade == 1:
            permissoes.append(" Modalidade")
        if user.acesso_regiao == 1:
            permissoes.append(" Regiao")
        if user.acesso_extracao == 1:
            permissoes.append(" Extracao")
        if user.acesso_area_extracao == 1:
            permissoes.append(" Area extracao")
        if user.acesso_area_cotacao == 1:
            permissoes.append(" Area cotacao")
        if user.acesso_area_comissao_modalidade == 1:
            permissoes.append(" Area comissao modalidade")
        if user.acesso_coletor == 1:
            permissoes.append(" Coletor")
        if user.acesso_vendedor == 1:
            permissoes.append(" Vendedor")
        if user.acesso_vendas_por_periodo_operador == 1:
            permissoes.append(" Vendas por periodo operador")
        if user.acesso_relatorio_geral_de_vendas == 1:
            permissoes.append(" Relatorio geral de vendas")
        if user.acesso_numeros_cotados == 1:
            permissoes.append(" Numeros cotados")
        if user.acesso_programacao_extracao == 1:
            permissoes.append(" Programacao extracao")
        if user.acesso_descarrego == 1:
            permissoes.append(" Descarrego")
        if user.acesso_cancelamento_fora_do_horario == 1:
            permissoes.append(" Cancelamento fora do horario")
        if user.acesso_administracao == 1:
            permissoes.append(" Administracao")

        permissoes_str = ",".join(permissoes)  # Junta com vírgula sem espaço

        usuarios_permissoes.append({
            "username": user.username,
            "senha": user.senha,
            "permissoes": permissoes_str,
            "ativo": getattr(user, "ativo", False)  # se tiver campo ativo
        })

    return render_template('CadastroUsuarios.html', usuarios_permissoes=usuarios_permissoes)


@admin_route.route('/', methods=['POST'])
def cadastrar_usuario():
    try:
        data = request.get_json()

        # Suporta enviar um único usuário ou uma lista de usuários
        usuarios = data if isinstance(data, list) else [data]

        salvos = []
        ignorados = []

        for usuario_data in usuarios:
            username = usuario_data.get("Username")
            password = usuario_data.get("Password")
            permissoes_texto = usuario_data.get("Permissões", "")
            ativo = usuario_data.get("Ativo", False)

            if not username or not password:
                # Ignora entrada inválida
                continue

            # Verifica se usuário já existe
            if User.query.filter_by(username=username).first():
                ignorados.append(username)
                continue

            permissoes_array = [p.strip().lower() for p in permissoes_texto.split(",") if p.strip()]

            novo_user = User(
                username=username,
                senha=password,
                acesso_usuario=1 if 'usuario' in permissoes_array else 0,
                acesso_modalidade=1 if 'modalidade' in permissoes_array else 0,
                acesso_regiao=1 if 'regiao' in permissoes_array else 0,
                acesso_extracao=1 if 'extracao' in permissoes_array else 0,
                acesso_area_extracao=1 if 'area extracao' in permissoes_array else 0,
                acesso_area_cotacao=1 if 'area cotacao' in permissoes_array else 0,
                acesso_area_comissao_modalidade=1 if 'area comissao modalidade' in permissoes_array else 0,
                acesso_coletor=1 if 'coletor' in permissoes_array else 0,
                acesso_vendedor=1 if 'vendedor' in permissoes_array else 0,
                acesso_vendas_por_periodo_operador=1 if 'vendas por periodo operador' in permissoes_array else 0,
                acesso_relatorio_geral_de_vendas=1 if 'relatorio geral de vendas' in permissoes_array else 0,
                acesso_numeros_cotados=1 if 'numeros cotados' in permissoes_array else 0,
                acesso_programacao_extracao=1 if 'programacao extracao' in permissoes_array else 0,
                acesso_descarrego=1 if 'descarrego' in permissoes_array else 0,
                acesso_cancelamento_fora_do_horario=1 if 'cancelamento fora do horario' in permissoes_array else 0,
                acesso_administracao=1 if 'administracao' in permissoes_array else 0,
                acesso_area=1 if 'area' in permissoes_array else 0,  # Nova permissão
                ativo=1 if ativo else 0
            )

            db.session.add(novo_user)
            salvos.append(username)

        db.session.commit()

        return jsonify({
            "success": True,
            "salvos": salvos,
            "ignorados": ignorados,
            "message": f"{len(salvos)} usuários cadastrados, {len(ignorados)} ignorados (já existentes)."
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400
