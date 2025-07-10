from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from models.models import Extracao, Relatorio, AreaCotacao, Modalidade
from util.checkCreds import checkCreds
from db_config import db
from datetime import datetime

extracao_route = Blueprint('Extracao', __name__, url_prefix='/extracao')

@extracao_route.route('/', methods=['GET'])
def extracao_page():

    check_result = checkCreds()

    if not check_result['success']:
        return check_result['message'], 401  
    
    user = check_result['user']

    try:
        if int(user.acesso_extracao) != 1:
            return "Usuário não autorizado", 403
    except (AttributeError, ValueError):
        return "Configuração de permissão inválida", 500
    
    extracoes = Extracao.query.all()

    return render_template('cadastroExtracao.html', extracoes=extracoes)
 

@extracao_route.route('/', methods=['POST'])
def salvar_extracao():
    extracoes_form = []
    usuario = request.cookies.get('username', 'Desconhecido')

    for key in request.form:
        if key.startswith('extracoes'):
            import re
            m = re.match(r'extracoes\[(\d+)\]\[(\w+)\]', key)
            if m:
                idx = int(m.group(1))
                campo = m.group(2)

                while len(extracoes_form) <= idx:
                    extracoes_form.append({})

                extracoes_form[idx][campo] = request.form[key]

    for extr in extracoes_form:
        existente = Extracao.query.filter_by(extracao=extr.get('extracao')).first()
        if existente:
            continue

        try:
            premiacao_val = int(extr.get('premiacao', 0))
        except ValueError:
            premiacao_val = 0

        ativo_val = extr.get('ativo', '').lower() in ['sim', '1', 'true', 'yes']
        nova_extracao = Extracao(
            extracao=extr.get('extracao'),
            fechamento=extr.get('fechamento'),
            premiacao=premiacao_val,
            dias_extracao=extr.get('dias_semana'),
            ativo=ativo_val
        )
        db.session.add(nova_extracao)
        db.session.flush()  # Garante que nova_extracao.id estará disponível

        # Relatório de inserção
        relatorio = Relatorio(
            usuario=usuario,
            tabela='tb_Extracao',
            acao='Inserção',
            id_linha=nova_extracao.id,
            linha=str({
                'extracao': extr.get('extracao'),
                'fechamento': extr.get('fechamento'),
                'premiacao': premiacao_val,
                'dias_extracao': extr.get('dias_semana'),
                'ativo': 'sim' if ativo_val else 'não'
            }),
            data=datetime.now().date(),
            horario=datetime.now().time()
        )
        db.session.add(relatorio)

    db.session.commit()
    return redirect(url_for('Extracao.extracao_page'))

@extracao_route.route('/json', methods=['GET'])
def json_extracoes():
    extracoes = Extracao.query.filter_by(ativo=1).all()
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
    usuario = request.cookies.get('username', 'Desconhecido')

    if not extracao_nome:
        return jsonify({'message': 'Nome da extração não fornecido.'}), 400

    extracao = Extracao.query.filter_by(extracao=extracao_nome).first()

    if extracao:
        # Relatório antes da exclusão
        relatorio = Relatorio(
            usuario=usuario,
            tabela='tb_Extracao',
            acao='Exclusão',
            id_linha=extracao.id,
            linha=str({
                'extracao': extracao.extracao,
                'fechamento': extracao.fechamento.strftime("%H:%M") if extracao.fechamento else None,
                'premiacao': extracao.premiacao,
                'dias_extracao': extracao.dias_extracao,
                'ativo': 'sim' if extracao.ativo else 'não'
            }),
            data=datetime.now().date(),
            horario=datetime.now().time()
        )
        db.session.add(relatorio)

        db.session.delete(extracao)
        db.session.commit()
        return jsonify({'message': 'Extração excluída com sucesso!'})
    else:
        return jsonify({'message': 'Extração não encontrada.'}), 404

@extracao_route.route('/editar', methods=['POST'])
def editar_extracao():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Dados inválidos"}), 400

        extracao_nome = data.get("extracao")
        if not extracao_nome:
            return jsonify({"success": False, "message": "Nome da extração é obrigatório"}), 400

        # Busca a extração
        extr = Extracao.query.filter_by(extracao=extracao_nome).first()
        if not extr:
            return jsonify({"success": False, "message": "Extração não encontrada"}), 404

        # Atualiza os campos com tratamento de erros
        if 'fechamento' in data:
            try:
                # Corrige o formato do horário (aceita HH:MM ou HH:MM:SS)
                fechamento_str = data['fechamento']
                if len(fechamento_str) == 5:  # Formato HH:MM
                    fechamento_str += ":00"  # Adiciona segundos
                extr.fechamento = datetime.strptime(fechamento_str, "%H:%M:%S").time()
            except ValueError as e:
                return jsonify({
                    "success": False,
                    "message": f"Formato de horário inválido. Use HH:MM (ex: 14:30). Erro: {str(e)}"
                }), 400

        if 'premiacao' in data:
            try:
                extr.premiacao = int(data['premiacao'])
            except ValueError:
                return jsonify({
                    "success": False,
                    "message": "Premiação deve ser um número inteiro"
                }), 400

        if 'dias_extracao' in data:
            extr.dias_extracao = data['dias_extracao']

        if 'ativo' in data:
            extr.ativo = data['ativo'].lower() in ['sim', '1', 'true', 'yes']

        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Extração atualizada com sucesso!",
            "data": {
                "extracao": extr.extracao,
                "fechamento": extr.fechamento.strftime("%H:%M") if extr.fechamento else None,
                "premiacao": extr.premiacao,
                "dias_extracao": extr.dias_extracao,
                "ativo": "sim" if extr.ativo else "não"
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500
    
@extracao_route.route('/cotacao', methods=['POST'])
def extracao_cotacao_premiacao():
    data = request.get_json()

    if not data or 'modalidade' not in data or 'extracao' not in data or 'area' not in data:
        return jsonify({'error': 'Parâmetros "modalidade", "extracao" e "area" são obrigatórios.'}), 400

    # Normalize strings
    modalidade = data['modalidade'].strip().lower()
    extracao = data['extracao'].strip().lower()
    area = data['area'].strip().lower()

    # Busca a extração
    extracao_filter = Extracao.query.filter(db.func.lower(Extracao.extracao) == extracao).first()
    if not extracao_filter:
        return jsonify({'error': 'Extração não encontrada!'}), 404

    # Busca cotação específica
    areacotacao = AreaCotacao.query.filter(
        db.func.lower(AreaCotacao.extracao) == extracao,
        db.func.lower(AreaCotacao.modalidade) == modalidade,
        db.func.lower(AreaCotacao.area) == area
    ).first()

    if areacotacao:
        cotacao = areacotacao.cotacao
    else:
        modalidade_obj = Modalidade.query.filter(db.func.lower(Modalidade.modalidade) == modalidade).first()
        if not modalidade_obj:
            return jsonify({'error': 'Modalidade não encontrada!'}), 404
        cotacao = modalidade_obj.cotacao

    if extracao_filter.ativo != "0":
        resultado = {
            'id': extracao_filter.id,
            'extracao': extracao_filter.extracao,
            'premiacao': extracao_filter.premiacao,
            'cotacao': cotacao
        }
    else:
        resultado = {
            'message': 'Extração não está ativa'
        }

    return jsonify(resultado)
