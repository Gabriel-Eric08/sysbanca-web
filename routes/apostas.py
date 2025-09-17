from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from sqlalchemy import func
from models.models import Aposta, AreaCotacao, Modalidade, Descarrego, CadastroDescarrego, CotacaoDefinida, ApostaExcluida, ApostaPremiada, ComissaoArea, Vendedor, Extracao, Area, Coleta
from db_config import db
import json
from datetime import time, date, datetime

aposta_route = Blueprint('Aposta', __name__)

@aposta_route.route('/homeapk2')
def apostas_apk():
    # Consulta todos os registros das tabelas
    # O .query.all() retorna uma lista de objetos
    modalidades = Modalidade.query.all()
    extracoes = Extracao.query.all()
    
    # Renderiza o template e passa as listas como variáveis
    return render_template(
        'apostas_apk.html',
        modalidades=modalidades,
        extracoes=extracoes
    )

@aposta_route.route('/vendedor/<string:vendedor_username>/<string:data_str>', methods=['GET'])
def get_apostas_por_vendedor_e_data(vendedor_username, data_str):
    try:
        # Tenta converter a string da data para um objeto date
        data_busca = datetime.strptime(data_str, "%d-%m-%Y").date()
    except ValueError:
        return jsonify({"success": False, "message": "Formato de data inválido. Use DD-MM-YYYY."}), 400

    try:
        # Busca todas as apostas do vendedor na data especificada
        apostas = Aposta.query.filter_by(
            vendedor=vendedor_username,
            data_atual=data_busca
        ).all()

        if not apostas:
            return jsonify({
                "success": False,
                "message": f"Nenhuma aposta encontrada para o vendedor '{vendedor_username}' na data {data_str}."
            }), 404

        # Prepara a lista de apostas para o JSON de resposta
        response_apostas = []
        for aposta in apostas:
            response_apostas.append({
                "id": aposta.id,
                "area": aposta.area,
                "vendedor": aposta.vendedor,
                "data_atual": aposta.data_atual.strftime("%d/%m/%Y"),
                "hora_atual": aposta.hora_atual.strftime("%H:%M"),
                "valor_total": float(aposta.valor_total),
                "extracao": aposta.extracao,
                "pre_datar": aposta.pre_datar,
                "data_agendada": aposta.data_agendada.strftime("%d/%m/%Y") if aposta.data_agendada else None,
                "apostas": json.loads(aposta.apostas) if aposta.apostas else []
            })

        return jsonify({
            "success": True,
            "message": f"Apostas encontradas para o vendedor '{vendedor_username}' na data {data_str}.",
            "apostas": response_apostas
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro interno ao buscar apostas: {str(e)}"
        }), 500


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
def salvar_apostas():
    try:
        data = request.get_json()

        apostas = data.get('apostas', [])
        area = data.get('area')
        extracao = data.get('extracao')
        data_agendada_str = data.get('data_agendada')
        data_atual_str = data.get('data_atual')
        hora_atual_str = data.get('hora_atual')
        pre_datar = data.get('pre_datar', False)
        vendedor_username = data.get('vendedor')

        # --- Camada de Depuração 1: Log de Dados Recebidos ---
        print("--- DEBUG: Dados recebidos na rota /aposta ---")
        print(f"Dados JSON: {data}")
        print("---------------------------------------------")
        # ----------------------------------------------------

        # 1. Obter o objeto Vendedor
        vendedor_obj = Vendedor.query.filter_by(username=vendedor_username).first()
        if not vendedor_obj:
            return jsonify({
                "success": False,
                "message": f"Vendedor '{vendedor_username}' não encontrado."
            }), 400

        # Obter o limite de venda diário do vendedor
        limite_venda = vendedor_obj.limite_venda if vendedor_obj.limite_venda is not None else float('inf')

        # Obter a data atual da aposta para a verificação diária
        data_atual = datetime.strptime(data_atual_str, "%d/%m/%Y").date()
        
        # Obter o valor total da nova aposta
        valor_nova_aposta = float(data.get('valor_total', 0))

        # 2. Calcular o total de vendas do vendedor para a data atual
        total_venda_dia = db.session.query(func.sum(Aposta.valor_total)).filter(
            Aposta.vendedor == vendedor_username,
            Aposta.data_atual == data_atual
        ).scalar() or 0.0

        # 3. Verificar se a nova aposta ultrapassa o limite diário
        if (total_venda_dia + valor_nova_aposta) > limite_venda:
            return jsonify({
                "success": False,
                "message": (f"Venda recusada. O valor de R$ {total_venda_dia:.2f} já foi atingido hoje."
                            f" Seu limite diário de venda é de R$ {limite_venda:.2f}.")
            }), 403

        # 4. Inicializar data_agendada (Correção do erro anterior)
        data_agendada = None
        
        if pre_datar and data_agendada_str and data_agendada_str != "00/00/00":
            data_agendada = datetime.strptime(data_agendada_str, "%d/%m/%Y").date()
        
        # --- Camada de Depuração 2: Log antes da conversão da hora ---
        print("--- DEBUG: Tentando converter a hora ---")
        print(f"Valor de hora_atual_str: '{hora_atual_str}'")
        # -----------------------------------------------------------
        if len(hora_atual_str) == 8:  # Formato "HH:MM:SS"
            hora_atual = datetime.strptime(hora_atual_str, "%H:%M:%S").time()
        else:  # Assume formato "HH:MM"
            hora_atual = datetime.strptime(hora_atual_str, "%H:%M").time()

        apostas_para_salvar = []
        descarregos_para_salvar = []

        contador_apostas = 1
        for aposta in apostas:
            numeros = aposta.get('numeros', [])
            modalidade_nome = aposta.get('modalidade')
            premio_str = aposta.get('premio')
            valor_total_aposta = float(aposta.get('valorTotalAposta', 0))
            unidade_aposta = float(aposta.get('unidadeAposta', 0))
            
            # --- Camada de Depuração 3: Log dentro do loop de apostas ---
            print(f"--- DEBUG: Processando aposta {contador_apostas} ---")
            print(f"Números: {numeros}")
            print(f"Modalidade: {modalidade_nome}")
            print(f"Valor total da aposta: {valor_total_aposta}")
            print("---------------------------------------------")
            # ------------------------------------------------------------

            modalidade_obj = Modalidade.query.filter_by(modalidade=modalidade_nome).first()
            if not modalidade_obj:
                return jsonify({
                    "success": False,
                    "message": f"Modalidade '{modalidade_nome}' não encontrada."
                }), 400

            normalized_area = normalize_string(area)
            normalized_extracao = normalize_string(extracao)
            normalized_modalidade_name = normalize_string(modalidade_nome)

            limite_descarrego = None
            descarregos_cadastrados = CadastroDescarrego.query.filter(
                db.or_(
                    db.func.lower(CadastroDescarrego.areas).like(f"%, {normalized_area},%"),
                    db.func.lower(CadastroDescarrego.areas).like(f"{normalized_area},%"),
                    db.func.lower(CadastroDescarrego.areas).like(f"%,{normalized_area}"),
                    db.func.lower(CadastroDescarrego.areas) == normalized_area
                ),
                db.or_(
                    db.func.lower(CadastroDescarrego.extracao).like(f"%, {normalized_extracao},%"),
                    db.func.lower(CadastroDescarrego.extracao).like(f"{normalized_extracao},%"),
                    db.func.lower(CadastroDescarrego.extracao).like(f"%,{normalized_extracao}"),
                    db.func.lower(CadastroDescarrego.extracao) == normalized_extracao
                ),
                db.or_(
                    db.func.lower(CadastroDescarrego.modalidade).like(f"%, {normalized_modalidade_name},%"),
                    db.func.lower(CadastroDescarrego.modalidade).like(f"{normalized_modalidade_name},%"),
                    db.func.lower(CadastroDescarrego.modalidade).like(f"%,{normalized_modalidade_name}"),
                    db.func.lower(CadastroDescarrego.modalidade) == normalized_modalidade_name
                )
            ).first()

            if descarregos_cadastrados:
                limite_descarrego = float(descarregos_cadastrados.limite)
            else:
                limite_descarrego = float(modalidade_obj.limite_descarrego) if modalidade_obj.limite_descarrego else 10_000_000_000
            
            # --- INÍCIO DA NOVA LÓGICA DE COTAÇÃO ---
            
            cotacao_utilizada = None
            
            # 1. Define as modalidades que usam a cotação definida do vendedor
            modalidades_cotacao_definida = ['Milhar', 'Centena', 'Dezena', 'Grupo', 'Terno de Grupo', 'Terno de Dezena']
            
            # 2. Checa se a modalidade da aposta está na lista e se o vendedor tem uma cotação definida
            if modalidade_nome in modalidades_cotacao_definida and vendedor_obj.cotacao_definida and vendedor_obj.cotacao_definida != 0:
                print(f"--- DEBUG: Usando cotação definida do vendedor {vendedor_username} ---")
                
                # Busca a linha na tabela CotacaoDefinida com base no nome
                cotacao_definida_obj = CotacaoDefinida.query.filter_by(nome=vendedor_obj.cotacao_definida).first()
                
                if cotacao_definida_obj:
                    # Usa um dicionário para mapear a modalidade à coluna correspondente
                    cotacao_map = {
                        'Milhar': cotacao_definida_obj.milhar,
                        'Centena': cotacao_definida_obj.centena,
                        'Dezena': cotacao_definida_obj.dezena,
                        'Grupo': cotacao_definida_obj.grupo,
                        'Terno de Grupo': cotacao_definida_obj.terno_de_grupo,
                        'Terno de Dezena': cotacao_definida_obj.terno_de_dezena,
                    }
                    # Pega a cotação do dicionário, se não encontrar, usa a da modalidade padrão (fallback)
                    cotacao_utilizada = float(cotacao_map.get(modalidade_nome))
                    
                    if cotacao_utilizada is not None:
                         print(f"--- DEBUG: Cotação definida encontrada: {cotacao_utilizada} ---")
                
            # 3. Se a cotação ainda não foi definida, segue o fluxo padrão (AreaCotacao ou Modalidade)
            if cotacao_utilizada is None:
                print("--- DEBUG: Usando o fluxo padrão de cotação (AreaCotacao ou Modalidade) ---")
                area_cotacao_obj = AreaCotacao.query.filter(
                    db.or_(
                        db.func.lower(AreaCotacao.area).like(f"%, {normalized_area},%"),
                        db.func.lower(AreaCotacao.area).like(f"{normalized_area},%"),
                        db.func.lower(AreaCotacao.area).like(f"%,{normalized_area}"),
                        db.func.lower(AreaCotacao.area) == normalized_area
                    ),
                    db.or_(
                        db.func.lower(AreaCotacao.extracao).like(f"%, {normalized_extracao},%"),
                        db.func.lower(AreaCotacao.extracao).like(f"{normalized_extracao},%"),
                        db.func.lower(AreaCotacao.extracao).like(f"%,{normalized_extracao}"),
                        db.func.lower(AreaCotacao.extracao) == normalized_extracao
                    ),
                    db.or_(
                        db.func.lower(AreaCotacao.modalidade).like(f"%, {normalized_modalidade_name},%"),
                        db.func.lower(AreaCotacao.modalidade).like(f"{normalized_modalidade_name},%"),
                        db.func.lower(AreaCotacao.modalidade).like(f"%,{normalized_modalidade_name}"),
                        db.func.lower(AreaCotacao.modalidade) == normalized_modalidade_name
                    )
                ).first()

                if area_cotacao_obj:
                    cotacao_utilizada = float(area_cotacao_obj.cotacao)
                else:
                    cotacao_utilizada = float(modalidade_obj.cotacao)
            
            # --- FIM DA NOVA LÓGICA DE COTAÇÃO ---

            premio_total_calculado = valor_total_aposta * cotacao_utilizada

            # ---- NOVA LÓGICA DE DESCARREGO POR NÚMERO ----
            
            # Itera sobre cada número da aposta para verificar individualmente
            for numero in numeros:
                # 5. Consulta para verificar se o número já teve um descarrego hoje
                descarrego_existente = Descarrego.query.join(Aposta, Descarrego.bilhete == Aposta.id).filter(
                    # Filtra por área, extração, modalidade e data
                    db.func.lower(Aposta.area) == normalized_area,
                    db.func.lower(Descarrego.extracao) == normalized_extracao,
                    db.func.lower(Descarrego.modalidade) == normalized_modalidade_name,
                    Aposta.data_atual == data_atual,
                    # Verifica se o número existe na coluna 'numeros' do descarrego
                    # Assume que 'numeros' é um JSON de lista de strings, ex: ["1234"]
                    db.func.lower(Descarrego.numeros).like(f'%"{numero}"%')
                ).first()

                if descarrego_existente:
                    # Se o número já foi descarregado hoje, descarrega o valor TOTAL da aposta
                    valor_excedente = unidade_aposta
                    premio_excedente = unidade_aposta * cotacao_utilizada
                elif unidade_aposta > limite_descarrego:
                    # Se não houve descarrego anterior, verifica se a aposta atual excede o limite
                    valor_excedente = unidade_aposta - limite_descarrego
                    premio_excedente = valor_excedente * cotacao_utilizada
                else:
                    # Nenhuma das condições de descarrego foi atendida para este número
                    continue # Pula para o próximo número

                # Adiciona o descarrego à lista para salvar
                descarregos_para_salvar.append({
                    "bilhete_id": None,
                    "extracao": extracao,
                    "valor_apostado": unidade_aposta,
                    "valor_excedente": valor_excedente,
                    "numeros": [numero],
                    "data": datetime.now(),
                    "modalidade": modalidade_nome,
                    "premio_total": unidade_aposta * cotacao_utilizada,
                    "premio_excedente": premio_excedente,
                    "tipo_premio": premio_str
                })

            # ---- FIM DA NOVA LÓGICA DE DESCARREGO ----

            nome_aposta = f"Aposta {contador_apostas}"
            apostas_para_salvar.append([
                nome_aposta,
                numeros,
                modalidade_nome,
                premio_str,
                valor_total_aposta,
                unidade_aposta
            ])

            contador_apostas += 1

        aposta_obj = Aposta(
            vendedor=vendedor_username,
            data_atual=data_atual,
            hora_atual=hora_atual,
            valor_total=valor_nova_aposta,
            extracao=extracao,
            apostas=json.dumps(apostas_para_salvar),
            pre_datar=pre_datar,
            data_agendada=data_agendada,
            area=area
        )
        db.session.add(aposta_obj)
        db.session.commit()

        # Salva descarregos gerados
        for d in descarregos_para_salvar:
            descarrego_obj = Descarrego(
                bilhete=aposta_obj.id,
                extracao=d['extracao'],
                valor_apostado=d['valor_apostado'],
                valor_excedente=d['valor_excedente'],
                numeros=json.dumps(d['numeros']),
                data=d['data'],
                modalidade=d['modalidade'],
                premio_total=d['premio_total'],
                premio_excedente=d['premio_excedente'],
                tipo_premio=d['tipo_premio']
            )
            db.session.add(descarrego_obj)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Apostas e descarregos salvos com sucesso.",
            "total_apostas_salvas": len(apostas_para_salvar),
            "total_descarregos_gerados": len(descarregos_para_salvar),
            "numero_bilhete": aposta_obj.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Erro interno ao salvar aposta: {str(e)}"
        }), 500
 
