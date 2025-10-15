from __future__ import annotations
import os, pathlib
from typing import Literal
import tomllib  # Python 3.11+
from dataclasses import dataclass

Env = Literal["DATA","DEV","PREPROD","PROD"]

@dataclass(frozen=True)
class DBSecrets:
    dbname: str
    host: str
    user: str
    password: str
    port: int = 5432

    def dsn_sqlalchemy(self) -> str:
        # pour SQLAlchemy psycopg v3
        return f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"

    def dsn_psycopg(self) -> str:
        # pour psycopg natif
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"

_ENV_TO_KEY = {
    "DATA":    "DB_DATA_SECRETS",
    "DEV":     "DB_DEV_SECRETS",
    "PREPROD": "DB_PREPROD_SECRETS",
    "PROD":    "DB_PROD_SECRETS",
}

def _default_secrets_path() -> pathlib.Path:
    return pathlib.Path.home() / ".config" / "quantfox" / "db_secrets.toml"

def load_db_secrets(env: Env | None = None) -> DBSecrets:
    env = (env or os.getenv("QF_ENV","DEV")).upper()
    if env not in _ENV_TO_KEY:
        raise ValueError(f"Unknown QF_ENV={env}")

    # 1) DSN direct via env (permet CI sans fichier)
    dsn_env = os.getenv(f"QF_DB_{env}_DSN")
    if dsn_env:
        # parse simple DSN si tu veux; sinon retourne un wrapper minimal
        userinfo = dsn_env.split("://",1)[-1].split("@")[0]
        user = userinfo.split(":")[0]
        return DBSecrets(dbname="", host="", user=user, password="")

    secrets_path = pathlib.Path(os.getenv("QF_DB_SECRETS_PATH", str(_default_secrets_path())))
    if not secrets_path.exists():
        raise FileNotFoundError(f"Secrets file not found: {secrets_path}")

    with open(secrets_path, "rb") as f:
        data = tomllib.load(f)

    key = _ENV_TO_KEY[env]
    block = data.get(key)
    if not block:
        raise KeyError(f"[{key}] missing in {secrets_path}")

    if env == "PROD" and os.getenv("QF_ALLOW_PROD") != "1":
        raise PermissionError("PROD blocked. Set QF_ALLOW_PROD=1 explicitly to enable.")

    return DBSecrets(**block)

def load_sqlalchemy_dsn(env: Env | None = None) -> str:
    env_s = (env or os.getenv("QF_ENV","DEV")).upper()
    dsn_env = os.getenv(f"QF_DB_{env_s}_DSN")
    if dsn_env:
        if env_s == "PROD" and os.getenv("QF_ALLOW_PROD") != "1":
            raise PermissionError("PROD blocked. Set QF_ALLOW_PROD=1 explicitly to enable.")
        return dsn_env
    return load_db_secrets(env).dsn_sqlalchemy()
