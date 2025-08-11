from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from sqlalchemy import func
from models.models import Aposta, AreaCotacao, Modalidade, Descarrego, CadastroDescarrego, ApostaExcluida, ApostaPremiada, ComissaoArea, Vendedor, Extracao, Area, Coleta
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
        vendedor = data.get('vendedor')

        data_agendada = None
        if pre_datar and data_agendada_str and data_agendada_str != "00/00/00":
            data_agendada = datetime.strptime(data_agendada_str, "%d/%m/%Y").date()

        data_atual = datetime.strptime(data_atual_str, "%d/%m/%Y").date()
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

            cotacao_utilizada = None
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

            premio_total_calculado = valor_total_aposta * cotacao_utilizada

            # Lógica de Descarrego: verifica o valor unitário de cada número da aposta
            if unidade_aposta > limite_descarrego:
                excedente_unitario = unidade_aposta - limite_descarrego
                premio_excedente_unitario = excedente_unitario * cotacao_utilizada

                for numero in numeros:
                    descarregos_para_salvar.append({
                        "bilhete_id": None,
                        "extracao": extracao,
                        "valor_apostado": unidade_aposta,  # Valor unitário apostado
                        "valor_excedente": excedente_unitario,
                        "numeros": [numero],  # Salva cada número individualmente
                        "data": datetime.now(),
                        "modalidade": modalidade_nome,
                        "premio_total": unidade_aposta * cotacao_utilizada,
                        "premio_excedente": premio_excedente_unitario,
                        "tipo_premio": premio_str
                    })

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
            vendedor=vendedor,
            data_atual=data_atual,
            hora_atual=hora_atual,
            valor_total=float(data.get('valor_total', 0)),
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
    todas_apostas_db = Aposta.query.order_by(Aposta.id.desc()).all()
    
    apostas_detalhadas = []
    for aposta_principal in todas_apostas_db:
        try:
            apostas_json = json.loads(aposta_principal.apostas)
        except json.JSONDecodeError:
            print(f"Erro ao decodificar JSON para o bilhete {aposta_principal.id}: {aposta_principal.apostas}")
            apostas_json = []

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

    apostas_premiadas = ApostaPremiada.query.order_by(ApostaPremiada.id.desc()).all()

    # --- Novas consultas para os selects ---
    vendedores = Vendedor.query.with_entities(Vendedor.nome).distinct().order_by(Vendedor.nome).all()
    # Extrai apenas os nomes e os converte para uma lista de strings
    vendedores_nomes = [v[0] for v in vendedores]

    modalidades = Modalidade.query.with_entities(Modalidade.modalidade).distinct().order_by(Modalidade.modalidade).all()
    modalidades_nomes = [m[0] for m in modalidades]

    extracoes = Extracao.query.with_entities(Extracao.extracao).distinct().order_by(Extracao.extracao).all()
    extracoes_nomes = [e[0] for e in extracoes]

    areas = Area.query.with_entities(Area.regiao_area).distinct().order_by(Area.regiao_area).all()
    areas_nomes = [a[0] for a in areas]
    # --- Fim das novas consultas ---

    debito_anterior = 0.00

    return render_template('relatorio_apostas.html', 
                           apostas=apostas_detalhadas,
                           apostas_premiadas=apostas_premiadas,
                           vendedores=vendedores_nomes,
                           modalidades=modalidades_nomes,
                           extracoes=extracoes_nomes,
                           areas=areas_nomes,
                           debito_anterior=debito_anterior)

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
    # Obtém os filtros da requisição
    data_inicial_str = request.args.get('data_inicial')
    data_final_str = request.args.get('data_final')
    extracao_filtro = request.args.get('extracao')
    area_filtro = request.args.get('area')
    vendedor_filtro = request.args.get('vendedor')

    # Define as datas padrão se não forem fornecidas
    if not data_inicial_str:
        data_inicial_str = datetime.now().strftime('%Y-%m-%d')
    if not data_final_str:
        data_final_str = datetime.now().strftime('%Y-%m-%d')

    data_inicial = datetime.strptime(data_inicial_str, '%Y-%m-%d').date()
    data_final = datetime.strptime(data_final_str, '%Y-%m-%d').date()

    # Monta a consulta para as apostas principais
    query_apostas = Aposta.query.filter(
        Aposta.data_atual.between(data_inicial, data_final)
    )
    if extracao_filtro:
        query_apostas = query_apostas.filter(Aposta.extracao == extracao_filtro)
    if area_filtro:
        query_apostas = query_apostas.filter(Aposta.area == area_filtro)
    if vendedor_filtro:
        query_apostas = query_apostas.filter(Aposta.vendedor == vendedor_filtro)
    
    todas_apostas_db = query_apostas.order_by(Aposta.id.desc()).all()

    # Monta a consulta para as apostas premiadas
    query_premiadas = ApostaPremiada.query.filter(
        ApostaPremiada.data_atual.between(data_inicial, data_final)
    )
    if extracao_filtro:
        query_premiadas = query_premiadas.filter(ApostaPremiada.extracao == extracao_filtro)
    if area_filtro:
        query_premiadas = query_premiadas.filter(ApostaPremiada.area == area_filtro)
    if vendedor_filtro:
        query_premiadas = query_premiadas.filter(ApostaPremiada.vendedor == vendedor_filtro)
    
    todas_apostas_premiadas = query_premiadas.order_by(ApostaPremiada.id.desc()).all()

    relatorio_por_area = {}
    
    # Processa apostas e comissões
    for aposta_principal in todas_apostas_db:
        try:
            apostas_json = json.loads(aposta_principal.apostas)
        except json.JSONDecodeError:
            print(f"Erro ao decodificar JSON para o bilhete {aposta_principal.id}")
            continue

        for aposta_individual in apostas_json:
            if len(aposta_individual) >= 6:
                vendedor_nome = aposta_principal.vendedor
                area_nome = aposta_principal.area
                extracao_nome = aposta_principal.extracao
                modalidade_nome = aposta_individual[2]
                valor_apostado_individual = aposta_individual[4]
                
                # Se houver filtro de modalidade e não corresponder, pula
                if request.args.get('modalidade') and modalidade_nome != request.args.get('modalidade'):
                    continue

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
                
                if area_nome not in relatorio_por_area:
                    relatorio_por_area[area_nome] = {'vendedores': {}, 'totais': {'apurado': 0, 'comissao': 0, 'premio': 0, 'liquido': 0, 'total': 0}}
                
                if vendedor_nome not in relatorio_por_area[area_nome]['vendedores']:
                    relatorio_por_area[area_nome]['vendedores'][vendedor_nome] = {'apurado': 0, 'comissao': 0, 'premio': 0}
                
                relatorio_por_area[area_nome]['vendedores'][vendedor_nome]['apurado'] += valor_apostado_individual
                relatorio_por_area[area_nome]['vendedores'][vendedor_nome]['comissao'] += valor_comissao

    # Processa os prêmios
    for premiada in todas_apostas_premiadas:
        if premiada.pago == 1:
            if area_filtro and premiada.area != area_filtro: continue
            if vendedor_filtro and premiada.vendedor != vendedor_filtro: continue
            if extracao_filtro and premiada.extracao != extracao_filtro: continue
            
            vendedor_nome = premiada.vendedor
            area_nome = premiada.area
            valor_premio = float(premiada.valor_premio.replace(',', '.'))
            
            if area_nome in relatorio_por_area and vendedor_nome in relatorio_por_area[area_nome]['vendedores']:
                relatorio_por_area[area_nome]['vendedores'][vendedor_nome]['premio'] += valor_premio
    
    # ... (o restante do código para calcular os totais e formatar a lista final é o mesmo)

    # Coleta todos os valores únicos para os filtros
    extracao_valores = [ext.extracao for ext in Extracao.query.all()]
    area_valores = [area.regiao_area for area in Area.query.all()]
    vendedor_valores = [vend.nome for vend in Vendedor.query.all()]
    modalidade_valores = [mod.modalidade for mod in Modalidade.query.all()]
    
    # Adicione a variável de filtros selecionados para manter o estado no HTML
    filtros = {
        'data_inicial': data_inicial_str,
        'data_final': data_final_str,
        'extracao': extracao_filtro,
        'area': area_filtro,
        'vendedor': vendedor_filtro,
        'modalidade': request.args.get('modalidade') # Adiciona o filtro de modalidade
    }

    # Calcula os totais finais para o relatório
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