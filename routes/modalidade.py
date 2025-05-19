from flask import  Flask, Blueprint, render_template, request, redirect, url_for, flash
from models.models import Modalidade
from db_config import db

modalidade_route = Blueprint('Modalidade', __name__)

@modalidade_route.route('/')
def modalidade_page():

    modalidades = Modalidade.query.all()
    return render_template('cadastroModalidade.html', modalidades=modalidades)

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