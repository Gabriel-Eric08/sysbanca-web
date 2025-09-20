from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from models.models import Vendedor, Area, Regiao, Relatorio, CotacaoDefinida
from db_config import db
from util.checkCreds import checkCreds
from datetime import datetime

vendedor_route = Blueprint('Vendedores', __name__)

@vendedor_route.route('/', methods=['GET'])
def vendedores_page():
    check_result = checkCreds()
    if not check_result['success']:
        return check_result['message'], 401

    user = check_result['user']
    try:
        if int(user.acesso_vendedor) != 1:
            return "Usuário não autorizado", 403
    except (AttributeError, ValueError):
        return "Permissão inválida", 500

    regioes = Regiao.query.all()
    areas = Area.query.all()
    vendedores = Vendedor.query.all()
    cotacoes_definidas = CotacaoDefinida.query.all() # Nova consulta para popular o select
    return render_template('cadastroOperador.html', vendedores=vendedores, regioes=regioes, areas=areas, cotacoes_definidas=cotacoes_definidas)


@vendedor_route.route('/', methods=['POST'])
def adicionar_vendedores():
    if request.is_json:
        data = request.get_json()
        nomes = data.get('nome', [])
        regioes = data.get('regiao', [])
        ativos = data.get('ativo', [])
        areas = data.get('area', [])
        logins = data.get('login', [])
        senhas = data.get('senha', [])
        comissoes = data.get('comissao', [])
        cancelar_poules = data.get('cancelar_poule', [])
        exibe_comissoes = data.get('exibe_comissao', [])
        exibe_premiacoes = data.get('exibe_premiacao', [])
        limites_venda = data.get('limite_venda', [])
        tipos_limite = data.get('tipo_limite', [])
        grades = data.get('grade', [])
        testes = data.get('teste', [])
        comissoes_retidas = data.get('comissao_retida', [])
        seriais = data.get('serial_maquina', [])
        cotacoes_definidas = data.get('cotacao_definida', []) # Novo campo
    else:
        nomes = request.form.getlist('nome[]')
        regioes = request.form.getlist('regiao[]')
        ativos = request.form.getlist('ativo[]')
        areas = request.form.getlist('area[]')
        logins = request.form.getlist('login[]')
        senhas = request.form.getlist('senha[]')
        comissoes = request.form.getlist('comissao[]')
        cancelar_poules = request.form.getlist('cancelar_poule[]')
        exibe_comissoes = request.form.getlist('exibe_comissao[]')
        exibe_premiacoes = request.form.getlist('exibe_premiacao[]')
        limites_venda = request.form.getlist('limite_venda[]')
        tipos_limite = request.form.getlist('tipo_limite[]')
        grades = request.form.getlist('grade[]')
        testes = request.form.getlist('teste[]')
        comissoes_retidas = request.form.getlist('comissao_retida[]')
        seriais = request.form.getlist('serial_maquina[]')
        cotacoes_definidas = request.form.getlist('cotacao_definida[]') # Novo campo

    usuario = request.cookies.get('username', 'Desconhecido')

    salvos = 0
    for i in range(len(nomes)):
        if not all([nomes[i], regioes[i], ativos[i], areas[i], logins[i], senhas[i]]):
            continue

        existente = Vendedor.query.filter_by(username=logins[i]).first()
        if existente:
            continue
        
        exibe_comissao_val = 1 if exibe_comissoes[i].lower() == 'sim' else 0 if exibe_comissoes[i].lower() == 'nao' else None
        exibe_premiacao_val = 1 if exibe_premiacoes[i].lower() == 'sim' else 0 if exibe_premiacoes[i].lower() == 'nao' else None

        novo = Vendedor(
            nome=nomes[i],
            regiao=regioes[i],
            ativo=ativos[i],
            area=areas[i],
            username=logins[i],
            senha=senhas[i],
            comissao=comissoes[i] or None,
            cancelar_poule=cancelar_poules[i] or None,
            exibe_comissao=exibe_comissao_val,
            exibe_premiacao=exibe_premiacao_val,
            limite_venda=limites_venda[i] or None,
            tipo_limite=tipos_limite[i] or None,
            grade=grades[i] or None,
            teste=testes[i] or None,
            comissao_retida=comissoes_retidas[i] or None,
            serial=seriais[i] or None,
            cotacao_definida=cotacoes_definidas[i] or None # Novo campo
        )

        db.session.add(novo)
        db.session.flush()

        relatorio = Relatorio(
            usuario=usuario,
            tabela="tb_vendedores",
            acao="Inserção",
            id_linha=novo.id,
            linha=str(novo.__dict__),
            data=datetime.now().date(),
            horario=datetime.now().time()
        )
        db.session.add(relatorio)
        salvos += 1

    db.session.commit()

    if request.is_json:
        return jsonify({"success": True, "message": f"{salvos} novos vendedores salvos."})
    return redirect(url_for('Vendedores.vendedores_page'))


