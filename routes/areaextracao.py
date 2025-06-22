from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from util.checkCreds import checkCreds
from models.models import Area, Extracao, AreaExtracao
from db_config import db

area_extracao_route = Blueprint('AreaExtracao', __name__)

@area_extracao_route.route('/')
def area_extracao_page():
    check_result = checkCreds()

    if not check_result['success']:
        return check_result['message'], 401  
    
    user = check_result['user']

    try:
        if int(user.acesso_area_extracao) != 1:
            return "Usuário não autorizado", 403
    except (AttributeError, ValueError):
        return "Configuração de permissão inválida", 500
    
    areas_extracao = AreaExtracao.query.all()
    extracoes = Extracao.query.all()
    areas = Area.query.all()
    return render_template('CadastroAreaExtracao.html', areas=areas, extracoes=extracoes, dados=areas_extracao)

@area_extracao_route.route('/', methods=['POST'])
def salvar_area_extracao():
    try:
        data = request.form
        
        # Processar os dados do formulário
        associacoes = []
        for key in data:
            if key.startswith('associacoes'):
                import re
                m = re.match(r'associacoes\[(\d+)\]\[(\w+)\]', key)
                if m:
                    idx = int(m.group(1))
                    campo = m.group(2)
                    
                    while len(associacoes) <= idx:
                        associacoes.append({})
                    
                    associacoes[idx][campo] = data[key]
        
        # Verificar e salvar no banco de dados
        for assoc in associacoes:
            area = assoc.get('area')
            extracao = assoc.get('extracao')
            
            # Verifica se já existe essa associação
            existe = AreaExtracao.query.filter_by(
                area=area,
                extracao=extracao
            ).first()
            
            if not existe:
                nova_associacao = AreaExtracao(
                    area=area,
                    extracao=extracao,
                    ativar=assoc.get('ativo', 'nao').lower() in ['sim', '1', 'true', 'yes']
                )
                db.session.add(nova_associacao)
        
        db.session.commit()
        return redirect(url_for('AreaExtracao.area_extracao_page'))
    
    except Exception as e:
        db.session.rollback()
        return str(e), 400
    
@area_extracao_route.route('/<int:id>', methods=['DELETE'])
def excluir_area_extracao(id):
    try:
        associacao = AreaExtracao.query.get(id)
        if not associacao:
            return jsonify({"success": False, "message": "Associação não encontrada"}), 404
        
        db.session.delete(associacao)
        db.session.commit()
        return jsonify({"success": True, "message": "Associação excluída com sucesso"})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    
@area_extracao_route.route('/<int:id>', methods=['PUT'])
def editar_area_extracao(id):
    try:
        data = request.get_json()

        area = data.get('area')
        extracao = data.get('extracao')
        ativo = data.get('ativo', 'nao').lower() in ['sim', '1', 'true', 'yes']

        associacao = AreaExtracao.query.get(id)
        if not associacao:
            return jsonify({"success": False, "message": "Associação não encontrada"}), 404

        # Atualiza os campos
        associacao.area = area
        associacao.extracao = extracao
        associacao.ativar = ativo

        db.session.commit()
        return jsonify({"success": True, "message": "Associação atualizada com sucesso"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500