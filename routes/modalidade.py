from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models.models import Modalidade, Relatorio, User
from util.checkCreds import checkCreds
from db_config import db
from datetime import datetime

modalidade_route = Blueprint('Modalidade', __name__)

@modalidade_route.route('/')
def modalidade_page():

    check_result = checkCreds()
    

    if not check_result['success']:
        return check_result['message'], 401
    
    user = check_result['user']
    
    try:
        if int(user.acesso_modalidade) != 1:
            return "Usuário não autorizado", 403
    except (AttributeError, ValueError):
        return "Configuração de permissão inválida", 500

    modalidades = Modalidade.query.all()

    return render_template('cadastroModalidade.html', 
                         modalidades=modalidades)

@modalidade_route.route('/', methods=['POST'])
def adicionar_modalidades():
    modalidades = request.form.getlist('modalidade[]')
    cotacoes = request.form.getlist('cotacao[]')
    unidades = request.form.getlist('unidade[]')
    limites_aposta = request.form.getlist('LimitePorAposta[]')
    ativacoes = request.form.getlist('AtivarAreaCotacao[]')

    usuario = request.cookies.get('username', 'Desconhecido')

    for i in range(len(modalidades)):
        existente = Modalidade.query.filter_by(modalidade=modalidades[i]).first()
        if existente:
            continue

        nova = Modalidade(
            modalidade=modalidades[i],
            cotacao=cotacoes[i],
            unidade=unidades[i],
            limite_por_aposta=limites_aposta[i],
            ativar_area=1 if str(ativacoes[i]).strip().lower() in ['sim', '1'] else 0
        )
        db.session.add(nova)
        db.session.flush()

        relatorio = Relatorio(
            usuario=usuario,
            tabela="tb_Modalidade",
            acao="Inserção",
            id_linha=nova.id,
            linha=str({
                "modalidade": modalidades[i],
                "cotacao": cotacoes[i],
                "unidade": unidades[i],
                "limite_por_aposta": limites_aposta[i],
                "ativar_area": ativacoes[i]
            }),
            data=datetime.now().date(),
            horario=datetime.now().time()
        )
        db.session.add(relatorio)

    db.session.commit()
    return redirect(url_for('Modalidade.modalidade_page'))

@modalidade_route.route('/json', methods=['GET'])
def json_modalidades():
    modalidades = Modalidade.query.filter_by(ativar_area=1).all()
    resultado = []
    for m in modalidades:
        linha = [
            m.modalidade,
            m.cotacao,
            m.unidade,
            m.limite_por_aposta,
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

        usuario = request.cookies.get('username', 'Desconhecido')

        relatorio = Relatorio(
            usuario=usuario,
            tabela="tb_Modalidade",
            acao="Exclusão",
            id_linha=modalidade.id,
            linha=str({
                "modalidade": modalidade.modalidade,
                "cotacao": modalidade.cotacao,
                "unidade": modalidade.unidade,
                "limite_por_aposta": modalidade.limite_por_aposta,
                "ativar_area": modalidade.ativar_area
            }),
            data=datetime.now().date(),
            horario=datetime.now().time()
        )
        db.session.add(relatorio)

        db.session.delete(modalidade)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Modalidade excluída com sucesso'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao excluir: {str(e)}'}), 500

@modalidade_route.route('/editar', methods=['POST'])
def editar_modalidade():
    try:
        data = request.get_json()
        modalidade_nome = data.get("modalidade")

        m = Modalidade.query.filter_by(modalidade=modalidade_nome).first()
        if not m:
            return jsonify({"success": False, "message": "Modalidade não encontrada"}), 404

        m.cotacao = float(data.get("cotacao"))
        m.unidade = int(data.get("unidade"))
        m.limite_por_aposta = int(data.get("limite_por_aposta"))
        m.ativar_area = 1 if str(data.get("ativar_area")).strip().lower() in ['sim', '1'] else 0

        db.session.commit()
        return jsonify({"success": True, "message": "Modalidade atualizada com sucesso!"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro ao editar: {str(e)}"}), 400