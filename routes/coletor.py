from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from util.checkCreds import checkCreds
from models.models import Area, Modalidade, Coletor
from db_config import db

coletor_route = Blueprint('Coletor', __name__)

@coletor_route.route('/')
def coletor_page():
    check_result = checkCreds()

    if not check_result['success']:
        return check_result['message'], 401  
    
    user = check_result['user']

    try:
        if int(user.acesso_coletor) != 1:
            return "Usuário não autorizado", 403
    except (AttributeError, ValueError):
        return "Configuração de permissão inválida", 500
    
    coletores = Coletor.query.all()
    modalidades = Modalidade.query.all()
    areas = Area.query.all()

    # Transformar em lista de dicionários simples:
    areas_json = [{'regiao_area': a.regiao_area} for a in areas]

    return render_template(
        'CadastroColetor.html',
        areas=areas,
        modalidades=modalidades,
        coletores=coletores,
        areas_json=areas_json  # ← adicionar isso
    )

@coletor_route.route('/', methods=['POST'])
def adicionar_coletores():
    nomes = request.form.getlist('nome[]')
    areas = request.form.getlist('area[]')
    logins = request.form.getlist('login[]')
    senhas = request.form.getlist('senha[]')
    ativacoes = request.form.getlist('ativar[]')

    total = len(nomes)

    # Verifica se todas as listas têm o mesmo tamanho
    if not all(len(lst) == total for lst in [areas, logins, senhas, ativacoes]):
        return "Erro: listas com tamanhos diferentes", 400

    for i in range(total):
        # Pula campos vazios
        if not nomes[i] or not areas[i] or not logins[i] or not senhas[i] or not ativacoes[i]:
            continue

        # Verifica se já existe pelo nome
        existente = Coletor.query.filter_by(nome_coletor=nomes[i]).first()
        if existente:
            continue

        novo = Coletor(
            nome_coletor=nomes[i],
            area=areas[i],
            login=logins[i],
            senha=senhas[i],
            ativar_coletor=ativacoes[i]
        )
        db.session.add(novo)

    db.session.commit()
    return redirect(url_for('Coletor.coletor_page'))

@coletor_route.route('/deletar_coletor', methods=['POST'])
def deletar_coletor():
    nome = request.json.get('nome')

    if not nome:
        return jsonify({'success': False, 'message': 'Nome não fornecido'}), 400

    coletor = Coletor.query.filter_by(nome_coletor=nome).first()

    if coletor:
        db.session.delete(coletor)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Coletor excluído com sucesso'})
    else:
        return jsonify({'success': False, 'message': 'Coletor não encontrado'}), 404
    
@coletor_route.route('/editar', methods=['POST'])
def editar_coletor():
    try:
        data = request.get_json()
        nome_original = data.get("nome_original")

        coletor = Coletor.query.filter_by(nome_coletor=nome_original).first()
        if not coletor:
            return jsonify({"success": False, "message": "Coletor não encontrado"}), 404

        coletor.nome_coletor = data.get("nome_coletor")
        coletor.area = data.get("area")
        coletor.login = data.get("login")
        coletor.senha = data.get("senha")
        coletor.ativar_coletor = data.get("ativar_coletor")

        db.session.commit()
        return jsonify({"success": True, "message": "Coletor atualizado com sucesso!"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400