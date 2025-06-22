from flask import Blueprint, render_template, request, jsonify
from db_config import db
from models.models import Area, Relatorio, Vendedor
from datetime import datetime
from util.checkCreds import checkCreds

area_route = Blueprint('Area', __name__)

# GET - Página de cadastro
@area_route.route('/', methods=['GET'])
def area_page():

    check_result = checkCreds()

    if not check_result['success']:
        return check_result['message'], 401  
    
    user = check_result['user']

    try:
        if int(user.acesso_area) != 1:
            return "Usuário não autorizado", 403
    except (AttributeError, ValueError):
        return "Configuração de permissão inválida", 500

    areas = Area.query.order_by(Area.regiao_area).all()
    return render_template('CadastroArea.html', areas=areas)

# POST - Salvar várias áreas
@area_route.route('/', methods=['POST'])
def salvar_area():
    dados = request.get_json()
    if not dados:
        return jsonify({'message': 'Nenhum dado recebido.', 'success': False}), 400

    usuario = request.cookies.get('username', 'Desconhecido')
    areas_adicionadas = 0

    for area in dados:
        regiao_area = area.get('regiao_area', '').strip()
        desc_area = area.get('desc_area', '').strip()
        ativar_area = area.get('ativar_area', False)

        # Verifica se a área já existe com base no nome (regiao_area)
        area_existente = Area.query.filter_by(regiao_area=regiao_area).first()
        if area_existente:
            continue  # Pula se já existe

        nova_area = Area(
            regiao_area=regiao_area,
            desc_area=desc_area,
            ativar_area=ativar_area
        )
        db.session.add(nova_area)
        db.session.flush()

        relatorio = Relatorio(
            usuario=usuario,
            tabela="tb_Area",
            acao="Inserção",
            id_linha=nova_area.id,
            linha=f'{{"regiao_area":"{regiao_area}", "desc_area":"{desc_area}", "ativar_area":"{ativar_area}"}}',
            data=datetime.now().date(),
            horario=datetime.now().time()
        )
        db.session.add(relatorio)
        areas_adicionadas += 1

    if areas_adicionadas == 0:
        return jsonify({'message': 'Nenhuma nova área foi adicionada. Todas já existem.', 'success': False}), 200

    db.session.commit()
    return jsonify({'message': f'{areas_adicionadas} área(s) salvas com sucesso!', 'success': True}), 201


# DELETE - Excluir área por ID
@area_route.route('/', methods=['DELETE'])
def excluir_area():
    dados = request.get_json()
    area_id = dados.get('id')

    if not area_id:
        return jsonify({'message': 'ID não fornecido.', 'success': False}), 400

    area = Area.query.get(area_id)
    if not area:
        return jsonify({'message': 'Área não encontrada.', 'success': False}), 404

    usuario = request.cookies.get('username', 'Desconhecido')

    relatorio = Relatorio(
        usuario=usuario,
        tabela="tb_Area",
        acao="Exclusão",
        id_linha=area.id,
        linha=f'{{"regiao_area":"{area.regiao_area}", "desc_area":"{area.desc_area}", "ativar_area":"{area.ativar_area}"}}',
        data=datetime.now().date(),
        horario=datetime.now().time()
    )
    db.session.add(relatorio)

    db.session.delete(area)
    db.session.commit()
    return jsonify({'message': 'Área excluída com sucesso!', 'success': True}), 200

# GET - Listar todas áreas como JSON
@area_route.route('/json', methods=['GET'])
def listar_areas_json():
    areas = Area.query.all()
    lista = [{
        'id': a.id,
        'regiao_area': a.regiao_area,
        'desc_area': a.desc_area,
        'ativar_area': a.ativar_area
    } for a in areas]

    return jsonify(lista), 200

@area_route.route('/editar', methods=['PUT'])
def editar_area():
    dados = request.get_json()
    area_id = dados.get('id')
    regiao_area = dados.get('regiao_area', '').strip()
    desc_area = dados.get('desc_area', '').strip()
    ativar_area = dados.get('ativar_area', '').strip().lower() in ['sim', '1', 'true']

    if not area_id:
        return jsonify({'message': 'ID não fornecido.', 'success': False}), 400

    area = Area.query.get(area_id)
    if not area:
        return jsonify({'message': 'Área não encontrada.', 'success': False}), 404

    area.regiao_area = regiao_area
    area.desc_area = desc_area
    area.ativar_area = ativar_area

    usuario = request.cookies.get('username', 'Desconhecido')

    relatorio = Relatorio(
        usuario=usuario,
        tabela="tb_Area",
        acao="Edição",
        id_linha=area.id,
        linha=f'{{"regiao_area":"{regiao_area}", "desc_area":"{desc_area}", "ativar_area":"{ativar_area}"}}',
        data=datetime.now().date(),
        horario=datetime.now().time()
    )
    db.session.add(relatorio)
    db.session.commit()

    return jsonify({'message': 'Área atualizada com sucesso!', 'success': True}), 200

@area_route.route('/<serial>')
def get_vendedor_by_serial(serial):
    vendedor = Vendedor.query.filter_by(serial=serial).first()
    
    if not vendedor:
        return jsonify({"success": False, "message": "Vendedor não encontrado"}), 404
    
    return jsonify({
        "success": True,
        "area": vendedor.area
    }), 200