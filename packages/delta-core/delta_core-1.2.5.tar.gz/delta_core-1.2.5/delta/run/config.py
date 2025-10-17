import re
from typing import Annotated

from pydantic import (Field, HttpUrl, PostgresDsn,
                      UrlConstraints, field_validator)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from rsa import PublicKey, PrivateKey


SQLiteUrl = Annotated[
    MultiHostUrl,
    UrlConstraints(
        host_required=False,
        allowed_schemes=['sqlite', 'sqlite3'],
    )
]


def format_pem_key(key: str, key_type: str) -> str:

    pem_header_footer_regex = (rf'(-----BEGIN RSA '
                               rf'{key_type} KEY-----)(.+)(-----END RSA '
                               rf'{key_type} KEY-----)')
    matches = re.match(pem_header_footer_regex, key)

    if matches:
        pem_content = matches.group(2)
        formatted_pem_content = '\n'.join(
            [pem_content[i:i+64] for i in range(0, len(pem_content), 64)])
        return (f"{matches.group(1)}\n"
                f"{formatted_pem_content}\n{matches.group(3)}")
    else:
        raise ValueError(f"The {key_type.lower()} key string does not "
                         f"match the expected PEM format.")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_prefix='DELTA_',
    )

    # Deltatwin Run
    gss_api_url: HttpUrl
    run_limit: int = Field(default=10)
    eviction_active: bool = Field(default=False)
    eviction_keep_period: int = Field(default=48)
    database_url: SQLiteUrl | PostgresDsn = Field(
        default="sqlite:///.delta-run.db?check_same_thread=false"
    )
    database_show_sql: bool = Field(default=False)
    page_limit: int = Field(default=100)
    public_key: str
    private_key: str

    # DeltaTwin container image registry
    image_repo_hostname: str
    image_repo_username: str
    image_repo_password: str

    # Keycloak
    socketio_adapter_url: str
    keycloak_jwks_url: HttpUrl

    # DeltaTwin Run output storage
    s3_endpoint: str
    s3_region: str
    s3_access_key: str
    s3_secret_access_key: str
    s3_bucket: str

    # kubernetes executor
    k8s_context: str
    k8s_namespace: str
    k8s_cluster_name: str
    k8s_cluster_cert_auth: str
    k8s_cluster_server: str
    k8s_user_name: str
    k8s_user_cli_cert: str
    k8s_user_cli_key: str

    @field_validator('public_key')
    def decode_public_key(cls, v: str) -> PublicKey:
        formatted_pem_key = format_pem_key(v, 'PUBLIC')
        return PublicKey.load_pkcs1(
            formatted_pem_key.encode('utf-8'), format='PEM')

    @field_validator('private_key')
    def decode_private_key(cls, v: str) -> PrivateKey:
        formatted_pem_key = format_pem_key(v, 'PRIVATE')
        return PrivateKey.load_pkcs1(
            formatted_pem_key.encode('utf-8'), format='PEM')