@aposta_route.route('/cotacao', methods=['POST'])
def get_cotacao():
    try:
        data = request.get_json()
        area = data.get('area')
        extracao = data.get('extracao')
        modalidade_nome = data.get('modalidade')

        if not area or not extracao or not modalidade_nome:
            return jsonify({
                "success": False,
                "message": "Parâmetros obrigatórios: area, extracao e modalidade"
            }), 400

        # Normaliza strings
        normalized_area = normalize_string(area)
        normalized_extracao = normalize_string(extracao)
        normalized_modalidade = normalize_string(modalidade_nome)

        # Busca modalidade
        modalidade_obj = Modalidade.query.filter_by(modalidade=modalidade_nome).first()
        if not modalidade_obj:
            return jsonify({
                "success": False,
                "message": f"Modalidade '{modalidade_nome}' não encontrada."
            }), 404

        # Procura cotação específica em AreaCotacao
        area_cotacao_obj = AreaCotacao.query.filter(
            db.or_(
                db.func.lower(AreaCotacao.area).like(f"%, {normalized_area},%"),
                db.func.lower(AreaCotacao.area).like(f"{normalized_area},%"),
                db.func.lower(AreaCotacao.area).like(f"%,{normalized_area}"),
                db.func.lower(AreaCotacao.area) == normalized_area
            ),
            db.or_(
                db.func.lower(AreaCotacao.extracao).like(f"%, {normalized_extracao},%"),
                db.func.lower(AreaCotacao.extracao).like(f"{normalized_extracao},%"),
                db.func.lower(AreaCotacao.extracao).like(f"%,{normalized_extracao}"),
                db.func.lower(AreaCotacao.extracao) == normalized_extracao
            ),
            db.or_(
                db.func.lower(AreaCotacao.modalidade).like(f"%, {normalized_modalidade},%"),
                db.func.lower(AreaCotacao.modalidade).like(f"{normalized_modalidade},%"),
                db.func.lower(AreaCotacao.modalidade).like(f"%,{normalized_modalidade}"),
                db.func.lower(AreaCotacao.modalidade) == normalized_modalidade
            )
        ).first()

        if area_cotacao_obj:
            cotacao = float(area_cotacao_obj.cotacao)
            origem = "area_cotacao"
        else:
            cotacao = float(modalidade_obj.cotacao)
            origem = "modalidade"

        return jsonify({
            "success": True,
            "cotacao": cotacao,
            "origem": origem
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Erro interno ao buscar cotação: {str(e)}"
        }), 500

