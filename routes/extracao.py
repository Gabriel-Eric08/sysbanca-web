from flask import Flask, Blueprint, render_template, request, redirect, url_for, jsonify
from models.models import Extracao
from util.checkCreds import checkCreds
from db_config import db

extracao_route = Blueprint('Extracao', __name__, url_prefix='/extracao')

@extracao_route.route('/', methods=['GET'])
def extracao_page():
    check_creds = checkCreds()
    if check_creds['success']:
        extracoes = Extracao.query.all()
        return render_template('cadastroExtracao.html', extracoes=extracoes)
    else:
        return check_creds['message']

@extracao_route.route('/', methods=['POST'])
def salvar_extracao():
    extracoes_form = []

    for key in request.form:
        # key exemplo: extracoes[0][extracao]
        if key.startswith('extracoes'):
            import re
            m = re.match(r'extracoes\[(\d+)\]\[(\w+)\]', key)
            if m:
                idx = int(m.group(1))
                campo = m.group(2)

                # Garantir espaço na lista
                while len(extracoes_form) <= idx:
                    extracoes_form.append({})

                extracoes_form[idx][campo] = request.form[key]

    for extr in extracoes_form:
        # Verifica se já existe no banco
        existente = Extracao.query.filter_by(extracao=extr.get('extracao')).first()
        if existente:
            continue  # pula se já existe

        # Converter premiacao para int, se possível
        try:
            premiacao_val = int(extr.get('premiacao', 0))
        except ValueError:
            premiacao_val = 0

        nova_extracao = Extracao(
            extracao=extr.get('extracao'),
            fechamento=extr.get('fechamento'),
            premiacao=premiacao_val,
            dias_extracao=extr.get('dias_semana'),
            ativo=extr.get('ativo').lower() in ['sim', '1', 'true', 'yes']
        )
        db.session.add(nova_extracao)

    db.session.commit()
    return redirect(url_for('Extracao.extracao_page'))

@extracao_route.route('/json', methods=['GET'])
def json_extracoes():
    extracoes = Extracao.query.all()
    resultado = []
    for m in extracoes:
        linha = {
            'id': m.id,
            'extracao': m.extracao,
            'fechamento': m.fechamento.strftime("%H:%M") if m.fechamento else None,
            'premiacao': m.premiacao,
            'dias_extracao': m.dias_extracao,
            'ativo': m.ativo
        }
        resultado.append(linha)
    return jsonify(resultado)

@extracao_route.route('/', methods=['DELETE'])
def excluir_extracao():
    dados = request.get_json()
    extracao_nome = dados.get('extracao')

    if not extracao_nome:
        return jsonify({'message': 'Nome da extração não fornecido.'}), 400

    extracao = Extracao.query.filter_by(extracao=extracao_nome).first()

    if extracao:
        db.session.delete(extracao)
        db.session.commit()
        return jsonify({'message': 'Extração excluída com sucesso!'})
    else:
        return jsonify({'message': 'Extração não encontrada.'}), 404
