from flask import  Flask, Blueprint, render_template, request, redirect, url_for, flash
from models.models import Extracao
from db_config import db

extracao_route = Blueprint('Extracao', __name__)

@extracao_route.route('/')
def extracao_page():

    extracoes = Extracao.query.all()
    return render_template('cadastroExtracao.html', extracoes=extracoes)

@extracao_route.route('/', methods=['POST'])
def salvar_extracao():
    extracoes_form = []

    # Extrair as linhas recebidas
    # O Flask não cria listas automaticamente para campos nomeados assim,
    # então vamos buscar por todas as keys e agrupar manualmente.

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

    # Agora extracoes_form é uma lista de dicts com as linhas da tabela

    for extr in extracoes_form:
        # Verifica se já existe no banco
        existente = Extracao.query.filter_by(extracao=extr['extracao']).first()
        if existente:
            continue  # pula se já existe

        nova_extracao = Extracao(
            extracao=extr['extracao'],
            fechamento=extr['fechamento'],
            premiacao=int(extr['premiacao']),
            dias_semana=extr['dias_semana'],
            ativo=extr['ativo']
        )
        db.session.add(nova_extracao)

    db.session.commit()
    return redirect(url_for('Extracao.extracao_page'))