@aposta_route.route('/last', methods=['GET'])
def get_ultimo_id_aposta():
    try:
        max_id = db.session.query(func.max(Aposta.id)).scalar()
        max_id_excluida = db.session.query(func.max(ApostaExcluida.aposta_id_original)).scalar()

        # Se ambos forem None
        if max_id is None and max_id_excluida is None:
            return jsonify({"success": False, "message": "Nenhuma aposta encontrada"}), 404

        # Se só max_id for None
        if max_id is None:
            return jsonify({"ultimo_id": str(max_id_excluida).zfill(8)}), 200

        # Se só max_id_excluida for None
        if max_id_excluida is None:
            return jsonify({"ultimo_id": str(max_id).zfill(8)}), 200

        # Se ambos tiverem valor
        if max_id > max_id_excluida:
            return jsonify({"ultimo_id": str(max_id).zfill(8)}), 200
        else:
            return jsonify({"ultimo_id": str(max_id_excluida).zfill(8)}), 200

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
        aposta_premiada = None
        apostas_detalhadas = []
        consulta_feita = True

        if aposta:
            apostas_detalhadas = json.loads(aposta.apostas) if aposta.apostas else []
            aposta_premiada = ApostaPremiada.query.filter_by(numero_bilhete=aposta.id).first()
            
            # --- Adição de Lógica ---
            # Se a aposta premiada existir, vamos reformatar 'apostas_detalhadas'
            # para o template renderizar corretamente, usando os dados da aposta premiada
            if aposta_premiada:
                detalhes_premiados = json.loads(aposta_premiada.apostas)
                apostas_detalhadas = []
                for item in detalhes_premiados:
                    # Reformata o dicionário em uma lista para compatibilidade com o HTML
                    detalhe_formatado = [
                        item.get('nomeAposta', 'N/A'), # Supondo que 'nomeAposta' exista no JSON
                        item.get('numeros', []),
                        item.get('modalidade', 'N/A'),
                        item.get('premio', 'N/A'), # Usado 'premio' em vez de 'tipo de aposta'
                        item.get('valorTotalAposta', 0.0),
                        item.get('unidadeAposta', 0.0)
                    ]
                    apostas_detalhadas.append(detalhe_formatado)

        return render_template(
            'consulta_aposta.html',
            aposta=aposta,
            consulta_feita=consulta_feita,
            apostas_detalhadas=apostas_detalhadas,
            aposta_premiada=aposta_premiada
        )

    except Exception as e:
        print(f"Erro ao buscar aposta: {e}")
        return render_template('consulta_aposta.html', aposta=None, consulta_feita=True)
    
