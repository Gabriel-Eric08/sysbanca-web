from flask import Blueprint, request, jsonify
from sqlalchemy import func
from models.models import Aposta, AreaCotacao, Modalidade, Descarrego, CadastroDescarrego
from db_config import db
import json
from datetime import time, date, datetime

aposta_route = Blueprint('Aposta', __name__)

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
        # Limpa e padroniza a área e extração do bilhete
        area_aposta_limpa = data['area'].strip()
        extracao_bilhete_limpa = data['extracao'].strip()

        cotacoes = []
        apostas_para_salvar = []
        descarregos_para_salvar = []

        for idx, aposta in enumerate(apostas_data):
            nome_aposta = f"Aposta {idx + 1}"
            # Limpa e padroniza a modalidade da aposta
            modalidade_aposta_limpa = aposta['modalidade'].strip()
            premio_extracao_aposta = aposta['premio'] # Este campo é usado para a cotação, não para o descarrego direto
            unidade_aposta = float(aposta['unidadeAposta'])
            valorTotalAposta = float(aposta['valorTotalAposta'])
            numeros = aposta['numeros']

            # Buscar cotação (mantido como está, pois funciona)
            area_cotacao = AreaCotacao.query.filter_by(
                modalidade=modalidade_aposta_limpa, # Usando a versão limpa
                extracao=premio_extracao_aposta,
                area=area_aposta_limpa, # Usando a versão limpa
                ativar_area_cotacao='S'
            ).first()

            cotacao_aposta = 0.0
            if area_cotacao:
                cotacao_aposta = float(area_cotacao.cotacao)
            else:
                modalidade_obj = Modalidade.query.filter_by(
                    modalidade=modalidade_aposta_limpa # Usando a versão limpa
                ).first()

                if not modalidade_obj:
                    raise ValueError(f"Modalidade '{modalidade_aposta_limpa}' não encontrada.")

                cotacao_aposta = float(modalidade_obj.cotacao)
            
            cotacoes.append([nome_aposta, cotacao_aposta])

            premio_a_receber = unidade_aposta * cotacao_aposta

            # --- Lógica de verificação do descarrego aprimorada ---
            limite_encontrado = False
            limite_aposta = float('inf')

            cadastro_descarregos = CadastroDescarrego.query.all()

            for cad_desc in cadastro_descarregos:
                # Limpa e separa os campos do CadastroDescarrego
                areas_cadastradas = [a.strip() for a in cad_desc.areas.split(',')]
                modalidades_cadastradas = [m.strip() for m in cad_desc.modalidade.split(',')]
                extracoes_cadastradas = [e.strip() for e in cad_desc.extracao.split(',')]

                # Realiza a comparação com os valores limpos e padronizados
                if (area_aposta_limpa in areas_cadastradas and
                    modalidade_aposta_limpa in modalidades_cadastradas and
                    extracao_bilhete_limpa in extracoes_cadastradas):
                    
                    limite_aposta = float(cad_desc.limite)
                    limite_encontrado = True
                    break

            if not limite_encontrado:
                # A mensagem de erro agora usa os valores limpos para maior clareza
                raise ValueError(f"Não existe um limite de descarrego cadastrado para a combinação exata de Área: '{area_aposta_limpa}', Modalidade: '{modalidade_aposta_limpa}' e Extração: '{extracao_bilhete_limpa}'.")

            if premio_a_receber > limite_aposta:
                valor_excedente = premio_a_receber - limite_aposta
                descarregos_para_salvar.append({
                    "extracao": extracao_bilhete_limpa, # Usando a versão limpa
                    "valor_apostado": valorTotalAposta,
                    "valor_excedente": valor_excedente,
                    "numeros": json.dumps(numeros),
                    "data": datetime.now()
                })
            
            aposta_formatada = [
                nome_aposta,
                numeros,
                modalidade_aposta_limpa, # Usando a versão limpa
                premio_extracao_aposta,
                valorTotalAposta,
                unidade_aposta
            ]
            apostas_para_salvar.append(aposta_formatada)

        nova_aposta = Aposta(
            area=data['area'], # O valor original é salvo aqui, a limpeza é para a lógica de descarrego
            vendedor=data['vendedor'],
            data_atual=data_atual,
            hora_atual=hora_atual,
            valor_total=float(data['valor_total']),
            extracao=extracao_bilhete_limpa, # Salva a versão limpa para consistência
            apostas=json.dumps(apostas_para_salvar),
            pre_datar=pre_datar,
            data_agendada=data_agendada
        )

        db.session.add(nova_aposta)
        db.session.commit()

        for descarrego_data in descarregos_para_salvar:
            novo_descarrego = Descarrego(
                bilhete=nova_aposta.id,
                extracao=descarrego_data['extracao'],
                valor_apostado=descarrego_data['valor_apostado'],
                valor_excedente=descarrego_data['valor_excedente'],
                numeros=descarrego_data['numeros'],
                data=descarrego_data['data']
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


