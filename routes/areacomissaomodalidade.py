from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from util.checkCreds import checkCreds
from models.models import Area, Modalidade, ComissaoArea
from db_config import db

area_comissao_route = Blueprint('AreaComissaoModalidade', __name__)

@area_comissao_route.route('/')
def area_comissao_page():

    check_result = checkCreds()

    if not check_result['success']:
        return check_result['message'], 401  
    
    user = check_result['user']

    try:
        if int(user.acesso_area_comissao_modalidade) != 1:
            return "Usuário não autorizado", 403
    except (AttributeError, ValueError):
        return "Configuração de permissão inválida", 500
    
    areas = Area.query.all()
    modalidades=Modalidade.query.all()
    comissao_area = ComissaoArea.query.all()
    return render_template('AreaComissaoModalidade.html', areas=areas, modalidades=modalidades, comissao_area = comissao_area)

@area_comissao_route.route('/salvar', methods=['POST'])
def salvar_area_comissao():
    data = request.get_json()
    linhas = data.get('dados', [])

    if not linhas:
        return jsonify({'success': False, 'message': 'Nenhum dado enviado'}), 400

    try:
        for item in linhas:
            area = item.get('area')
            modalidade = item.get('modalidade')
            comissao = item.get('comissao')
            ativar = item.get('ativar')

            if not area or not modalidade:
                continue

            existente = ComissaoArea.query.filter_by(area=area, modalidade=modalidade).first()

            if existente:
                # Atualiza se já existir
                existente.comissao = comissao
                existente.ativar = ativar
            else:
                # Cria novo registro
                novo = ComissaoArea(
                    area=area,
                    modalidade=modalidade,
                    comissao=comissao,
                    ativar=ativar
                )
                db.session.add(novo)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Comissões salvas com sucesso!'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@area_comissao_route.route('/editar', methods=['POST'])
def editar_comissao_area():
    try:
        data = request.get_json()
        area = data.get("area")
        modalidade = data.get("modalidade")

        # Buscar o registro correspondente
        registro = ComissaoArea.query.filter_by(area=area, modalidade=modalidade).first()
        if not registro:
            return jsonify({"success": False, "message": "Registro não encontrado"}), 404

        # Atualizar campos
        registro.comissao = data.get("comissao")
        registro.ativar = data.get("ativar")

        db.session.commit()
        return jsonify({"success": True, "message": "Registro atualizado com sucesso!"})
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400
    
@area_comissao_route.route('/excluir', methods=['POST'])
def excluir_comissao_area():
    try:
        data = request.get_json()
        area = data.get("area")
        modalidade = data.get("modalidade")

        if not area or not modalidade:
            return jsonify({"success": False, "message": "Área ou modalidade ausente"}), 400

        registro = ComissaoArea.query.filter_by(area=area, modalidade=modalidade).first()
        if not registro:
            return jsonify({"success": False, "message": "Registro não encontrado"}), 404

        db.session.delete(registro)
        db.session.commit()
        return jsonify({"success": True, "message": "Registro excluído com sucesso!"})
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400