@aposta_route.route('/consulta_excluida/<int:aposta_excluida_id>', methods=['GET'])
def consultar_aposta_excluida(aposta_excluida_id):
    try:
        # Busca a aposta na tabela ApostaExcluida
        aposta = ApostaExcluida.query.get(aposta_excluida_id)
        consulta_feita = True

        # Transforma o campo de apostas de texto em uma lista
        apostas_detalhadas = json.loads(aposta.apostas) if aposta and aposta.apostas else []

        return render_template(
            'consulta_aposta.html', # Você pode criar um template específico se preferir
            aposta=aposta,
            consulta_feita=consulta_feita,
            apostas_detalhadas=apostas_detalhadas
        )
    except Exception as e:
        # Tratamento de erro genérico, como você tinha originalmente
        print(f"Erro ao buscar aposta excluída: {e}")
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
    

@aposta_route.route('/<int:aposta_excluida_id>/recuperar', methods=['POST'])
def recuperar_aposta_excluida(aposta_excluida_id):
    # Busca a aposta excluída
    aposta_excluida = ApostaExcluida.query.get(aposta_excluida_id)

    if not aposta_excluida:
        return jsonify({'erro': 'Aposta excluída não encontrada.'}), 404

    # Cria uma nova aposta com os mesmos dados
    nova_aposta = Aposta(
        id=aposta_excluida.aposta_id_original,
        vendedor=aposta_excluida.vendedor,
        data_atual=aposta_excluida.data_atual,
        hora_atual=aposta_excluida.hora_atual,
        valor_total=aposta_excluida.valor_total,
        extracao=aposta_excluida.extracao,
        apostas=aposta_excluida.apostas,
        pre_datar=aposta_excluida.pre_datar,
        data_agendada=aposta_excluida.data_agendada,
        area=aposta_excluida.area
    )

    # Adiciona a nova aposta
    db.session.add(nova_aposta)

    # Remove a aposta da tabela de apostas excluídas
    db.session.delete(aposta_excluida)

    # Commit de tudo
    db.session.commit()

    return jsonify({
        'mensagem': 'Aposta recuperada com sucesso.',
        'nova_aposta_id': nova_aposta.id
    }), 201


@aposta_route.route('/premiada', methods=['POST'])
def salvar_aposta_premiada():
    try:
        data = request.get_json()

        # Extraindo dados do JSON
        apostas_raw = data.get('apostas', [])
        area = data.get('area')
        extracao = data.get('extracao')
        data_agendada_str = data.get('data_agendada')
        data_atual_str = data.get('data_atual')
        hora_atual_str = data.get('hora_atual')
        pre_datar = data.get('pre_datar', False)
        vendedor = data.get('vendedor')
        valor_total = float(data.get('valor_total', 0))
        valor_premio = data.get('valor_premio')
        # --- Captura o novo campo 'numero_bilhete' e converte para INT ---
        numero_bilhete_str = data.get('numero_bilhete')
        if not numero_bilhete_str:
            return jsonify({"success": False, "message": "Campo 'numero_bilhete' é obrigatório."}), 400
        try:
            numero_bilhete = int(numero_bilhete_str)
        except ValueError:
            return jsonify({"success": False, "message": "Campo 'numero_bilhete' deve ser um número inteiro válido."}), 400
        # --- Fim Captura e Conversão ---

        # Convertendo datas e horas para objetos Python
        data_agendada = None
        if pre_datar and data_agendada_str and data_agendada_str != "00/00/00":
            data_agendada = datetime.strptime(data_agendada_str, "%d/%m/%Y").date()

        if not data_atual_str:
            return jsonify({"success": False, "message": "Campo 'data_atual' é obrigatório."}), 400
        if not hora_atual_str:
            return jsonify({"success": False, "message": "Campo 'hora_atual' é obrigatório."}), 400

        data_atual = datetime.strptime(data_atual_str, "%d/%m/%Y").date()
        if len(hora_atual_str) == 8:  # Formato "HH:MM:SS"
            hora_atual = datetime.strptime(hora_atual_str, "%H:%M:%S").time()
        else:  # Assume formato "HH:MM"
            hora_atual = datetime.strptime(hora_atual_str, "%H:%M").time()

        apostas_json = json.dumps(apostas_raw)

        # Criando a instância da ApostaPremiada
        aposta_premiada_obj = ApostaPremiada(
            vendedor=vendedor,
            data_atual=data_atual,
            hora_atual=hora_atual,
            valor_total=valor_total,
            extracao=extracao,
            apostas=apostas_json,
            pre_datar=pre_datar,
            data_agendada=data_agendada,
            area=area,
            valor_premio=valor_premio,
            impresso=0,
            # --- Passa o novo campo 'numero_bilhete' para o modelo ---
            numero_bilhete=numero_bilhete
            # --- Fim Passa ---
        )

        # Adicionando ao banco de dados e commitando
        db.session.add(aposta_premiada_obj)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Aposta premiada salva com sucesso.",
            "id_aposta_premiada": aposta_premiada_obj.id
        }), 201

    except ValueError as ve:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Erro de validação de dados: {str(ve)}. Verifique o formato de datas e horas."
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Erro interno ao salvar aposta premiada: {str(e)}"
        }), 500


def normalize_string(s):
    import unicodedata
    if s is None:
        return ""
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('utf-8')
    return s.strip().lower()

@aposta_route.route('/relatorio-geral-caixa', methods=['GET'])
def relatorio_apostas_detalhado():
    """
    Renderiza a página de relatório com os campos de filtro.
    Não carrega os dados das apostas e prêmios.
    """
    vendedores_nomes = [v[0] for v in Vendedor.query.with_entities(Vendedor.nome).distinct().order_by(Vendedor.nome).all()]
    modalidades_nomes = [m[0] for m in Modalidade.query.with_entities(Modalidade.modalidade).distinct().order_by(Modalidade.modalidade).all()]
    extracoes_nomes = [e[0] for e in Extracao.query.with_entities(Extracao.extracao).distinct().order_by(Extracao.extracao).all()]
    areas_nomes = [a[0] for a in Area.query.with_entities(Area.regiao_area).distinct().order_by(Area.regiao_area).all()]

    return render_template(
        'relatorio_apostas.html',
        vendedores=vendedores_nomes,
        modalidades=modalidades_nomes,
        extracoes=extracoes_nomes,
        areas=areas_nomes,
        debito_anterior=0.00
    )


