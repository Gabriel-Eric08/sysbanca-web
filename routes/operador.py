from flask import Blueprint, render_template, request, redirect, url_for
from models.models import Operador
from util.checkCreds import checkCreds
from db_config import db

operadores_route = Blueprint('Operadores', __name__)

@operadores_route.route('/', methods=['GET'])
def operadores_page():
    check_result = checkCreds()
    

    if not check_result['success']:
        return check_result['message'], 401
    
    user = check_result['user']
    
    try:
        if int(user.acesso_modalidade) != 1:
            return "Usuário não autorizado", 403
    except (AttributeError, ValueError):
        return "Configuração de permissão inválida", 500
    
    operadores = Operador.query.all()
    return render_template('cadastroOperador.html', operadores=operadores)

@operadores_route.route('/', methods=['POST'])
def novo_operador():
    nomes = request.form.getlist('nome[]')
    regioes = request.form.getlist('regiao[]')
    ativos = request.form.getlist('ativo[]')
    areas = request.form.getlist('area[]')
    logins = request.form.getlist('login[]')
    senhas = request.form.getlist('senha[]')
    comissoes = request.form.getlist('comissao[]')
    cancelar_poules = request.form.getlist('cancelar_poule[]')
    exibe_comissoes = request.form.getlist('exibe_comissao[]')
    limites_venda = request.form.getlist('limite_venda[]')
    premiacoes = request.form.getlist('premiacao[]')
    tipos_limite = request.form.getlist('tipo_limite[]')
    grades = request.form.getlist('grade[]')
    testes = request.form.getlist('teste[]')
    comissoes_retidas = request.form.getlist('comissao_retida[]')
    seriais_maquina = request.form.getlist('serial_maquina[]')

    for i in range(len(nomes)):
        nome = nomes[i]
        regiao = regioes[i]
        ativo = ativos[i]
        area = areas[i]
        login = logins[i]
        senha = senhas[i]
        comissao = comissoes[i]
        cancelar_poule = cancelar_poules[i]
        exibe_comissao = exibe_comissoes[i]
        limite_venda = limites_venda[i]
        premiacao = premiacoes[i] if i < len(premiacoes) else ''
        tipo_limite = tipos_limite[i]
        grade = grades[i]
        teste = testes[i]
        comissao_retida = comissoes_retidas[i]
        serial_maquina = seriais_maquina[i]

        if not all([nome, regiao, ativo, area, login, senha]):
            # pula se dados essenciais estão faltando
            continue

        # Checa se já existe operador com mesmo login
        existente = Operador.query.filter_by(login=login).first()
        if existente:
            continue  # já existe, passa para o próximo

        try:
            comissao_val = int(comissao) if comissao else 0
            limite_venda_val = int(limite_venda) if limite_venda else 0
        except ValueError:
            continue  # ignora se conversão falhar

        novo = Operador(
            nome=nome,
            regiao=regiao,
            ativo=ativo,
            area=area,
            login=login,
            senha=senha,
            comissao=comissao_val,
            cancelar_poule=cancelar_poule or '',
            exibe_comissao=exibe_comissao or '',
            limite_venda=limite_venda_val,
            premiacao=premiacao or '',
            tipo_limite=tipo_limite or '',
            grade=grade or '',
            teste=teste or '',
            comissao_retida=comissao_retida or '',
            serial_maquina=serial_maquina or ''
        )
        db.session.add(novo)

    db.session.commit()

    return redirect(url_for('Operadores.operadores_page'))