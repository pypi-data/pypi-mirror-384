import secrets
from datetime import datetime, timezone, timedelta

import jwt

from typing import Tuple
from uuid import uuid4, UUID

from cryptography.fernet import Fernet

import fastdup.vl.utils.aws_secrets
from fastdup.vl.common.settings import Settings
from fastdup.vldbaccess.api_key import ApiCredentials, ApiCredentialsDAO


def _get_storage_key() -> str:
    return fastdup.vl.utils.aws_secrets.get_secret(Settings.PG_SECRET, 'storage_key')


def create_and_store_api_credentials(user_id: UUID) -> Tuple[UUID, str]:
    api_key: UUID = uuid4()
    api_secret = secrets.token_urlsafe(64)
    storage_key: str = _get_storage_key()
    encrypted_api_secret: str = Fernet(storage_key.encode()).encrypt(api_secret.encode()).decode()
    ApiCredentialsDAO.upsert_api_key(ApiCredentials(api_key, encrypted_api_secret, user_id))
    return api_key, api_secret


def decrypt_api_secret(encrypted_api_secret: str) -> str:
    storage_key: str = _get_storage_key()
    api_secret: str = Fernet(storage_key.encode()).decrypt(encrypted_api_secret.encode()).decode()
    return api_secret


def init_session_encryption_key():
    if not Settings.DISABLE_AUTH:
        Settings.STORAGE_KEY = _get_storage_key()


def decrypt_session_id(encrypted_session_id: str):
    if Settings.DISABLE_AUTH:
        return encrypted_session_id
    else:
        return Fernet(Settings.STORAGE_KEY.encode()).decrypt(encrypted_session_id.encode()).decode()


def encrypt_session_id(session_id: str):
    if Settings.DISABLE_AUTH:
        return session_id
    else:
        return Fernet(Settings.STORAGE_KEY.encode()).encrypt(session_id.encode()).decode()


def get_jwt_token(api_key, api_secret, ttl: timedelta) -> str:
    header = {
        'alg': 'HS256',
        'typ': 'JWT',
        'kid': api_key,
    }
    payload = {
        'sub': api_key,
        'iat': datetime.now(tz=timezone.utc),
        'exp': datetime.now(tz=timezone.utc) + ttl,
        'iss': 'sdk'
    }
    return jwt.encode(payload=payload, key=api_secret, algorithm='HS256', headers=header)