@aposta_route.route('/api/relatorio-caixa-dados', methods=['POST'])
def get_relatorio_caixa_dados():
    """
    Recebe os filtros do frontend e retorna os dados de apostas e prêmios.
    """
    try:
        filtros = request.get_json()
        if not filtros:
            return jsonify({"error": "Nenhum filtro recebido."}), 400

        # Configura as consultas baseadas nos filtros
        query_apostas = Aposta.query
        query_apostas_premiadas = ApostaPremiada.query

        # Aplica filtros às consultas de apostas
        if filtros.get('vendedor'):
            normalized_vendedor = normalize_string(filtros['vendedor'])
            query_apostas = query_apostas.filter(func.lower(Aposta.vendedor) == normalized_vendedor)
            
        if filtros.get('extracao'):
            normalized_extracao = normalize_string(filtros['extracao'])
            query_apostas = query_apostas.filter(func.lower(Aposta.extracao) == normalized_extracao)

        if filtros.get('area'):
            normalized_area = normalize_string(filtros['area'])
            query_apostas = query_apostas.filter(func.lower(Aposta.area) == normalized_area)
            
        if filtros.get('data'):
            query_apostas = query_apostas.filter(Aposta.data_atual == filtros['data'])

        # Aplica filtros às consultas de apostas premiadas
        if filtros.get('vendedor'):
            normalized_vendedor = normalize_string(filtros['vendedor'])
            query_apostas_premiadas = query_apostas_premiadas.filter(func.lower(ApostaPremiada.vendedor) == normalized_vendedor)
            
        if filtros.get('extracao'):
            normalized_extracao = normalize_string(filtros['extracao'])
            query_apostas_premiadas = query_apostas_premiadas.filter(func.lower(ApostaPremiada.extracao) == normalized_extracao)

        if filtros.get('area'):
            normalized_area = normalize_string(filtros['area'])
            query_apostas_premiadas = query_apostas_premiadas.filter(func.lower(ApostaPremiada.area) == normalized_area)
            
        if filtros.get('data'):
            query_apostas_premiadas = query_apostas_premiadas.filter(ApostaPremiada.data_atual == filtros['data'])

        apostas_filtradas_db = query_apostas.order_by(Aposta.id.desc()).all()
        apostas_premiadas_filtradas_db = query_apostas_premiadas.order_by(ApostaPremiada.id.desc()).all()
        
        # Processamento das apostas detalhadas
        apostas_detalhadas = []
        for aposta_principal in apostas_filtradas_db:
            try:
                apostas_json = json.loads(aposta_principal.apostas)
            except json.JSONDecodeError:
                continue # Pula para o próximo bilhete se o JSON for inválido

            for aposta_individual in apostas_json:
                # Validação da estrutura do dado
                if not isinstance(aposta_individual, list) or len(aposta_individual) < 6:
                    continue

                try:
                    modalidade_nome = aposta_individual[2]
                    valor_apostado_raw = aposta_individual[4]
                    vendedor_nome = aposta_principal.vendedor
                    area_nome = aposta_principal.area
                    extracao_nome = aposta_principal.extracao
                    unidade_aposta = aposta_individual[5]

                    # Validação de valor numérico
                    valor_apostado_individual = float(valor_apostado_raw)
                except (IndexError, ValueError, TypeError):
                    continue

                comissao_aplicada = 0.0
                normalized_area = normalize_string(area_nome)
                normalized_modalidade = normalize_string(modalidade_nome)
                normalized_vendedor = normalize_string(vendedor_nome)
                normalized_extracao = normalize_string(extracao_nome)

                comissao_especifica = ComissaoArea.query.filter(
                    func.lower(ComissaoArea.area) == normalized_area,
                    func.lower(ComissaoArea.modalidade) == normalized_modalidade,
                    func.lower(ComissaoArea.vendedor) == normalized_vendedor,
                    func.lower(ComissaoArea.extracao) == normalized_extracao,
                    ComissaoArea.ativar == 'sim'
                ).first()

                if comissao_especifica:
                    try:
                        comissao_aplicada = float(comissao_especifica.comissao)
                    except (ValueError, TypeError):
                        comissao_aplicada = 0.0
                else:
                    vendedor_obj = Vendedor.query.filter(func.lower(Vendedor.nome) == normalized_vendedor).first()
                    if vendedor_obj and vendedor_obj.comissao is not None:
                        try:
                            comissao_aplicada = float(vendedor_obj.comissao)
                        except (ValueError, TypeError):
                            comissao_aplicada = 0.0
                    else:
                        comissao_aplicada = 0.0

                valor_comissao = (valor_apostado_individual * comissao_aplicada) / 100

                apostas_detalhadas.append({
                    "bilhete_id": aposta_principal.id,
                    "data_aposta": aposta_principal.data_atual.strftime('%d/%m/%Y'),
                    "vendedor": vendedor_nome,
                    "extracao": extracao_nome,
                    "area": area_nome,
                    "modalidade": modalidade_nome,
                    "numeros": ", ".join(aposta_individual[1]),
                    "premio_str": aposta_individual[3],
                    "valor_apostado_individual": valor_apostado_individual,
                    "unidade_aposta": unidade_aposta,
                    "valor_total_bilhete": aposta_principal.valor_total,
                    "comissao_percentual": comissao_aplicada,
                    "valor_comissao": valor_comissao
                })
        
        # Processamento das apostas premiadas
        apostas_premiadas = []
        for premiada in apostas_premiadas_filtradas_db:
            try:
                # Trata valor do prêmio, convertendo para float se necessário
                valor_premio_str = str(premiada.valor_premio).replace(',', '.')
                valor_premio_float = float(valor_premio_str)
            except (ValueError, TypeError):
                valor_premio_float = 0.0

            apostas_premiadas.append({
                "id": premiada.id,
                "numero_bilhete": premiada.numero_bilhete,
                "data_atual": premiada.data_atual.strftime('%d/%m/%Y'),
                "hora_atual": premiada.hora_atual.strftime('%H:%M'),
                "vendedor": premiada.vendedor,
                "extracao": premiada.extracao,
                "area": premiada.area,
                "valor_premio": f"{valor_premio_float:.2f}".replace('.', ','),
                "impresso": premiada.impresso,
                "pago": premiada.pago,
            })
        
        return jsonify({
            "apostas_detalhadas": apostas_detalhadas,
            "apostas_premiadas": apostas_premiadas,
        })
    except Exception as e:
        return jsonify({"error": f"Erro interno do servidor: {e}"}), 500

