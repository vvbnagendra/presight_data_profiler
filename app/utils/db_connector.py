# Directory: app/utils/db_connector.py
import sqlalchemy

def get_sqlalchemy_engine(db_type, host, port, user, password, db_name):
    if db_type == "PostgreSQL":
        uri = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    elif db_type == "MySQL":
        uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
    else:
        raise ValueError("Unsupported DB type")
    return sqlalchemy.create_engine(uri)
