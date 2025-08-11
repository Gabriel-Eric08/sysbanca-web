from flask import Blueprint, render_template, jsonify, request
from util.checkCreds import checkCreds
from util.get_animal_grupo import num_animal_grupo
from db_config import db
from models.models import Resultado, Extracao, Aposta, Modalidade, ApostaPremiada
from datetime import datetime
from decimal import Decimal
import json

resultado_route = Blueprint('Resultado', __name__)

@resultado_route.route('/')
def resultado_page():
    check_result = checkCreds()
    
    if not check_result['success']:
        return check_result['message'], 401
    
    user = check_result['user']
    
    try:
        if int(user.acesso_modalidade) != 1:
            return "Usuário não autorizado", 403
    except (AttributeError, ValueError):
        return "Configuração de permissão inválida", 500

    extracoes = Extracao.query.all()
    return render_template('resultados.html', 
                            extracoes=extracoes, 
                            resultado=None,
                            extracao_selecionada=None, 
                            data_selecionada=None,
                            pode_salvar=True)
    
    
@resultado_route.route('/json')
def json_resultados():
    resultados = Resultado.query.all()
    resultado_list = []

    for r in resultados:
        data_do_banco = r.data
        data_formatada = ""

        # Tenta converter a string para um objeto datetime
        if isinstance(data_do_banco, str):
            try:
                # Converte a string 'YYYY-MM-DD HH:MM:SS' para um objeto datetime
                data_objeto = datetime.strptime(data_do_banco, '%Y-%m-%d %H:%M:%S')
                data_formatada = data_objeto.strftime('%Y-%m-%d')
            except ValueError:
                # Se o formato da string for diferente, usa a string como está
                data_formatada = data_do_banco
        elif isinstance(data_do_banco, datetime):
            # Se já for um objeto datetime, formata diretamente
            data_formatada = data_do_banco.strftime('%Y-%m-%d')
        else:
            # Para outros casos, usa o valor como está
            data_formatada = str(data_do_banco)

        linha = {
            'id': r.id,
            'extracao': r.extracao,
            'data': data_formatada,
            'premio_1': num_animal_grupo(r.premio_1),
            'premio_2': num_animal_grupo(r.premio_2),
            'premio_3': num_animal_grupo(r.premio_3),
            'premio_4': num_animal_grupo(r.premio_4),
            'premio_5': num_animal_grupo(r.premio_5),
            'premio_6': num_animal_grupo(r.premio_6),
            'premio_7': num_animal_grupo(r.premio_7),
            'premio_8': num_animal_grupo(r.premio_8),
            'premio_9': num_animal_grupo(r.premio_9),
            'premio_10': num_animal_grupo(r.premio_10)
        }
        resultado_list.append(linha)

    return jsonify(resultado_list)

@resultado_route.route('/salvar', methods=['POST'])
def salvar():
    data = request.get_json()

    extracao = data.get('extracao')
    data_str = data.get('data')
    premios = data.get('premios')  # Lista com 10 elementos

    if not extracao or not data_str or not premios or len(premios) != 10:
        return jsonify({'message': 'Dados inválidos'}), 400

    try:
        data_formatada = datetime.strptime(data_str, '%Y-%m-%d')

        novo_resultado = Resultado(
            extracao=extracao,
            data=data_formatada,
            premio_1=premios[0],
            premio_2=premios[1],
            premio_3=premios[2],
            premio_4=premios[3],
            premio_5=premios[4],
            premio_6=premios[5],
            premio_7=premios[6],
            premio_8=premios[7],
            premio_9=premios[8],
            premio_10=premios[9]
        )

        db.session.add(novo_resultado)
        db.session.commit()

        return jsonify({'message': 'Resultado salvo com sucesso!'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao salvar: {str(e)}'}), 500
    
@resultado_route.route('consultar_json/<extracao>/<data>/', methods=['GET'])
def consultar_resultado_json(extracao, data):
    try:
        data_formatada = datetime.strptime(data, '%Y-%m-%d').date()
        resultado = Resultado.query.filter_by(extracao=extracao).filter(
            db.func.date(Resultado.data) == data_formatada
        ).first()

        if resultado:
            premios = {
                'premio_1': resultado.premio_1,
                'premio_2': resultado.premio_2,
                'premio_3': resultado.premio_3,
                'premio_4': resultado.premio_4,
                'premio_5': resultado.premio_5,
                'premio_6': resultado.premio_6,
                'premio_7': resultado.premio_7,
                'premio_8': resultado.premio_8,
                'premio_9': resultado.premio_9,
                'premio_10': resultado.premio_10,
            }
            return jsonify(premios)
        else:
            return jsonify({'message': 'Nenhum resultado encontrado'}), 404
    except Exception as e:
        return jsonify({'message': f"Erro: {str(e)}"}), 500
    
@resultado_route.route('/consultar_lucro', methods=['POST'])
def consultar_lucro():
    try:
        data = request.get_json()

        extracao = data.get('extracao')
        data_str = data.get('data')
        premios_recebidos = data.get('premios', [])
        
        if not extracao or not data_str or not premios_recebidos or len(premios_recebidos) != 10:
            return jsonify({
                "success": False,
                "message": "Dados de extração, data ou prêmios inválidos."
            }), 400

        data_consulta = datetime.strptime(data_str, '%Y-%m-%d').date()

        # 1. Calcular o valor total apostado somando os valores unitários
        total_apostas = Decimal(0)
        
        apostas_do_dia = Aposta.query.filter_by(
            extracao=extracao,
            data_atual=data_consulta
        ).all()
        
        for aposta in apostas_do_dia:
            apostas_individuais = json.loads(aposta.apostas)
            
            for aposta_detalhada in apostas_individuais:
                # Índice 5 é o valor unitário, Índice 1 é a lista de números
                valor_unitario = Decimal(str(aposta_detalhada[5]))
                numeros = aposta_detalhada[1]
                total_apostas += valor_unitario * len(numeros)

        # 2. Calcular o valor total de prêmios pagos APENAS para os números premiados
        # Desta vez, vamos iterar sobre os premios_recebidos para fazer a busca
        total_premios = Decimal(0)
        
        for numero_premiado in premios_recebidos:
            # A coluna 'apostas' da tabela ApostaPremiada contém o JSON
            # que inclui a lista de números premiados.
            # Precisamos buscar bilhetes que contenham esse numero na sua lista de apostas
            
            # Converte o número premiado para string JSON para a busca no banco
            numero_premiado_json = json.dumps([numero_premiado])
            
            premios_para_numero = ApostaPremiada.query.filter(
                ApostaPremiada.extracao == extracao,
                ApostaPremiada.data_atual == data_consulta,
                ApostaPremiada.apostas.like(f"%{numero_premiado_json}%")
            ).all()

            for premio in premios_para_numero:
                total_premios += Decimal(premio.valor_premio)

        # 3. Calcular o lucro e a porcentagem
        lucro = total_apostas - total_premios
        porcentagem_lucro = (lucro / total_apostas * 100) if total_apostas > 0 else Decimal(0)

        return jsonify({
            "success": True,
            "total_apostas": float(total_apostas),
            "total_premios": float(total_premios),
            "lucro": float(lucro),
            "porcentagem_lucro": float(porcentagem_lucro),
            "extracao": extracao,
            "data": data_str
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro interno ao consultar o lucro: {str(e)}"
        }), 500