@aposta_route.route('/relatorio-apostas-json', methods=['POST'])
def relatorio_apostas_json():
    data = request.get_json()

    filtro_vendedor = data.get('Vendedor')
    filtro_data_str = data.get('Data')

    filtro_data = None
    if filtro_data_str:
        try:
            filtro_data = datetime.strptime(filtro_data_str, '%d/%m/%Y').date()
        except ValueError:
            return jsonify({"erro": "Formato de data inválido. Use 'dd/mm/yyyy'."}), 400

    apostas_detalhadas = []
    apostas_premiadas_filtradas = []
    
    # --- Processamento das Apostas Principais ---
    query_apostas = Aposta.query

    if filtro_vendedor:
        query_apostas = query_apostas.filter(db.func.lower(Aposta.vendedor) == filtro_vendedor.lower())
    if filtro_data:
        query_apostas = query_apostas.filter(db.func.date(Aposta.data_atual) == filtro_data)

    todas_apostas_db = query_apostas.order_by(Aposta.id.desc()).all()

    for aposta_principal in todas_apostas_db:
        try:
            apostas_json = json.loads(aposta_principal.apostas)
        except json.JSONDecodeError:
            print(f"Erro ao decodificar JSON para o bilhete {aposta_principal.id}: {aposta_principal.apostas}")
            continue

        for aposta_individual in apostas_json:
            if len(aposta_individual) >= 6:
                modalidade_nome = aposta_individual[2]
                valor_apostado_individual = aposta_individual[4]
                vendedor_nome = aposta_principal.vendedor
                area_nome = aposta_principal.area
                extracao_nome = aposta_principal.extracao

                comissao_aplicada = 0.0
                normalized_area = normalize_string(area_nome)
                normalized_modalidade = normalize_string(modalidade_nome)
                normalized_vendedor = normalize_string(vendedor_nome)
                normalized_extracao = normalize_string(extracao_nome)

                comissao_especifica = ComissaoArea.query.filter(
                    db.func.lower(ComissaoArea.area) == normalized_area,
                    db.func.lower(ComissaoArea.modalidade) == normalized_modalidade,
                    db.func.lower(ComissaoArea.vendedor) == normalized_vendedor,
                    db.func.lower(ComissaoArea.extracao) == normalized_extracao,
                    ComissaoArea.ativar == 'sim'
                ).first()

                if comissao_especifica:
                    comissao_aplicada = float(comissao_especifica.comissao)
                else:
                    vendedor_obj = Vendedor.query.filter(
                        db.func.lower(Vendedor.nome) == normalized_vendedor
                    ).first()
                    if vendedor_obj and vendedor_obj.comissao is not None:
                        comissao_aplicada = float(vendedor_obj.comissao)

                valor_comissao = (valor_apostado_individual * comissao_aplicada) / 100

                apostas_detalhadas.append({
                    "bilhete_id": aposta_principal.id,
                    "data_aposta": aposta_principal.data_atual.strftime('%d/%m/%Y'),
                    "vendedor": vendedor_nome,
                    "extracao": extracao_nome,
                    "area": area_nome,
                    "modalidade": modalidade_nome,
                    "numeros": ", ".join(aposta_individual[1]),
                    "premio_str": aposta_individual[3],
                    "valor_apostado_individual": valor_apostado_individual,
                    "unidade_aposta": aposta_individual[5],
                    "valor_total_bilhete": aposta_principal.valor_total,
                    "comissao_percentual": comissao_aplicada,
                    "valor_comissao": valor_comissao
                })
            else:
                print(f"Formato inesperado da aposta individual no bilhete {aposta_principal.id}: {aposta_individual}")

    # --- Processamento das Apostas Premiadas ---
    query_premiadas = ApostaPremiada.query
    if filtro_vendedor:
        query_premiadas = query_premiadas.filter(db.func.lower(ApostaPremiada.vendedor) == filtro_vendedor.lower())
    if filtro_data:
        query_premiadas = query_premiadas.filter(db.func.date(ApostaPremiada.data_atual) == filtro_data)

    apostas_premiadas = query_premiadas.order_by(ApostaPremiada.id.desc()).all()

    for premiada in apostas_premiadas:
        apostas_premiadas_filtradas.append({
            "id": premiada.id,
            "numero_bilhete": premiada.numero_bilhete,
            "data_atual": premiada.data_atual.strftime('%d/%m/%Y'),
            "hora_atual": premiada.hora_atual.strftime('%H:%M'),
            "vendedor": premiada.vendedor,
            "extracao": premiada.extracao,
            "area": premiada.area,
            "valor_premio": premiada.valor_premio,
            "impresso": 'Sim' if premiada.impresso == 1 else 'Não',
            "pago": 'Sim' if premiada.pago == 1 else 'Não'
        })
    
    # --- Cálculo dos totais ---
    total_valor_apostas = sum(item['valor_apostado_individual'] for item in apostas_detalhadas)
    total_valor_comissoes = sum(item['valor_comissao'] for item in apostas_detalhadas)
    total_valor_premios = sum(float(p['valor_premio'].replace(',', '.')) for p in apostas_premiadas_filtradas)
    
    # --- Lógica para o cálculo do débito anterior (CORRIGIDO) ---
    debito_anterior = 0.00
    if filtro_vendedor:
        ultima_coleta = Coleta.query.filter(db.func.lower(Coleta.vendedor) == filtro_vendedor.lower()).order_by(Coleta.id.desc()).first()
        if ultima_coleta and ultima_coleta.valor_debito is not None and ultima_coleta.valor_coleta is not None:
            debito_anterior = ultima_coleta.valor_debito - ultima_coleta.valor_coleta
        
    # --- Cálculo dos totais finais ---
    lucro_total = total_valor_apostas - total_valor_premios - total_valor_comissoes
    debito_atual = total_valor_apostas - total_valor_premios + debito_anterior

    # --- Prepara a resposta JSON ---
    response = {
        "apostas_detalhadas": apostas_detalhadas,
        "apostas_premiadas": apostas_premiadas_filtradas,
        "totais": {
            "valor_total_apostas": f"R$ {total_valor_apostas:.2f}".replace('.', ','),
            "valor_total_comissoes": f"R$ {total_valor_comissoes:.2f}".replace('.', ','),
            "valor_total_premios": f"R$ {total_valor_premios:.2f}".replace('.', ','),
            "lucro": f"R$ {lucro_total:.2f}".replace('.', ','),
            "debito_atual": f"R$ {debito_atual:.2f}".replace('.', ','),
            "debito_anterior": f"R$ {debito_anterior:.2f}".replace('.', ',')
        }
    }
    
    return jsonify(response)

