from flask import Blueprint, render_template, jsonify, request
from models.models import User
from db_config import db
from util.checkCreds import checkCreds

admin_route = Blueprint('Admin', __name__)


@admin_route.route('/1')
def admin_page1():
    return "TESTANDO 1"

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

        if user.acesso_usuario: permissoes.append("usuario")
        if user.acesso_modalidade: permissoes.append("modalidade")
        if user.acesso_regiao: permissoes.append("regiao")
        if user.acesso_extracao: permissoes.append("extracao")
        if user.acesso_area_extracao: permissoes.append("area extracao")
        if user.acesso_area_cotacao: permissoes.append("area cotacao")
        if user.acesso_area_comissao_modalidade: permissoes.append("area comissao modalidade")
        if user.acesso_coletor: permissoes.append("coletor")
        if user.acesso_vendedor: permissoes.append("vendedor")
        if user.acesso_vendas_por_periodo_operador: permissoes.append("vendas por periodo operador")
        if user.acesso_relatorio_geral_de_vendas: permissoes.append("relatorio geral de vendas")
        if user.acesso_numeros_cotados: permissoes.append("numeros cotados")
        if user.acesso_programacao_extracao: permissoes.append("programacao extracao")
        if user.acesso_descarrego: permissoes.append("descarrego")
        if user.acesso_cancelamento_fora_do_horario: permissoes.append("cancelamento fora do horario")
        if user.acesso_administracao: permissoes.append("administracao")
        if user.acesso_area: permissoes.append("area")

        usuarios_permissoes.append({
            "username": user.username,
            "senha": user.senha,
            "permissoes": ", ".join(permissoes),
            "ativo": user.ativo == 1
        })

    return render_template('CadastroUsuarios.html', usuarios_permissoes=usuarios_permissoes)


@admin_route.route('/', methods=['POST'])
def cadastrar_usuario():
    try:
        data = request.get_json()
        usuarios = data if isinstance(data, list) else [data]

        salvos = []
        ignorados = []

        for usuario_data in usuarios:
            username = usuario_data.get("Username")
            password = usuario_data.get("Password")
            permissoes_texto = usuario_data.get("Permissões", "")
            ativo = usuario_data.get("Ativo", False)

            if not username or not password:
                ignorados.append(username or "(sem username)")
                continue

            permissoes_array = [p.strip().lower() for p in permissoes_texto.split(",") if p.strip()]
            user_existente = User.query.filter_by(username=username).first()

            campos = {
                'acesso_usuario': 'usuario',
                'acesso_modalidade': 'modalidade',
                'acesso_regiao': 'regiao',
                'acesso_extracao': 'extracao',
                'acesso_area_extracao': 'area extracao',
                'acesso_area_cotacao': 'area cotacao',
                'acesso_area_comissao_modalidade': 'area comissao modalidade',
                'acesso_coletor': 'coletor',
                'acesso_vendedor': 'vendedor',
                'acesso_vendas_por_periodo_operador': 'vendas por periodo operador',
                'acesso_relatorio_geral_de_vendas': 'relatorio geral de vendas',
                'acesso_numeros_cotados': 'numeros cotados',
                'acesso_programacao_extracao': 'programacao extracao',
                'acesso_descarrego': 'descarrego',
                'acesso_cancelamento_fora_do_horario': 'cancelamento fora do horario',
                'acesso_administracao': 'administracao',
                'acesso_area': 'area'
            }

            if user_existente:
                user_existente.senha = password
                for attr, chave in campos.items():
                    setattr(user_existente, attr, 1 if chave in permissoes_array else 0)
                user_existente.ativo = 1 if ativo else 0
                salvos.append(username)
            else:
                novo_user = User(
                    username=username,
                    senha=password,
                    ativo=1 if ativo else 0,
                    **{ attr: 1 if chave in permissoes_array else 0 for attr, chave in campos.items() }
                )
                db.session.add(novo_user)
                salvos.append(username)

        db.session.commit()

        return jsonify({
            "success": True,
            "salvos": salvos,
            "ignorados": ignorados,
            "message": f"{len(salvos)} usuários salvos, {len(ignorados)} ignorados."
        }), 200

    except Exception as e:
        db.session.rollback()
@admin_route.route('/<username>', methods=['DELETE'])
def deletar_usuario(username):
    try:
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"success": False, "message": "Usuário não encontrado."}), 404

        db.session.delete(user)
        db.session.commit()
        return jsonify({"success": True, "message": f"Usuário {username} excluído."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400