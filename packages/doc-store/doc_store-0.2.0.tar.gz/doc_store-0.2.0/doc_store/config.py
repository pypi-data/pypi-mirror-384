import os
import urllib.parse
import warnings

import yaml
from pydantic import BaseModel


def _read_config() -> dict:
    config_file = os.getenv("DOC_STORE_CONFIG")
    if config_file and not os.path.isfile(config_file):
        raise Exception(f"DocStore config file [{config_file}] not exists.")
    default_config_file = os.path.expanduser("~/doc-store.yaml")
    if not config_file and os.path.isfile(default_config_file):
        config_file = default_config_file
    if not config_file:
        warnings.warn(
            "DocStore config file not found. "
            f"The default config file is ~/doc-store.yaml ({default_config_file}). "
            "Use env [DOC_STORE_CONFIG] to specify the custom config file path if needed.",
        )
        return {}
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)
    if isinstance(config, dict):
        return config
    warnings.warn(f"DocStore config file [{config_file}] is empty or invalid.")
    return {}


def get_env(key: str, default: str | None = None) -> str:
    value = os.getenv(key)
    if value not in (None, ""):
        return value
    if default is not None:
        return default
    raise ValueError(f"Environment variable {key} is not set.")


class S3Profile(BaseModel):
    endpoint_url: str
    aws_access_key_id: str
    aws_secret_access_key: str
    addressing_style: str = "path"  # default to path style


class S3Config(BaseModel):
    profiles: dict[str, S3Profile] = {}
    buckets: dict[str, str] = {}  # bucket_name -> profile_name


class DBHost(BaseModel):
    host: str
    port: int


class DBConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 27017
    hosts: list[DBHost] = []
    username: str = "mongoadmin"
    password: str = "mypassword"
    database: str = "test"
    auth_source: str | None = None
    replica_set: str | None = None
    extra_options: dict[str, str] = {}

    @property
    def uri(self) -> str:
        hosts = config.db.hosts
        if not hosts:
            hosts = [DBHost(host=config.db.host, port=config.db.port)]
        hosts_str = ",".join(f"{h.host}:{h.port}" for h in hosts)

        username = config.db.username
        password = config.db.password
        password = urllib.parse.quote_plus(password)
        database = config.db.database

        options = {**config.db.extra_options}
        if config.db.auth_source:
            options["authSource"] = config.db.auth_source
        if config.db.replica_set:
            options["replicaSet"] = config.db.replica_set
        extra_options_str = "&".join(f"{k}={v}" for k, v in options.items())

        uri = f"mongodb://{username}:{password}@{hosts_str}/{database}"
        uri = f"{uri}?{extra_options_str}" if extra_options_str else uri
        return uri


class KafkaConfig(BaseModel):
    brokers: list[str] = []
    protocol: str | None = None
    mechanism: str | None = None
    username: str | None = None
    password: str | None = None
    topic: str = "test"


class ServerConfig(BaseModel):
    url: str | None = None


class Config(BaseModel):
    s3: S3Config = S3Config()
    db: DBConfig = DBConfig()
    kafka: KafkaConfig = KafkaConfig()
    server: ServerConfig = ServerConfig()


config = Config(**_read_config())


def debug_print():
    import json

    config_json = config.model_dump()
    print(json.dumps(config_json, indent=2, ensure_ascii=False))
    print("MongoDB URI:", config.db.uri)


if __name__ == "__main__":
    debug_print()