@aposta_route.route('/relatorio-financeiro', methods=['GET'])
def relatorio_agrupado_area():
    print("Iniciando a rota /relatorio-financeiro...")

    # Obtém os filtros da requisição
    data_inicial_str = request.args.get('data_inicial')
    data_final_str = request.args.get('data_final')
    extracao_filtro = request.args.get('extracao')
    area_filtro = request.args.get('area')
    vendedor_filtro = request.args.get('vendedor')
    modalidade_filtro = request.args.get('modalidade')

    print(f"Filtros recebidos: data_inicial={data_inicial_str}, data_final={data_final_str}, extracao={extracao_filtro}, area={area_filtro}, vendedor={vendedor_filtro}, modalidade={modalidade_filtro}")

    # Define as datas padrão se não forem fornecidas
    if not data_inicial_str:
        data_inicial_str = datetime.now().strftime('%Y-%m-%d')
    if not data_final_str:
        data_final_str = datetime.now().strftime('%Y-%m-%d')
    
    try:
        data_inicial = datetime.strptime(data_inicial_str, '%Y-%m-%d').date()
        data_final = datetime.strptime(data_final_str, '%Y-%m-%d').date()
        print(f"Datas de pesquisa formatadas: {data_inicial} a {data_final}")
    except ValueError as e:
        print(f"ERRO: Formato de data inválido. data_inicial={data_inicial_str}, data_final={data_final_str}. Erro: {e}")
        return "Erro no formato da data.", 400

    # Monta a consulta para as apostas principais
    try:
        query_apostas = Aposta.query.filter(
            Aposta.data_atual.between(data_inicial, data_final)
        )
        if extracao_filtro:
            query_apostas = query_apostas.filter(Aposta.extracao == extracao_filtro)
        if area_filtro:
            query_apostas = query_apostas.filter(Aposta.area == area_filtro)
        if vendedor_filtro:
            query_apostas = query_apostas.filter(Aposta.vendedor == vendedor_filtro)
        
        print(f"Consulta SQL para Apostas: {query_apostas.statement}")
        todas_apostas_db = query_apostas.order_by(Aposta.id.desc()).all()
        print(f"Número de apostas principais encontradas: {len(todas_apostas_db)}")
    except Exception as e:
        print(f"ERRO ao consultar apostas: {e}")
        return f"Erro ao consultar apostas: {e}", 500

    # Monta a consulta para as apostas premiadas
    try:
        query_premiadas = ApostaPremiada.query.filter(
            ApostaPremiada.data_atual.between(data_inicial, data_final)
        )
        if extracao_filtro:
            query_premiadas = query_premiadas.filter(ApostaPremiada.extracao == extracao_filtro)
        if area_filtro:
            query_premiadas = query_premiadas.filter(ApostaPremiada.area == area_filtro)
        if vendedor_filtro:
            query_premiadas = query_premiadas.filter(ApostaPremiada.vendedor == vendedor_filtro)
        
        print(f"Consulta SQL para Apostas Premiadas: {query_premiadas.statement}")
        todas_apostas_premiadas = query_premiadas.order_by(ApostaPremiada.id.desc()).all()
        print(f"Número de apostas premiadas encontradas: {len(todas_apostas_premiadas)}")
    except Exception as e:
        print(f"ERRO ao consultar apostas premiadas: {e}")
        return f"Erro ao consultar apostas premiadas: {e}", 500

    relatorio_por_area = {}

    # --- INÍCIO DA OTIMIZAÇÃO: PRÉ-CARREGAMENTO DE DADOS ---
    print("Pré-carregando dados de comissão para otimizar...")
    comissoes_por_chave = {}
    for comissao in ComissaoArea.query.filter(ComissaoArea.ativar == 'sim').all():
        chave = (
            normalize_string(comissao.area),
            normalize_string(comissao.modalidade),
            normalize_string(comissao.vendedor),
            normalize_string(comissao.extracao)
        )
        comissoes_por_chave[chave] = float(comissao.comissao)

    comissoes_vendedor = {
        normalize_string(v.nome): float(v.comissao)
        for v in Vendedor.query.all() if v.comissao is not None
    }
    print("Pré-carregamento concluído.")
    # --- FIM DA OTIMIZAÇÃO ---
    
    # Processa apostas e comissões
    print("Iniciando o processamento das apostas principais...")
    for aposta_principal in todas_apostas_db:
        print(f"Processando bilhete ID: {aposta_principal.id}, Vendedor: {aposta_principal.vendedor}, Área: {aposta_principal.area}")
        try:
            apostas_json = json.loads(aposta_principal.apostas)
        except json.JSONDecodeError:
            print(f"ERRO: JSON inválido para o bilhete {aposta_principal.id}. Dados: {aposta_principal.apostas}")
            continue

        for aposta_individual in apostas_json:
            if len(aposta_individual) >= 6:
                vendedor_nome = aposta_principal.vendedor
                area_nome = aposta_principal.area
                extracao_nome = aposta_principal.extracao
                modalidade_nome = aposta_individual[2]
                valor_apostado_individual = aposta_individual[4]
                
                if modalidade_filtro and modalidade_nome != modalidade_filtro:
                    continue

                comissao_aplicada = 0.0
                normalized_area = normalize_string(area_nome)
                normalized_modalidade = normalize_string(modalidade_nome)
                normalized_vendedor = normalize_string(vendedor_nome)
                normalized_extracao = normalize_string(extracao_nome)

                # --- INÍCIO DA LÓGICA OTIMIZADA ---
                chave_comissao = (normalized_area, normalized_modalidade, normalized_vendedor, normalized_extracao)
                
                if chave_comissao in comissoes_por_chave:
                    comissao_aplicada = comissoes_por_chave[chave_comissao]
                elif normalized_vendedor in comissoes_vendedor:
                    comissao_aplicada = comissoes_vendedor[normalized_vendedor]
                else:
                    print(f"AVISO: Nenhuma comissão encontrada para o vendedor '{vendedor_nome}'. Comissão padrão de 0% aplicada.")
                # --- FIM DA LÓGICA OTIMIZADA ---
                
                valor_comissao = (valor_apostado_individual * comissao_aplicada) / 100
                
                if area_nome not in relatorio_por_area:
                    relatorio_por_area[area_nome] = {'vendedores': {}, 'totais': {'apurado': 0, 'comissao': 0, 'premio': 0, 'liquido': 0, 'total': 0}}
                
                if vendedor_nome not in relatorio_por_area[area_nome]['vendedores']:
                    relatorio_por_area[area_nome]['vendedores'][vendedor_nome] = {'apurado': 0, 'comissao': 0, 'premio': 0}
                
                relatorio_por_area[area_nome]['vendedores'][vendedor_nome]['apurado'] += valor_apostado_individual
                relatorio_por_area[area_nome]['vendedores'][vendedor_nome]['comissao'] += valor_comissao
    
    print("Processamento de apostas principais finalizado.")

    # Processa os prêmios
    print("Iniciando o processamento das apostas premiadas...")
    for premiada in todas_apostas_premiadas:
        if premiada.pago == 1:
            if area_filtro and premiada.area != area_filtro: continue
            if vendedor_filtro and premiada.vendedor != vendedor_filtro: continue
            if extracao_filtro and premiada.extracao != extracao_filtro: continue
            
            vendedor_nome = premiada.vendedor
            area_nome = premiada.area
            
            try:
                valor_premio = float(str(premiada.valor_premio).replace(',', '.'))
            except (ValueError, TypeError) as e:
                print(f"ERRO: Valor de prêmio inválido para o ID {premiada.id}. Valor: {premiada.valor_premio}. Erro: {e}")
                continue
            
            if area_nome in relatorio_por_area and vendedor_nome in relatorio_por_area[area_nome]['vendedores']:
                relatorio_por_area[area_nome]['vendedores'][vendedor_nome]['premio'] += valor_premio
                print(f"Adicionando prêmio de R${valor_premio} ao vendedor '{vendedor_nome}' da área '{area_nome}'")
    
    print("Processamento de apostas premiadas finalizado.")

    # Coleta todos os valores únicos para os filtros
    extracao_valores = [ext.extracao for ext in Extracao.query.all()]
    area_valores = [area.regiao_area for area in Area.query.all()]
    vendedor_valores = [vend.nome for vend in Vendedor.query.all()]
    modalidade_valores = [mod.modalidade for mod in Modalidade.query.all()]
    
    filtros = {
        'data_inicial': data_inicial_str,
        'data_final': data_final_str,
        'extracao': extracao_filtro,
        'area': area_filtro,
        'vendedor': vendedor_filtro,
        'modalidade': modalidade_filtro
    }

    relatorio_final_agrupado = []
    total_geral_apurado = 0
    total_geral_comissao = 0
    total_geral_liquido = 0
    total_geral_premio = 0
    total_geral_total = 0
    total_vendedores = 0

    for area, dados_area in relatorio_por_area.items():
        vendedores_lista = []
        totais_area = {'apurado': 0, 'comissao': 0, 'liquido': 0, 'premio': 0, 'total': 0}

        for vendedor, dados_vendedor in dados_area['vendedores'].items():
            apurado = dados_vendedor['apurado']
            comissao = dados_vendedor['comissao']
            premio = dados_vendedor['premio']
            liquido = apurado - comissao
            total = liquido - premio
            
            vendedores_lista.append({
                'nome': vendedor,
                'apurado': apurado,
                'comissao': comissao,
                'liquido': liquido,
                'premio': premio,
                'total': total
            })

            totais_area['apurado'] += apurado
            totais_area['comissao'] += comissao
            totais_area['liquido'] += liquido
            totais_area['premio'] += premio
            totais_area['total'] += total
            total_vendedores += 1

        vendedores_lista.sort(key=lambda x: x['nome'])

        relatorio_final_agrupado.append({
            'area': area,
            'vendedores': vendedores_lista,
            'totais': totais_area
        })

        total_geral_apurado += totais_area['apurado']
        total_geral_comissao += totais_area['comissao']
        total_geral_liquido += totais_area['liquido']
        total_geral_premio += totais_area['premio']
        total_geral_total += totais_area['total']

    relatorio_final_agrupado.sort(key=lambda x: x['area'])

    print("Processamento de totais finalizado. Renderizando template...")
    return render_template('relatorio_agrupado.html',
                           relatorio_agrupado=relatorio_final_agrupado,
                           filtros=filtros,
                           extracao_valores=extracao_valores,
                           area_valores=area_valores,
                           vendedor_valores=vendedor_valores,
                           modalidade_valores=modalidade_valores,
                           total_geral_apurado=total_geral_apurado,
                           total_geral_comissao=total_geral_comissao,
                           total_geral_liquido=total_geral_liquido,
                           total_geral_premio=total_geral_premio,
                           total_geral_total=total_geral_total,
                           total_vendedores=total_vendedores)