@vendedor_route.route('/cadastrar-sem-android', methods=['POST'])
def cadastrar_vendedor_sem_idAndroid():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Dados inválidos ou ausentes."}), 400

    nome = data.get('nome')
    regiao = data.get('regiao')
    ativo = data.get('ativo')
    area = data.get('area')
    login = data.get('login')
    senha = data.get('senha')
    comissao = data.get('comissao')
    cancelar_poule = data.get('cancelar_poule')
    exibe_comissao = data.get('exibe_comissao')
    exibe_premiacao = data.get('exibe_premiacao')
    limite_venda = data.get('limite_venda')
    tipo_limite = data.get('tipo_limite')
    grade = data.get('grade')
    teste = data.get('teste')
    comissao_retida = data.get('comissao_retida')
    cotacao_definida = data.get('cotacao_definida')

    if not all([nome, regiao, ativo, area, login, senha]):
        return jsonify({"success": False, "message": "Campos obrigatórios (nome, regiao, ativo, area, login, senha) ausentes."}), 400

    existente = Vendedor.query.filter_by(username=login).first()
    if existente:
        return jsonify({"success": False, "message": "Vendedor com este login já existe."}), 409
    
    exibe_comissao_val = 1 if exibe_comissao and exibe_comissao.lower() == 'sim' else 0 if exibe_comissao and exibe_comissao.lower() == 'nao' else None
    exibe_premiacao_val = 1 if exibe_premiacao and exibe_premiacao.lower() == 'sim' else 0 if exibe_premiacao and exibe_premiacao.lower() == 'nao' else None

    novo = Vendedor(
        nome=nome,
        regiao=regiao,
        ativo=ativo,
        area=area,
        username=login,
        senha=senha,
        comissao=comissao,
        cancelar_poule=cancelar_poule,
        exibe_comissao=exibe_comissao_val,
        exibe_premiacao=exibe_premiacao_val,
        limite_venda=limite_venda,
        tipo_limite=tipo_limite,
        grade=grade,
        teste=teste,
        comissao_retida=comissao_retida,
        cotacao_definida=cotacao_definida
    )

    db.session.add(novo)
    db.session.flush()

    usuario = request.cookies.get('username', 'Desconhecido')
    relatorio = Relatorio(
        usuario=usuario,
        tabela="tb_vendedores",
        acao="Inserção (API)",
        id_linha=novo.id,
        linha=str(novo.__dict__),
        data=datetime.now().date(),
        horario=datetime.now().time()
    )
    db.session.add(relatorio)
    db.session.commit()

    return jsonify({"success": True, "message": "Vendedor cadastrado com sucesso!", "vendedor_id": novo.id}), 201


@vendedor_route.route('/editar', methods=['POST'])
def editar_vendedor():
    data = request.get_json()
    username = data.get("username")

    vendedor = Vendedor.query.filter_by(username=username).first()
    if not vendedor:
        return jsonify({"success": False, "message": "Vendedor não encontrado"}), 404
    
    exibe_comissao_val = 1 if data.get("exibe_comissao", "").lower() == 'sim' else 0 if data.get("exibe_comissao", "").lower() == 'nao' else None
    exibe_premiacao_val = 1 if data.get("exibe_premiacao", "").lower() == 'sim' else 0 if data.get("exibe_premiacao", "").lower() == 'nao' else None

    vendedor.nome = data.get("nome")
    vendedor.regiao = data.get("regiao")
    vendedor.ativo = data.get("ativo")
    vendedor.area = data.get("area")
    vendedor.senha = data.get("senha")
    vendedor.comissao = data.get("comissao")
    vendedor.cancelar_poule = data.get("cancelar_poule")
    vendedor.exibe_comissao = exibe_comissao_val
    vendedor.exibe_premiacao = exibe_premiacao_val
    vendedor.limite_venda = data.get("limite_venda")
    vendedor.tipo_limite = data.get("tipo_limite")
    vendedor.grade = data.get("grade")
    vendedor.teste = data.get("teste")
    vendedor.comissao_retida = data.get("comissao_retida")
    vendedor.serial = data.get("serial")
    vendedor.cotacao_definida = data.get("cotacao_definida") # Novo campo

    db.session.commit()
    return jsonify({"success": True, "message": "Vendedor atualizado com sucesso!"})

@vendedor_route.route('/', methods=['DELETE'])
def excluir_vendedor():
    dados = request.get_json()
    username = dados.get('username')
    vendedor = Vendedor.query.filter_by(username=username).first()

    if not vendedor:
        return jsonify({'success': False, 'message': 'Vendedor não encontrado'}), 404

    usuario = request.cookies.get('username', 'Desconhecido')

    relatorio = Relatorio(
        usuario=usuario,
        tabela="tb_vendedores",
        acao="Exclusão",
        id_linha=vendedor.id,
        linha=str(vendedor.__dict__),
        data=datetime.now().date(),
        horario=datetime.now().time()
    )
    db.session.add(relatorio)
    db.session.delete(vendedor)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Vendedor excluído com sucesso'})