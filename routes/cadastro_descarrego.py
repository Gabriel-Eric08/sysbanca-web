from flask import Blueprint, render_template, request, jsonify
from models.models import Modalidade, Extracao, Area, CadastroDescarrego, User
from util.checkCreds import checkCreds
from db_config import db



cadastro_descarrego_route = Blueprint('CadastroDescarrego', __name__)

@cadastro_descarrego_route.route('/')
def cadastro_page():
    check_result = checkCreds()

    if not check_result['success']:
        return check_result['message'], 401

    users_acess = User.query.filter(User.acesso_descarrego == 1).all()

    areas = Area.query.all()
    extracoes = Extracao.query.all()
    modalidades = Modalidade.query.all()
    descarregos = CadastroDescarrego.query.all()

    return render_template('CadastroDescarrego.html',
                           areas=areas,
                           extracoes=extracoes,
                           modalidades=modalidades,
                           descarregos=descarregos,
                           users_acess=users_acess)

@cadastro_descarrego_route.route('/salvar', methods=['POST'])
def salvar_descarrego():
    dados = request.get_json()

    for item in dados:
        area = item.get('area')
        extracao = item.get('extracao')
        modalidade = item.get('modalidade')
        limite = item.get('limite')

        existente = CadastroDescarrego.query.filter_by(
            areas=area,
            extracao=extracao,
            modalidade=modalidade
        ).first()

        if not existente:
            novo = CadastroDescarrego(
                areas=area,
                extracao=extracao,
                modalidade=modalidade,
                limite=float(limite)
            )
            db.session.add(novo)
        else:
            # Atualiza limite se quiser (opcional)
            existente.limite = float(limite)

    db.session.commit()
    return jsonify({"success": True, "message": "Dados salvos com sucesso."})

@cadastro_descarrego_route.route('/excluir', methods=['POST'])
def excluir_descarrego():
    dados = request.get_json()
    area = dados.get('area')
    extracao = dados.get('extracao')
    modalidade = dados.get('modalidade')

    descarrego = CadastroDescarrego.query.filter_by(
        areas=area,
        extracao=extracao,
        modalidade=modalidade
    ).first()

    if descarrego:
        db.session.delete(descarrego)
        db.session.commit()
        return jsonify({"success": True, "message": "Registro excluído com sucesso."})
    else:
        return jsonify({"success": False, "message": "Registro não encontrado."}), 404
