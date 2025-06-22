from flask import Blueprint, render_template, request, jsonify
from models.models import Regiao, Relatorio
from util.checkCreds import checkCreds
from db_config import db
from datetime import datetime

regiao_route = Blueprint('Regiao', __name__)

@regiao_route.route('/', methods=['GET'])
def regiao_page():
    check_result = checkCreds()

    if not check_result['success']:
        return check_result['message'], 401  
    
    user = check_result['user']

    try:
        if int(user.acesso_regiao) != 1:
            return "Usuário não autorizado", 403
    except (AttributeError, ValueError):
        return "Configuração de permissão inválida", 500
    
    regioes = Regiao.query.all()
    
    return render_template('cadastroRegiao.html', regioes=regioes)
    

@regiao_route.route('/', methods=['POST'])
def adicionar_regiao():
    data = request.get_json()
    novas_regioes = data.get('regioes', [])
    usuario = request.cookies.get('username', 'Desconhecido')

    inseridas = 0
    for item in novas_regioes:
        regiao_nome = item.get('regiao')
        desc_regiao = item.get('desc_regiao')
        ativo_str = item.get('ativo')
        ativo = True if ativo_str and ativo_str.lower() == 'sim' else False

        existe = Regiao.query.filter_by(regiao=regiao_nome).first()
        if not existe:
            nova_regiao = Regiao(
                regiao=regiao_nome,
                desc_regiao=desc_regiao,
                ativo=ativo
            )
            db.session.add(nova_regiao)
            db.session.flush()  # para pegar o ID antes do commit

            # Relatório de inserção
            relatorio = Relatorio(
                usuario=usuario,
                tabela='tb_Regiao',
                acao='Inserção',
                id_linha=nova_regiao.id,
                linha=str({
                    'regiao': regiao_nome,
                    'desc_regiao': desc_regiao,
                    'ativo': ativo_str
                }),
                data=datetime.now().date(),
                horario=datetime.now().time()
            )
            db.session.add(relatorio)
            inseridas += 1

    if inseridas > 0:
        db.session.commit()

    return jsonify({'message': f'{inseridas} região(ões) inserida(s) com sucesso!'})

@regiao_route.route('/', methods=['DELETE'])
def excluir_regiao():
    data = request.get_json()
    regiao_nome = data.get('Regiao')
    usuario = request.cookies.get('username', 'Desconhecido')

    if not regiao_nome:
        return jsonify({'message': 'Campo "Regiao" é obrigatório.'}), 400

    try:
        regiao = Regiao.query.filter_by(regiao=regiao_nome).first()
        if not regiao:
            return jsonify({'message': 'Região não encontrada.'}), 404

        # Relatório antes da exclusão
        relatorio = Relatorio(
            usuario=usuario,
            tabela='tb_Regiao',
            acao='Exclusão',
            id_linha=regiao.id,
            linha=str({
                'regiao': regiao.regiao,
                'desc_regiao': regiao.desc_regiao,
                'ativo': 'sim' if regiao.ativo else 'não'
            }),
            data=datetime.now().date(),
            horario=datetime.now().time()
        )
        db.session.add(relatorio)

        db.session.delete(regiao)
        db.session.commit()

        return jsonify({'message': f'Região "{regiao_nome}" excluída com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao excluir: {str(e)}'}), 500

@regiao_route.route('/editar', methods=['POST'])
def editar_regiao():
    try:
        data = request.get_json()
        regiao_nome = data.get("regiao")  # Nome da região original usada como chave

        regiao_obj = Regiao.query.filter_by(regiao=regiao_nome).first()
        if not regiao_obj:
            return jsonify({"success": False, "message": "Região não encontrada"}), 404

        # Atualiza os campos
        regiao_obj.desc_regiao = data.get("desc_regiao")
        ativo_str = data.get("ativo")
        regiao_obj.ativo = True if ativo_str and ativo_str.lower() == 'sim' else False

        db.session.commit()
        return jsonify({"success": True, "message": "Região atualizada com sucesso!"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400