@aposta_route.route('/api/bilhetes-por-filtro', methods=['POST'])
def get_bilhetes_por_filtro():
    """
    Busca e retorna os IDs dos bilhetes com base em dados de extração e data,
    recebidos no corpo de uma requisição JSON (método POST).
    
    Exemplo de JSON de entrada:
    {
      "Extracao": "Extração 1",
      "Data": "20-12-2025"
    }
    """
    try:
        # Tenta pegar os dados do JSON no corpo da requisição
        data = request.get_json()

        # 1. Validação de que o JSON foi enviado
        if not data:
            print("AVISO: Nenhuns dados JSON recebidos.")
            return jsonify({"error": "Requisição inválida. O corpo deve ser um JSON."}), 400

        # 2. Extrai os dados do JSON e valida a existência dos campos
        extracao_nome = data.get('Extracao')
        data_param = data.get('Data')

        if not extracao_nome or not data_param:
            print("AVISO: Campos 'Extracao' ou 'Data' estão faltando no JSON.")
            return jsonify({"error": "Os campos 'Extracao' e 'Data' são obrigatórios."}), 400
        
        print(f"DEBUG: Buscando bilhetes para Extração: '{extracao_nome}' e Data: '{data_param}'")

        # 3. Converte a data do formato DD-MM-YYYY para o formato YYYY-MM-DD
        try:
            dia, mes, ano = map(int, data_param.split('-'))
            data_obj = date(ano, mes, dia)
        except (ValueError, TypeError) as e:
            print(f"ERRO: Formato de data inválido. Esperado 'DD-MM-YYYY', recebido '{data_param}'. Erro: {e}")
            return jsonify({"error": f"Formato de data inválido. Use o formato DD-MM-YYYY."}), 400

        normalized_extracao = normalize_string(extracao_nome)

        # 4. Executa a consulta no banco de dados
        query = Aposta.query.with_entities(Aposta.id).filter(
            func.lower(Aposta.extracao) == normalized_extracao,
            Aposta.data_atual == data_obj
        )
        
        bilhetes = query.all()
        
        # 5. Extrai os IDs
        bilhete_ids = [bilhete.id for bilhete in bilhetes]
        
        print(f"DEBUG: Encontrados {len(bilhete_ids)} IDs de bilhetes.")

        # 6. Retorna a resposta JSON
        return jsonify({
            "success": True,
            "extracao": extracao_nome,
            "data": data_obj.strftime('%d/%m/%Y'),
            "bilhete_ids": bilhete_ids
        }), 200

    except Exception as e:
        # Lida com qualquer erro inesperado no processo
        print(f"ERRO FATAL: Falha ao buscar bilhetes por filtro. Erro: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}"}), 500
    
@aposta_route.route('/pagar-premio/<int:aposta_id>', methods=['PUT'])
def pagar_aposta_premiada(aposta_id):
    """
    Atualiza o status de pagamento de uma aposta premiada para 'pago' (1).
    Recebe o ID da aposta premiada pela URL.
    
    Exemplo de URL: /api/aposta-premiada/pagar/123
    """
    try:
        # 1. Busca a aposta premiada pelo ID fornecido na URL
        aposta_premiada = ApostaPremiada.query.filter_by(numero_bilhete=aposta_id).first()

        # 2. Verifica se a aposta foi encontrada
        if not aposta_premiada:
            print(f"AVISO: Aposta premiada com ID {aposta_id} não encontrada.")
            return jsonify({"error": "Aposta premiada não encontrada."}), 404

        # 3. Verifica se a aposta já está paga
        if aposta_premiada.pago == 1:
            print(f"AVISO: Aposta premiada com ID {aposta_id} já está marcada como paga.")
            return jsonify({"message": "Aposta já está paga."}), 200

        # 4. Atualiza o valor da coluna 'pago' para 1 e persiste no banco de dados
        aposta_premiada.pago = 1
        db.session.commit()
        
        print(f"DEBUG: Aposta premiada com ID {aposta_id} marcada como paga com sucesso.")

        # 5. Retorna uma resposta de sucesso
        return jsonify({
            "success": True,
            "message": "Aposta premiada marcada como paga com sucesso.",
            "aposta_id": aposta_id
        }), 200

    except Exception as e:
        # Lida com qualquer erro inesperado no processo
        db.session.rollback() # Garante que a transação é desfeita em caso de erro
        print(f"ERRO FATAL: Falha ao marcar aposta como paga. ID: {aposta_id} | Erro: {e}")
        return jsonify({"error": f"Erro interno do servidor: {e}"}), 500
