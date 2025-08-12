from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import os
from urllib.parse import quote_plus

db = SQLAlchemy()
# dbsysbanca
def init_db(app):
    db_user = os.getenv("DB_USER", "clesperanca")
    db_password = quote_plus(os.getenv("DB_PASSWORD", "Tns22062010#"))
    db_name = os.getenv("DB_NAME", "clesperanca")
    db_host = os.getenv("DB_HOST", "clesperanca.mysql.dbaas.com.br")
    db_port = int(os.getenv("DB_PORT", 3306))

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ✅ Configurações importantes para o pool de conexões
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,  # ✅ Testa se a conexão está viva antes de usar
        "pool_size": 5,         # ✅ Ajuste conforme a necessidade da sua aplicação
        "max_overflow": 10,     # ✅ Conexões extras em picos de carga
        "pool_recycle": 28000   # ✅ Fecha e recria conexões após 28000 segundos (~8h), evita timeout do MySQL
    }

    db.init_app(app)
