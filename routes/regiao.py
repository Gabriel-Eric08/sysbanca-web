from flask import Blueprint, render_template, request, jsonify
from models.models import Regiao
from util.checkCreds import checkCreds
from db_config import db

regiao_route = Blueprint('Regiao', __name__)

@regiao_route.route('/', methods=['GET'])
def regiao_page():

    check_creds = checkCreds()
    if check_creds['success'] == True:
        regioes = Regiao.query.all()
        return render_template('cadastroRegiao.html', regioes=regioes)
    else:
        return check_creds['message']

@regiao_route.route('/', methods=['POST'])
def adicionar_regiao():
    data = request.get_json()
    novas_regioes = data.get('regioes', [])

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
            inseridas += 1

    if inseridas > 0:
        db.session.commit()

    return jsonify({'message': f'{inseridas} região(ões) inserida(s) com sucesso!'})

@regiao_route.route('/', methods=['DELETE'])
def excluir_regiao():
    data = request.get_json()
    regiao_nome = data.get('Regiao')

    if not regiao_nome:
        return jsonify({'message': 'Campo "Regiao" é obrigatório.'}), 400

    try:
        regiao = Regiao.query.filter_by(regiao=regiao_nome).first()
        if not regiao:
            return jsonify({'message': 'Região não encontrada.'}), 404

        db.session.delete(regiao)
        db.session.commit()

        return jsonify({'message': f'Região "{regiao_nome}" excluída com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao excluir: {str(e)}'}), 500