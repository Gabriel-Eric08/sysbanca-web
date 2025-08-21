# corrige_descarregos.py

import sys
import os

# Ajusta o caminho de importação para encontrar a pasta 'models'
# Isso garante que o script funcione independente de onde for executado
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models.models import Aposta, Descarrego, CadastroDescarrego, Modalidade
from db_config import db
from datetime import datetime
import json
from sqlalchemy import func

# Esta função de normalização é necessária para replicar a lógica do seu endpoint
# Usando a função que remove todos os espaços, conforme você confirmou
# que funciona com o seu banco de dados.
def normalize_string(s):
    if not isinstance(s, str):
        return ""
    return s.lower().strip().replace(" ", "")

# Configuração mínima do Flask para inicializar o SQLAlchemy
app = Flask(__name__)

# Configuração do Banco de Dados
DB_USER = "dbsysbanca"
DB_PASSWORD = "Tns22062010#"
DB_HOST = "dbsysbanca.mysql.dbaas.com.br"
DB_PORT = 3306
DB_NAME = "dbsysbanca"

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def corrige_descarregos():
    with app.app_context():
        print("Iniciando a correção de descarregos...")
        
        # 1. Busca todas as apostas existentes
        apostas_para_corrigir = Aposta.query.order_by(Aposta.id).all()
        
        total_descarregos_gerados = 0
        total_apostas_processadas = 0

        for aposta_obj in apostas_para_corrigir:
            print(f"Processando aposta ID: {aposta_obj.id}...")
            
            try:
                # Carrega os dados da aposta a partir do JSON salvo
                apostas = json.loads(aposta_obj.apostas)
                
                descarregos_da_aposta = []
                
                for aposta in apostas:
                    numeros = aposta[1]
                    modalidade_nome = aposta[2]
                    premio_str = aposta[3]
                    valor_total_aposta = float(aposta[4])
                    unidade_aposta = float(aposta[5])
                    
                    modalidade_obj = Modalidade.query.filter_by(modalidade=modalidade_nome).first()
                    if not modalidade_obj:
                        print(f"  - Aviso: Modalidade '{modalidade_nome}' não encontrada. Pulando.")
                        continue
                    
                    # Normalize os valores para busca, removendo espaços e convertendo para minúsculas
                    normalized_area = normalize_string(aposta_obj.area)
                    normalized_extracao = normalize_string(aposta_obj.extracao)
                    normalized_modalidade_name = normalize_string(modalidade_nome)

                    limite_descarrego = None
                    
                    descarregos_cadastrados = CadastroDescarrego.query.filter(
                        func.FIND_IN_SET(normalized_area, func.REPLACE(CadastroDescarrego.areas, ' ', '')),
                        func.FIND_IN_SET(normalized_extracao, func.REPLACE(CadastroDescarrego.extracao, ' ', '')),
                        func.FIND_IN_SET(normalized_modalidade_name, func.REPLACE(CadastroDescarrego.modalidade, ' ', ''))
                    ).first()

                    if descarregos_cadastrados:
                        limite_descarrego = float(descarregos_cadastrados.limite)
                    else:
                        limite_descarrego = float(modalidade_obj.limite_descarrego) if modalidade_obj.limite_descarrego else 10_000_000_000

                    cotacao_utilizada = float(modalidade_obj.cotacao)
                    
                    for numero in numeros:
                        # Verifica se o descarrego já existe para evitar duplicação em execuções futuras
                        descarrego_ja_existe = Descarrego.query.filter_by(
                            bilhete=aposta_obj.id,
                            extracao=aposta_obj.extracao,
                            modalidade=modalidade_nome,
                            numeros=json.dumps([numero])
                        ).first()
                        
                        if descarrego_ja_existe:
                            print(f"  - Descarrego para o bilhete {aposta_obj.id}, número {numero} já existe. Pulando.")
                            continue

                        valor_excedente = 0
                        premio_excedente = 0
                        
                        # CRIA A LISTA DE MODALIDADES A SEREM VERIFICADAS
                        # Inclui ambas as variações de "Milhar e Centena"
                        modalidades_a_checar = [normalized_modalidade_name]
                        if normalized_modalidade_name in ['milharecentena', 'milharecenten']:
                            modalidades_a_checar = ['milhar', 'centena', 'milharecentena', 'milharecenten']

                        # FILTRO DINÂMICO PARA AS MODALIDADES
                        modalidade_filter = db.or_(*[db.func.lower(Descarrego.modalidade) == m for m in modalidades_a_checar])

                        # LÓGICA CORRIGIDA: VERIFICA SE O NÚMERO JÁ FOI DESCARREGADO EM QUALQUER OUTRO BILHETE,
                        # CONSIDERANDO AS MODALIDADES RELACIONADAS.
                        descarrego_existente_para_numero = Descarrego.query.filter(
                            modalidade_filter,
                            db.func.lower(Descarrego.extracao) == normalized_extracao,
                            db.func.lower(Descarrego.numeros).like(f'%"{numero}"%')
                        ).first()
                        
                        # ...aplica a regra de descarregar o valor total da aposta
                        if descarrego_existente_para_numero:
                            print(f"  - Descarrego existente para o número {numero}, bilhete {descarrego_existente_para_numero.bilhete}. Descarregando valor total.")
                            valor_excedente = unidade_aposta
                            premio_excedente = unidade_aposta * cotacao_utilizada
                        elif unidade_aposta > limite_descarrego:
                            # Se não existe e o valor excede o limite, descarrega apenas o excedente
                            valor_excedente = unidade_aposta - limite_descarrego
                            premio_excedente = valor_excedente * cotacao_utilizada
                        
                        if valor_excedente > 0:
                            descarregos_da_aposta.append(Descarrego(
                                bilhete=aposta_obj.id,
                                extracao=aposta_obj.extracao,
                                valor_apostado=unidade_aposta,
                                valor_excedente=valor_excedente,
                                numeros=json.dumps([numero]),
                                data=aposta_obj.data_atual,
                                modalidade=modalidade_nome,
                                premio_total=unidade_aposta * cotacao_utilizada,
                                premio_excedente=premio_excedente,
                                tipo_premio=premio_str
                            ))

                if descarregos_da_aposta:
                    db.session.add_all(descarregos_da_aposta)
                    db.session.commit()
                    print(f"  - COMMIT bem-sucedido. {len(descarregos_da_aposta)} descarrego(s) gerado(s).")
                    total_descarregos_gerados += len(descarregos_da_aposta)
                else:
                    print(f"  - NENHUM descarrego necessário.")

                total_apostas_processadas += 1

            except Exception as e:
                db.session.rollback()
                print(f"  - ERRO FATAL ao processar aposta ID {aposta_obj.id}: {str(e)}")
                raise # Re-lança o erro para parar a execução e mostrar a pilha completa
                
        print(f"\nProcessamento concluído.")
        print(f"Total de apostas processadas: {total_apostas_processadas}")
        print(f"Total de descarregos gerados: {total_descarregos_gerados}")

if __name__ == '__main__':
    corrige_descarregos()
