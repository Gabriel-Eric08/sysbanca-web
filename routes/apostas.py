from flask import Blueprint, request, jsonify
from sqlalchemy import func
from models.models import Aposta
from db_config import db
import json
from datetime import datetime

aposta_route = Blueprint('Aposta', __name__)

# POST: salva uma nova aposta
@aposta_route.route('/', methods=['POST'])
def salvar_aposta():
    try:
        data = request.get_json()

        # Conversão de datas e horas
        data_atual = datetime.strptime(data['data_atual'], "%d/%m/%Y").date()
        hora_atual = datetime.strptime(data['hora_atual'], "%H:%M").time()
        horario_selecionado = datetime.strptime(data['horario_selecionado'], "%H:%M").time()

        pre_datar = data.get('pre_datar', False)
        data_agendada = None
        if pre_datar:
            if data['data_agendada'] == "00/00/00":
                raise ValueError("Data agendada inválida para pré-datamento.")
            data_agendada = datetime.strptime(data['data_agendada'], "%d/%m/%Y").date()

        nova_aposta = Aposta(
            vendedor=data['vendedor'],
            data_atual=data_atual,
            hora_atual=hora_atual,
            valor_total=data['valor_total'],
            horario_selecionado=horario_selecionado,
            apostas=json.dumps(data['apostas']),
            pre_datar=pre_datar,
            data_agendada=data_agendada
        )

        db.session.add(nova_aposta)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Aposta salva com sucesso!",
            "Numero_bilhete": nova_aposta.id  # retorna o ID da aposta
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


# GET: retorna os dados da aposta por ID
@aposta_route.route('/<int:aposta_id>', methods=['GET'])
def get_aposta(aposta_id):
    try:
        aposta = Aposta.query.get(aposta_id)

        if aposta:
            return jsonify({
                "id": aposta.id,
                "vendedor": aposta.vendedor,
                "data_atual": aposta.data_atual.strftime("%d/%m/%Y"),
                "hora_atual": aposta.hora_atual.strftime("%H:%M"),
                "valor_total": float(aposta.valor_total),
                "horario_selecionado": aposta.horario_selecionado.strftime("%H:%M"),
                "pre_datar": aposta.pre_datar,
                "data_agendada": aposta.data_agendada.strftime("%d/%m/%Y") if aposta.data_agendada else None,
                "apostas": json.loads(aposta.apostas)
            }), 200

        else:
            return jsonify({"success": False, "message": "Aposta não encontrada"}), 404

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400
    


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
