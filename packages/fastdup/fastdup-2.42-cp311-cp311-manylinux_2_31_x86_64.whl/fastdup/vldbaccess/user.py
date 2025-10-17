from typing import Optional, Tuple, List, Dict, Annotated
from uuid import UUID

from fastdup.vl.common.pydantic_helper import AppResponseModel, Omit
from fastdup.vl.utils.useful_decorators import log_exception_with_args
from fastdup.vldbaccess.base import BaseDB, AccessOperation
from fastdup.vldbaccess.connection_manager import get_session

import sqlalchemy as sa


# class Org(BaseModel):
#     org_id: Optional[UUID] = None
#     name: str = ''


class User(AppResponseModel):
    user_id: Optional[UUID] = None
    user_identity: Annotated[str, Omit()] = ''
    identity_provider: Annotated[str, Omit()] = ''
    email: Optional[str] = None
    name: Annotated[Optional[str], Omit()] = None
    avatar_uri: Optional[str] = None
    dataset_quota: Annotated[int, Omit()] = 10
    is_internal_user: Optional[bool] = False
    assume_role: Annotated[Optional[str], Omit()] = ''

    def __repr__(self):
        return self.name or self.email or self.user_identity

    def is_anonymous_user(self) -> bool:
        return self.user_identity == 'anonymous'

    @staticmethod
    @log_exception_with_args
    def from_db_dict(row: dict) -> 'User':
        return User(
            user_id=row['id'],
            user_identity=row['user_identity'],
            identity_provider=row['identity_provider'],
            email=row.get('email', None),
            name=row.get('name', None),
            avatar_uri=row.get('avatar_uri', None),
            dataset_quota=row.get('dataset_quota', 10),
            assume_role=row.get('assume_role', ''),
            is_internal_user=row.get('email') and row.get('email').endswith('@visual-layer.com')
        )


