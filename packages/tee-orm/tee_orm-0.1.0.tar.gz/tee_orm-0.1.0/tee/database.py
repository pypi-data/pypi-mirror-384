from typing import Any, Dict


class MysqlDatabase:
    def __init__(self, host: str, port: int, user: str, password: str, database: str, ssl: Any = None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.ssl = ssl


db: Dict[str, MysqlDatabase] = {}


def set_default_db(host: str, port: int, user: str, password: str, database: str):
    global db
    db["default"] = MysqlDatabase(host, port, user, password, database)


def get_default_db() -> MysqlDatabase:
    return db["default"]


def set_db(name: str, host: str, port: int, user: str, password: str, database: str, ssl: Any = None):
    if name == "default":
        raise ValueError('Database name "default" is reserved for the default database.')
    global db
    db[name] = MysqlDatabase(host, port, user, password, database, ssl)


def get_db(name: str) -> MysqlDatabase:
    return db[name]
