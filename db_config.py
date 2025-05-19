from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote_plus

db = SQLAlchemy()

def init_db(app):
    db_user = "dbsysbanca"
    db_password = quote_plus("Tns22062010@") 
    db_name = "dbsysbanca"
    db_host = "dbsysbanca.mysql.dbaas.com.br".strip()
    db_port = 3306

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)