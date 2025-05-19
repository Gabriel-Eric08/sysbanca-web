from flask import Blueprint, render_template, request, redirect, url_for
from models.models import Area
from db_config import db

area_route = Blueprint('Area', __name__)

@area_route.route('/')
def area_page():
    areas = Area.query.all()
    msg = request.args.get('msg')
    return render_template('cadastroArea.html', areas=areas, msg=msg)

@area_route.route('/', methods=['POST'])
def salvar_area():
    areas = []
    i = 0

    # Coleta os dados do formulário
    while True:
        regiao_area = request.form.get(f'areas[{i}][area]')
        desc_area = request.form.get(f'areas[{i}][complemento]')
        ativar_area = request.form.get(f'areas[{i}][ativar_area]')
        if regiao_area is None:
            break
        areas.append({
            'regiao_area': regiao_area.strip().lower(),
            'desc_area': desc_area.strip() if desc_area else '',
            'ativar_area': ativar_area.strip().lower() if ativar_area else ''
        })
        i += 1

    if not areas:
        return redirect(url_for('Area.area_page', msg='Nenhuma área para salvar'))

    salvas = 0
    for item in areas:
        if not item['regiao_area'] or not item['desc_area'] or item['ativar_area'] not in ['sim', 'nao']:
            continue

        # Verifica se já existe essa região
        existe = Area.query.filter(
            db.func.lower(Area.regiao_area) == item['regiao_area']
        ).first()

        if existe:
            continue

        nova = Area(
            regiao_area=item['regiao_area'],
            desc_area=item['desc_area'],
            ativar_area=item['ativar_area']
        )
        db.session.add(nova)
        salvas += 1

    if salvas > 0:
        db.session.commit()
        return redirect(url_for('Area.area_page', msg=f'{salvas} área(s) cadastrada(s) com sucesso'))
    else:
        return redirect(url_for('Area.area_page', msg='Nenhuma nova área foi cadastrada (todas já existiam)'))
