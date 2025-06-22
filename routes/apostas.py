from flask import Blueprint, request, jsonify
from sqlalchemy import func
from models.models import Aposta, AreaCotacao, Modalidade
from db_config import db
import json
from datetime import time, date, datetime

aposta_route = Blueprint('Aposta', __name__)

# POST: salva uma nova aposta
@aposta_route.route('/', methods=['POST'])
def salvar_aposta():
    try:
        data = request.get_json()

        # Validação básica dos dados recebidos
        if not data or 'apostas' not in data:
            return jsonify({"success": False, "message": "Dados de aposta inválidos"}), 400

        # Conversão de datas e horas
        data_atual = datetime.strptime(data['data_atual'], "%d/%m/%Y").date()
        hora_atual = datetime.strptime(data['hora_atual'], "%H:%M").time()

        # Verificação de pré-datamento
        pre_datar = data.get('pre_datar', False)
        data_agendada = None
        if pre_datar:
            if data.get('data_agendada') == "00/00/00":
                raise ValueError("Data agendada inválida para pré-datamento.")
            data_agendada = datetime.strptime(data['data_agendada'], "%d/%m/%Y").date()

        # Processar as apostas
        apostas_data = data['apostas']
        area = data['area']
        extracao = data['extracao']
        cotacoes = []
        apostas_para_salvar = []

        for idx, aposta in enumerate(apostas_data):
            nome_aposta = f"Aposta {idx + 1}"
            modalidade = aposta['modalidade']
            premio = aposta['premio']
            unidade_aposta = aposta['unidadeAposta']
            valorTotalAposta = aposta['valorTotalAposta']
            numeros = aposta['numeros']

            # Formatar a aposta para salvar no banco
            aposta_formatada = [
                nome_aposta,
                numeros,
                modalidade,
                premio,
                valorTotalAposta,
                unidade_aposta
            ]
            apostas_para_salvar.append(aposta_formatada)

            # Buscar cotação
            area_cotacao = AreaCotacao.query.filter_by(
                modalidade=modalidade,
                extracao=premio,
                area=area,
                ativar_area_cotacao='S'
            ).first()

            if area_cotacao:
                cotacoes.append([nome_aposta, float(area_cotacao.cotacao)])
            else:
                modalidade_obj = Modalidade.query.filter_by(
                    modalidade=modalidade
                ).first()

                if not modalidade_obj:
                    raise ValueError(f"Modalidade '{modalidade}' não encontrada.")

                cotacoes.append([nome_aposta, float(modalidade_obj.cotacao)])

        # Salvar a aposta no banco de dados
        nova_aposta = Aposta(
            area=data['area'],
            vendedor=data['vendedor'],
            data_atual=data_atual,
            hora_atual=hora_atual,
            valor_total=float(data['valor_total']),
            extracao=extracao,
            apostas=json.dumps(apostas_para_salvar),
            pre_datar=pre_datar,
            data_agendada=data_agendada
        )

        db.session.add(nova_aposta)
        db.session.commit()

        # Preparar resposta garantindo que todos os valores sejam serializáveis
        response_data = {
            "success": True,
            "message": "Aposta salva com sucesso!",
            "Numero_bilhete": nova_aposta.id,
            "Cotacao": cotacoes,
            "horario_atual": hora_atual.strftime("%H:%M"),
            "Extracao": extracao,
            "data_atual": data_atual.strftime("%d/%m/%Y")
        }

        return jsonify(response_data), 201

    except ValueError as ve:
        db.session.rollback()
        return jsonify({"success": False, "message": str(ve)}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500


# GET: retorna os dados da aposta por ID
@aposta_route.route('/<int:aposta_id>', methods=['GET'])
def get_aposta(aposta_id):
    try:
        aposta = Aposta.query.get(aposta_id)

        if not aposta:
            return jsonify({"success": False, "message": "Aposta não encontrada"}), 404

        # Formatação dos dados para resposta
        response_data = {
            "id": aposta.id,
            "area": aposta.area,
            "vendedor": aposta.vendedor,
            "data_atual": aposta.data_atual.strftime("%d/%m/%Y"),
            "hora_atual": aposta.hora_atual.strftime("%H:%M"),
            "valor_total": float(aposta.valor_total),
            "extracao": aposta.extracao,  # Já é string no formato "LOTEP 10:40"
            "pre_datar": aposta.pre_datar,
            "data_agendada": aposta.data_agendada.strftime("%d/%m/%Y") if aposta.data_agendada else None,
            "apostas": json.loads(aposta.apostas) if aposta.apostas else []
        }

        return jsonify(response_data), 200

    except json.JSONDecodeError as e:
        return jsonify({
            "success": False,
            "message": f"Erro ao decodificar apostas: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro ao recuperar aposta: {str(e)}"
        }), 500
    
@aposta_route.route('/last', methods=['GET'])
def get_ultimo_id_aposta():
    try:
        max_id = db.session.query(func.max(Aposta.id)).scalar()

        if max_id is not None:
            id_formatado = str(max_id).zfill(8)
            return jsonify({"ultimo_id": id_formatado}), 200
        else:
            return jsonify({"success": False, "message": "Nenhuma aposta encontrada"}), 404

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


