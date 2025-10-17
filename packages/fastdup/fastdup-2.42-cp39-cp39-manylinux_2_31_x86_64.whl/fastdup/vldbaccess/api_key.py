from dataclasses import dataclass
from typing import Optional, Tuple
from uuid import UUID

import sqlalchemy as sa

from fastdup.vl.utils.useful_decorators import log_exception_with_args
from fastdup.vldbaccess.base import BaseDB
from fastdup.vldbaccess.connection_manager import get_session


@dataclass
class ApiCredentials:
    api_key: UUID
    encrypted_api_secret: str
    user_id: UUID


class ApiCredentialsDAO(BaseDB):

    @staticmethod
    @log_exception_with_args
    def upsert_api_key(api_credentials: ApiCredentials) -> UUID:
        with get_session(autocommit=True) as session:
            return session.execute(sa.text(
                """
                INSERT INTO api_keys (api_key, encrypted_api_secret, user_id)
                VALUES (:key, :secret, :user_id)
                ON CONFLICT (user_id) DO UPDATE SET
                    encrypted_api_secret = EXCLUDED.encrypted_api_secret,
                    api_key = EXCLUDED.api_key
                RETURNING user_id;
                """),
                {
                    'key': api_credentials.api_key,
                    'secret': api_credentials.encrypted_api_secret,
                    'user_id': api_credentials.user_id
                }
            ).one()[0]

    @staticmethod
    @log_exception_with_args
    def get_api_key(user_id: UUID) -> Optional[UUID]:
        with get_session() as session:
            row: Optional[tuple] = session.execute(
                sa.text("SELECT api_key FROM api_keys WHERE user_id = :user_id"),
                {"user_id": user_id}
            ).one_or_none()
        if row is None:
            return None
        return row[0]

    @staticmethod
    @log_exception_with_args
    def get_user_and_secret(api_key: str) -> Optional[Tuple[UUID, str]]:
        with get_session() as session:
            row = session.execute(
                sa.text("SELECT api_key, encrypted_api_secret, user_id FROM api_keys WHERE api_key = :api_key"),
                {"api_key": api_key}
            ).mappings().one_or_none()
        if row is None:
            return None
        return row['user_id'], row['encrypted_api_secret']
