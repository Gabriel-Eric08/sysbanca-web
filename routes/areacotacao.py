from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash
from models.models import AreaCotacao, Area, Extracao, Modalidade, Relatorio
from util.checkCreds import checkCreds
from db_config import db

area_cotacao_route = Blueprint('AreaCotacao', __name__)

@area_cotacao_route.route('/', methods=['GET'])
def area_cotacao_page():

    check_result = checkCreds()

    if not check_result['success']:
        return check_result['message'], 401  
    
    user = check_result['user']

    try:
        if int(user.acesso_area_cotacao) != 1:
            return "Usuário não autorizado", 403
    except (AttributeError, ValueError):
        return "Configuração de permissão inválida", 500
    
    areasCotacao =AreaCotacao.query.all()
    areas = Area.query.order_by(Area.regiao_area).all()
    modalidades = Modalidade.query.all()
    extracoes = Extracao.query.all()
    return render_template('cadastroAreaCotacao.html', areasCotacao=areasCotacao, areas=areas, modalidades=modalidades, extracoes=extracoes)
        

@area_cotacao_route.route('/', methods=['POST'])
def salvar_extracao():
    check_creds = checkCreds()
    if check_creds['success'] != True:
        return check_creds['message']

    linhas = request.form.get('linhas')
    if not linhas:
        flash("Nenhuma linha enviada.")
        return redirect(url_for('AreaCotacao.area_cotacao_page'))

    import json
    try:
        linhas = json.loads(linhas)
    except Exception:
        flash("Dados enviados inválidos.")
        return redirect(url_for('AreaCotacao.area_cotacao_page'))

    for linha in linhas:
        ativar_area_cotacao = 1 if linha['ativar_area_cotacao'].lower() == 'sim' else 0

        existe = AreaCotacao.query.filter_by(
            area=linha['area'],
            extracao=linha['extracao'],
            modalidade=linha['modalidade'],
            cotacao=int(linha['cotacao']),
            ativar_area_cotacao=ativar_area_cotacao
        ).first()

        if not existe:
            nova_area = AreaCotacao(
                area=linha['area'],
                extracao=linha['extracao'],
                modalidade=linha['modalidade'],
                cotacao=int(linha['cotacao']),
                ativar_area_cotacao=ativar_area_cotacao
            )
            db.session.add(nova_area)   

    db.session.commit()
    return redirect(url_for('AreaCotacao.area_cotacao_page'))

@area_cotacao_route.route('/deletar/<int:id>', methods=['DELETE'])
def excluir_area_cotacao(id):
    check_creds = checkCreds()
    if check_creds['success'] != True:
        return check_creds['message'], 403

    area = AreaCotacao.query.get(id)
    if not area:
        return {'error': 'Registro não encontrado'}, 404

    db.session.delete(area)
    db.session.commit()
    return {'success': True}, 200

@area_cotacao_route.route('/editar/<int:id>', methods=['PUT'])
def editar_area_cotacao(id):
    check_creds = checkCreds()
    if not check_creds['success']:
        return check_creds['message'], 403

    dados = request.get_json()
    if not dados:
        return {'error': 'Dados inválidos ou ausentes'}, 400

    area = AreaCotacao.query.get(id)
    if not area:
        return {'error': 'Registro não encontrado'}, 404

    try:
        area.area = dados['area']
        area.extracao = dados['extracao']
        area.modalidade = dados['modalidade']
        area.cotacao = dados['cotacao']  # Corrigido para float
        area.ativar_area_cotacao = 1 if dados['ativar_area_cotacao'].lower() == 'sim' else 0
        db.session.commit()
        return {'success': True}, 200
    except Exception as e:
        db.session.rollback()
        return {'error': f'Erro ao editar: {str(e)}'}, 500