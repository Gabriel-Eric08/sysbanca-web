from db_config import db

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)


class Pessoa(db.Model):
    __tablename__ = 'tblpessoa'
    nome = db.Column(db.String(20), primary_key=True)
    sobrenome = db.Column(db.String(20), nullable=False)


class Area(db.Model):
    __tablename__ = 'tb_area'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    regiao_area = db.Column('RegiaoArea', db.String(20), nullable=False)
    desc_area = db.Column('DescArea', db.String(20), nullable=False)
    ativar_area = db.Column('AtivarArea', db.Text, nullable=False)


class AreaCotacao(db.Model):
    __tablename__ = 'tb_AreaCotacao'
    id = db.Column('idCotArea', db.Integer, primary_key=True, autoincrement=True)
    area = db.Column(db.String(55), nullable=False)
    extracao = db.Column(db.String(25), nullable=False)
    modalidade = db.Column(db.String(25), nullable=False)
    cotacao = db.Column(db.Integer, nullable=False)
    ativar_area_cotacao = db.Column('AtivarAreaCotacao',db.String(5), nullable=False)


class AreaLimite(db.Model):
    __tablename__ = 'tb_AreaLimite'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    area_limite = db.Column(db.String(15), nullable=False)
    extracao_area_limite = db.Column(db.String(15), nullable=False)
    modalidade_area_limite = db.Column(db.String(15), nullable=False)
    limite_area_palpite = db.Column(db.Integer, nullable=False)


class ColetaVendedor(db.Model):
    __tablename__ = 'tb_ColetaVendedor'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    data_inicial = db.Column(db.Date, nullable=False)
    data_final = db.Column(db.Date, nullable=False)
    area_coleta = db.Column(db.String(15), nullable=False)
    coletor = db.Column(db.String(15), nullable=False)
    coleta_vendedor = db.Column(db.String(15), nullable=False)
    tipo_coleta = db.Column(db.Text, nullable=False)
    status = db.Column(db.Text, nullable=False)


class Coletor(db.Model):
    __tablename__ = 'tb_coletor'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_coletor = db.Column(db.String(15), nullable=False)
    area = db.Column(db.String(15), nullable=False)
    login = db.Column(db.String(10), nullable=False)
    senha = db.Column(db.String(10), nullable=False)
    ativar_coletor = db.Column(db.Text, nullable=False)


class Extracao(db.Model):
    __tablename__ = 'tb_extracao'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    extracao = db.Column(db.String(30), nullable=False)
    fechamento = db.Column(db.Time, nullable=False)
    premiacao = db.Column(db.Integer, nullable=False)
    dias_extracao = db.Column('DiasExtracao', db.String(100), nullable=False)
    ativo = db.Column(db.String(5), nullable=False)


class Modalidade(db.Model):
    __tablename__ = 'tb_modalidade'
    modalidade = db.Column(db.String(15), primary_key=True)
    unidade = db.Column(db.Integer, nullable=False)
    limite_por_aposta = db.Column('LimitePorAposta', db.Integer, nullable=False)
    limite_por_jogo = db.Column('LimitePorJogo', db.Integer, nullable=False)
    cotacao = db.Column('cotacao', db.Float, nullable=False)
    ativar_area = db.Column('ativar_area', db.Text, nullable=False)

class Operador(db.Model):
    __tablename__ = 'tb_operador'
    id = db.Column('IdOperador', db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column('nome', db.Text, nullable=False)
    regiao = db.Column('regiao', db.Text, nullable=False)
    ativo = db.Column('ativo',db.Text, nullable=False)
    area = db.Column('area', db.String(15), nullable=False)
    login = db.Column('login',db.String(15), nullable=False)
    senha = db.Column('senha', db.String(15), nullable=False)
    comissao = db.Column('comissao', db.Integer, nullable=True, default=0)
    cancelar_poule = db.Column('CancelarPoule', db.Text, nullable=True, default='')
    exibe_comissao = db.Column('ExibeComissao', db.Text, nullable=True, default='')
    limite_venda = db.Column('LimiteVenda', db.Integer, nullable=True, default=0)
    premiacao = db.Column('premiacao', db.Text, nullable=True, default='')  # default string vazia
    tipo_limite = db.Column('TipoLimite', db.Text, nullable=True, default='')
    grade = db.Column(db.String(15), nullable=True, default='')
    teste = db.Column(db.Text, nullable=True, default='')
    comissao_retida = db.Column('ComissaoRetida', db.String(10), nullable=True, default='')
    serial_maquina = db.Column('SerialMaquina', db.String(25), nullable=True, default='')


class Regiao(db.Model):
    __tablename__ = 'tb_regiao'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    regiao = db.Column('regiao', db.String(20), nullable=False)
    desc_regiao = db.Column('desc_regiao', db.String(20), nullable=True)
    ativo = db.Column('Ativo', db.Boolean, nullable=False)


class Resultado(db.Model):
    __tablename__ = 'tb_resultados'

    id = db.Column('ID', db.Integer, primary_key=True, autoincrement=True)
    extracao = db.Column(db.String(255), nullable=True)
    data = db.Column(db.DateTime, nullable=False)
    premio_1 = db.Column(db.Integer, nullable=False)
    premio_2 = db.Column(db.Integer, nullable=False)
    premio_3 = db.Column(db.Integer, nullable=False)
    premio_4 = db.Column(db.Integer, nullable=False)
    premio_5 = db.Column(db.Integer, nullable=False)
    premio_6 = db.Column(db.Integer, nullable=False)
    premio_7 = db.Column(db.Integer, nullable=False)
    premio_8 = db.Column(db.Integer, nullable=False)
    premio_9 = db.Column(db.Integer, nullable=False)
    premio_10 = db.Column(db.Integer, nullable=False)


class Venda(db.Model):
    __tablename__ = 'tb_venda'
    id = db.Column('IdVenda', db.Integer, primary_key=True, autoincrement=True)
    extracao = db.Column(db.String(25), nullable=False)
    modalidade = db.Column(db.String(25), nullable=False)
    apostas = db.Column(db.Integer, nullable=False)
    valor_aposta = db.Column('ValorAposta', db.Integer, nullable=False)
    premio = db.Column(db.Integer, nullable=False)
    valor_unitario_aposta = db.Column('ValorUnitarioAposta', db.Integer, nullable=False)
    valor_total_aposta = db.Column('ValorTotalAposta', db.Integer, nullable=False)
    valor_total_poule = db.Column('ValorTotalPoule', db.Integer, nullable=False)

class User(db.Model):
    __tablename__='tb_users'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column('nome', db.String(25), nullable=False)
    username = db.Column('username', db.String(25), nullable=False)
    senha = db.Column('senha', db.String(25), nullable=False)
    serial = db.Column('serial', db.String(25), nullable=False)