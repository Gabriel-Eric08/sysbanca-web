from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from sqlalchemy import func
from models.models import Aposta, AreaCotacao, Modalidade, Descarrego, CadastroDescarrego, ApostaExcluida
from db_config import db
import json
from datetime import time, date, datetime

aposta_route = Blueprint('Aposta', __name__)


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

# POST: salva uma nova aposta
@aposta_route.route('/', methods=['POST'])
def salvar_aposta():
    try:
        data = request.get_json()

        if not data or 'apostas' not in data:
            return jsonify({"success": False, "message": "Dados de aposta inválidos"}), 400

        data_atual = datetime.strptime(data['data_atual'], "%d/%m/%Y").date()
        hora_atual = datetime.strptime(data['hora_atual'], "%H:%M").time()

        pre_datar = data.get('pre_datar', False)
        data_agendada = None
        if pre_datar:
            if data.get('data_agendada') == "00/00/00":
                raise ValueError("Data agendada inválida para pré-datamento.")
            data_agendada = datetime.strptime(data['data_agendada'], "%d/%m/%Y").date()

        apostas_data = data['apostas']
        area_aposta_limpa = data['area'].strip()
        extracao_bilhete_limpa = data['extracao'].strip()

        cotacoes = []
        apostas_para_salvar = []
        descarregos_para_salvar = []

        for idx, aposta in enumerate(apostas_data):
            nome_aposta = f"Aposta {idx + 1}"
            modalidade_aposta_limpa = aposta['modalidade'].strip()
            premio_extracao_aposta = aposta['premio']
            unidade_aposta = float(aposta['unidadeAposta'])
            valorTotalAposta = float(aposta['valorTotalAposta'])
            numeros = aposta['numeros']

            # Cotação
            area_cotacao = AreaCotacao.query.filter_by(
                modalidade=modalidade_aposta_limpa,
                extracao=premio_extracao_aposta,
                area=area_aposta_limpa,
                ativar_area_cotacao='S'
            ).first()

            cotacao_aposta = float(area_cotacao.cotacao) if area_cotacao else None

            if cotacao_aposta is None:
                modalidade_obj = Modalidade.query.filter_by(modalidade=modalidade_aposta_limpa).first()
                if not modalidade_obj:
                    raise ValueError(f"Modalidade '{modalidade_aposta_limpa}' não encontrada.")
                cotacao_aposta = float(modalidade_obj.cotacao)

            cotacoes.append([nome_aposta, cotacao_aposta])

            # Limite de descarrego
            cadastro_descarregos = CadastroDescarrego.query.all()
            limite_aposta = None

            for cad_desc in cadastro_descarregos:
                areas_cadastradas = [a.strip() for a in cad_desc.areas.split(',')]
                modalidades_cadastradas = [m.strip() for m in cad_desc.modalidade.split(',')]
                extracoes_cadastradas = [e.strip() for e in cad_desc.extracao.split(',')]

                if (area_aposta_limpa in areas_cadastradas and
                    modalidade_aposta_limpa in modalidades_cadastradas and
                    extracao_bilhete_limpa in extracoes_cadastradas):
                    limite_aposta = float(cad_desc.limite)
                    break

            if limite_aposta is None:
                raise ValueError(f"Não existe limite para Área: '{area_aposta_limpa}', Modalidade: '{modalidade_aposta_limpa}', Extração: '{extracao_bilhete_limpa}'.")

            # Verifica número a número para descarrego
            for numero in numeros:
                premio = unidade_aposta * cotacao_aposta
                if premio > limite_aposta:
                    valor_excedente = (premio - limite_aposta) / cotacao_aposta
                    descarregos_para_salvar.append({
                        "extracao": extracao_bilhete_limpa,
                        "valor_apostado": unidade_aposta,
                        "valor_excedente": valor_excedente,
                        "numeros": numero,
                        "data": datetime.now()
                    })

            apostas_para_salvar.append([
                nome_aposta,
                numeros,
                modalidade_aposta_limpa,
                premio_extracao_aposta,
                valorTotalAposta,
                unidade_aposta
            ])

        # Cria e salva a aposta
        nova_aposta = Aposta(
            area=data['area'],
            vendedor=data['vendedor'],
            data_atual=data_atual,
            hora_atual=hora_atual,
            valor_total=float(data['valor_total']),
            extracao=extracao_bilhete_limpa,
            apostas=json.dumps(apostas_para_salvar),
            pre_datar=pre_datar,
            data_agendada=data_agendada
        )

        db.session.add(nova_aposta)
        db.session.commit()

        # Salva descarregos
        for desc in descarregos_para_salvar:
            novo_descarrego = Descarrego(
                bilhete=nova_aposta.id,
                extracao=desc['extracao'],
                valor_apostado=desc['valor_apostado'],
                valor_excedente=desc['valor_excedente'],
                numeros=json.dumps([desc['numeros']]),  # sempre lista
                data=desc['data']
            )
            db.session.add(novo_descarrego)

        db.session.commit()

        response_data = {
            "success": True,
            "message": "Aposta salva com sucesso!",
            "Numero_bilhete": nova_aposta.id,
            "Cotacao": cotacoes,
            "horario_atual": hora_atual.strftime("%H:%M"),
            "Extracao": extracao_bilhete_limpa,
            "data_atual": data_atual.strftime("%d/%m/%Y")
        }

        return jsonify(response_data), 201

    except ValueError as ve:
        db.session.rollback()
        return jsonify({"success": False, "message": str(ve)}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500
    
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


@aposta_route.route('/<int:aposta_id>', methods=['DELETE'])
def excluir_aposta_temporariamente(aposta_id):
    try:
        aposta = Aposta.query.get(aposta_id)

        if not aposta:
            return jsonify({"success": False, "message": f"Aposta com ID {aposta_id} não encontrada."}), 404

        # Mover para tabela de exclusões temporárias
        aposta_excluida = ApostaExcluida(
            aposta_id_original=aposta.id,
            area=aposta.area,
            vendedor=aposta.vendedor,
            data_atual=aposta.data_atual,
            hora_atual=aposta.hora_atual,
            valor_total=aposta.valor_total,
            extracao=aposta.extracao,
            apostas=aposta.apostas,
            pre_datar=aposta.pre_datar,
            data_agendada=aposta.data_agendada
        )
        db.session.add(aposta_excluida)

        # Excluir os descarregos vinculados
        Descarrego.query.filter_by(bilhete=aposta_id).delete()

        # Excluir a aposta original
        db.session.delete(aposta)
        db.session.commit()

        return jsonify({"success": True, "message": f"Aposta {aposta_id} movida para exclusão temporária."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro ao excluir aposta: {str(e)}"}), 500
    
@aposta_route.route('/consulta/<int:aposta_id>', methods=['GET'])
def consultar_aposta(aposta_id):
    try:
        aposta = Aposta.query.get(aposta_id)
        consulta_feita = True

        # Transforma o campo de apostas de texto em uma lista
        apostas_detalhadas = json.loads(aposta.apostas) if aposta and aposta.apostas else []

        return render_template(
            'consulta_aposta.html',
            aposta=aposta,
            consulta_feita=consulta_feita,
            apostas_detalhadas=apostas_detalhadas
        )
    except Exception as e:
        print(f"Erro ao buscar aposta: {e}")
        return render_template('consulta_aposta.html', aposta=None, consulta_feita=True)
    
@aposta_route.route('/consulta2/<int:aposta_id>', methods=['GET'])
def consultar_aposta2(aposta_id):
    try:
        aposta = Aposta.query.get(aposta_id)
        consulta_feita = True

        # Transforma o campo de apostas de texto em uma lista
        apostas_detalhadas = json.loads(aposta.apostas) if aposta and aposta.apostas else []

        return render_template(
            'consulta_aposta2.html',
            aposta=aposta,
            consulta_feita=consulta_feita,
            apostas_detalhadas=apostas_detalhadas
        )
    except Exception as e:
        print(f"Erro ao buscar aposta: {e}")
        return render_template('consulta_aposta2.html', aposta=None, consulta_feita=True)

@aposta_route.route('/<int:aposta_id>/excluir', methods=['POST'])
def excluir_aposta_post(aposta_id):
    try:
        aposta = Aposta.query.get(aposta_id)

        if not aposta:
            return redirect(url_for('Aposta.consultar_aposta', aposta_id=aposta_id))

        # Move para a tabela de apostas excluídas
        aposta_excluida = ApostaExcluida(
            aposta_id_original=aposta.id,
            area=aposta.area,
            vendedor=aposta.vendedor,
            data_atual=aposta.data_atual,
            hora_atual=aposta.hora_atual,
            valor_total=aposta.valor_total,
            extracao=aposta.extracao,
            apostas=aposta.apostas,
            pre_datar=aposta.pre_datar,
            data_agendada=aposta.data_agendada
        )
        db.session.add(aposta_excluida)

        # Remove descarregos associados
        Descarrego.query.filter_by(bilhete=aposta_id).delete()

        # Exclui a aposta original
        db.session.delete(aposta)
        db.session.commit()

        return redirect(url_for('Aposta.consultar_aposta', aposta_id=aposta_id))

    except Exception as e:
        db.session.rollback()
        return redirect(url_for('Aposta.consultar_aposta', aposta_id=aposta_id))

@aposta_route.route('/<int:aposta_id>/excluir_ajax', methods=['POST'])
def excluir_aposta_post1(aposta_id):
    try:
        aposta = Aposta.query.get(aposta_id)

        if not aposta:
            return jsonify({"success": False, "message": f"Aposta com ID {aposta_id} não encontrada."}), 404

        # Mover para tabela de exclusões temporárias
        aposta_excluida = ApostaExcluida(
            aposta_id_original=aposta.id,
            area=aposta.area,
            vendedor=aposta.vendedor,
            data_atual=aposta.data_atual,
            hora_atual=aposta.hora_atual,
            valor_total=aposta.valor_total,
            extracao=aposta.extracao,
            apostas=aposta.apostas,
            pre_datar=aposta.pre_datar,
            data_agendada=aposta.data_agendada
        )
        db.session.add(aposta_excluida)

        # Excluir os descarregos vinculados
        Descarrego.query.filter_by(bilhete=aposta_id).delete()

        # Excluir a aposta original
        db.session.delete(aposta)
        db.session.commit()

        return jsonify({"success": True, "message": f"Aposta {aposta_id} excluída com sucesso."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Erro ao excluir aposta: {str(e)}"}), 500