class UserDB(BaseDB):
    # @staticmethod
    # def _get_org_by_user_id(conn: Connection, user_id: UUID) -> Org:
    #     records: list = conn.execute("""
    #         SELECT
    #             id, name
    #         FROM
    #             org
    #         WHERE
    #             id in (SELECT org_id FROM users WHERE id = %s)
    #         ;""", (user_id,)).fetchall()
    #     if len(records) != 0:
    #         return

    @staticmethod
    def _get(
            user_id: Optional[UUID] = None,
            user_identity: Optional[str] = None,
            identity_provider: Optional[str] = None
    ) -> Optional[User]:
        if (user_id is None) and (user_identity is None and identity_provider is None):
            raise ValueError('either user_id or user_identity and identity_provider most be provided')
        query = """SELECT * FROM users """
        if user_id is not None:
            query += f"""WHERE id = :user_id """
        else:
            query += f"""WHERE user_identity = :user_identity AND identity_provider = :identity_provider """

        with get_session() as session:
            row: Optional[Dict] = session.execute(
                sa.text(query),
                {"user_id": user_id, "user_identity": user_identity, "identity_provider": identity_provider}
            ).mappings().one_or_none()
        if row is None:
            return None
        else:
            return User.from_db_dict(row)

    @classmethod
    @log_exception_with_args
    def get_by_id(cls, user_id: UUID) -> Optional[User]:
        return cls._get(user_id)

    @classmethod
    @log_exception_with_args
    def get_or_create(
            cls,
            user_identity: str,
            identity_provider: str,
            email: Optional[str] = None,
            name: Optional[str] = None,
            avatar_uri: Optional[str] = None,
    ) -> User:
        with get_session(autocommit=True) as session:
            ctx = {
                'user_identity': user_identity,
                'identity_provider': identity_provider,
                'email': email,
                'name': name,
                'avatar_uri': avatar_uri
            }
            # get
            user = cls._get(user_identity=user_identity, identity_provider=identity_provider)
            if user is None:
                user_row = session.execute(sa.text("""
                    INSERT INTO users (user_identity, identity_provider, email, name, avatar_uri)
                    VALUES (:user_identity, :identity_provider, :email, :name, :avatar_uri)
                    ON CONFLICT (user_identity, identity_provider) DO NOTHING
                    RETURNING *
                """), ctx).mappings().one()
                created = True
                session.commit()
                user: User = User.from_db_dict(user_row)
            else:
                created = False
            if created:
                sample_dataset_ids: Tuple[List[UUID], List[UUID]] = UserDB._get_sample_dataset_ids(
                    session)
                for sample_ds_id in sample_dataset_ids[0]:
                    UserDB._grant_access(session, sample_ds_id, user.user_id,
                                         [AccessOperation.READ, AccessOperation.LIST])
                for sample_ds_id in sample_dataset_ids[1]:
                    UserDB._grant_access(session, sample_ds_id, user.user_id, [AccessOperation.READ])
        return user

    @classmethod
    @log_exception_with_args
    def _get_system_user(cls) -> User:
        """
        This function is protected (starts with _) to make sure you know exactly what you are doing if calling it.
        It returns the system user with the access to all datasets.
        """
        return cls._get(user_identity='system', identity_provider='system')

    @classmethod
    @log_exception_with_args
    def get_anonymous_user(cls) -> Optional[User]:
        return cls._get(user_identity='anonymous', identity_provider='system')

    # @staticmethod
    # def delete(user: User) -> bool:
    #     conn: Connection
    #     with get_connection() as conn:
    #         status: str = conn.execute("""
    #             DELETE FROM
    #                 users
    #             WHERE
    #                 user_identity = %s
    #                 AND identity_provider = %s
    #             ;""", (user.user_identity, user.identity_provider)).statusmessage
    #
    #     return status == 'DELETE 1'

    @staticmethod
    def check_authorized_user(user: User, dataset_id: UUID, operations: List[AccessOperation]) -> bool:
        ctx = {"dataset_id": dataset_id, "user_id": user.user_id}
        with get_session() as session:
            authorized_operations = session.execute(sa.text(
                """
                -- direct access
                SELECT operation
                FROM access
                WHERE
                    object_id = :dataset_id
                    AND subject_id = :user_id
                UNION
                -- group-based access
                SELECT operation
                FROM users_to_groups, access
                WHERE
                    access.object_id = :dataset_id
                    AND access.subject_id = users_to_groups.group_id 
                    AND users_to_groups.user_id = :user_id
                """), ctx).scalars().all()
        return set(operations).issubset(set(authorized_operations))

    @staticmethod
    def get_by_email(user_email: str) -> Optional[UUID]:
        params = {'user_email': user_email}

        with get_session() as session:
            user_ids: list[UUID] = session.execute(sa.text(
                """
                    SELECT
                        id
                    FROM
                        users
                    WHERE email = :user_email
                """
            ), params).scalars().all()

            if not user_ids or len(user_ids) > 1:
                return None

            return user_ids[0]

    @staticmethod
    def get_image_usage(user_id: Optional[UUID] = None) -> int:
        params = {'user_id': user_id}

        with get_session() as session:
            image_usage: int = session.execute(sa.text("""
            SELECT 
                COALESCE(SUM(n_images), 0) 
            FROM 
                datasets
            WHERE 
                created_by = :user_id AND status NOT IN ('INITIALIZING', 'FATAL_ERROR')
            """), params).scalar()

        return image_usage

    @staticmethod
    def get_image_quota(user_id: Optional[UUID] = None) -> Optional[int]:
        params = {'user_id': user_id}

        with get_session() as session:
            image_quota: Optional[int] = session.execute(sa.text("""
            SELECT image_quota
            from users 
            where id = :user_id
            """), params).scalar()

        return image_quota

    @staticmethod
    def get_group_name(group_id: UUID) -> Optional[str]:
        params = {'group_id': group_id}

        with get_session() as session:
            group_name: Optional[str] = session.execute(sa.text("""
                    SELECT 
                        name
                    FROM 
                        user_groups
                    WHERE 
                        id = :group_id
                    """), params).scalar()

        return group_name
