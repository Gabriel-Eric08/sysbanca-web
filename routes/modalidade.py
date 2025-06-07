from flask import  Flask, Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.models import Modalidade
from util.checkCreds import checkCreds
from db_config import db

modalidade_route = Blueprint('Modalidade', __name__)

@modalidade_route.route('/')
def modalidade_page():
    check_creds = checkCreds()
    if check_creds['success'] == True:
        modalidades = Modalidade.query.all()
        return render_template('cadastroModalidade.html', modalidades=modalidades)
    else:
        return check_creds['message']

@modalidade_route.route('/', methods=['POST'])
def adicionar_modalidades():
    modalidades = request.form.getlist('modalidade[]')
    cotacoes = request.form.getlist('cotacao[]')
    unidades = request.form.getlist('unidade[]')
    limites_aposta = request.form.getlist('LimitePorAposta[]')
    limites_jogo = request.form.getlist('LimitePorJogo[]')
    ativacoes = request.form.getlist('AtivarAreaCotacao[]')

    for i in range(len(modalidades)):
        # Verifica se a modalidade já existe no banco
        existente = Modalidade.query.filter_by(modalidade=modalidades[i]).first()
        if existente:
            # Se já existe, pula para próxima
            continue

        nova = Modalidade(
            modalidade=modalidades[i],
            cotacao=cotacoes[i],
            unidade=unidades[i],
            limite_por_aposta=limites_aposta[i],
            limite_por_jogo=limites_jogo[i],
            ativar_area=ativacoes[i]
        )
        db.session.add(nova)

    db.session.commit()

    return redirect(url_for('Modalidade.modalidade_page'))

@modalidade_route.route('/json', methods=['GET'])

def json_modalidades():
    modalidades = Modalidade.query.all()

    resultado = []
    for m in modalidades:
        linha = [
            m.modalidade,
            m.cotacao,
            m.unidade,
            m.limite_por_aposta,
            m.limite_por_jogo,
            m.ativar_area
        ]
        resultado.append(linha)

    return jsonify(resultado)


@modalidade_route.route('/', methods=['DELETE'])
def excluir_modalidades():
    try:
        dados = request.get_json()
        nome_modalidade = dados.get('Modalidade')

        if not nome_modalidade:
            return jsonify({'success': False, 'message': 'Nome da modalidade não fornecido'}), 400

        modalidade = Modalidade.query.filter_by(modalidade=nome_modalidade).first()

        if not modalidade:
            return jsonify({'success': False, 'message': 'Modalidade não encontrada'}), 404

        db.session.delete(modalidade)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Modalidade excluída com sucesso'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao excluir: {str(e)}'}), 500