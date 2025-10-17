import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Final
from uuid import UUID

import sqlalchemy as sa

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from fastdup.vldbaccess.models import events
from fastdup.vl.common import logging_init
from fastdup.vl.utils.useful_decorators import log_exception_with_args, timed
from fastdup.vldbaccess import sql_template_utils
from fastdup.vldbaccess.base import (
    BaseDB, DatasetSourceType, SampleDataset, DatasetStatus, AccessOperation, SeverityCount, Severity
)
from fastdup.vldbaccess import image_embeddings
from fastdup.vldbaccess.connection_manager import get_session, get_async_session, get_engine, get_engine_dialect
from fastdup.vldbaccess.event_dao import EventDAO
from fastdup.vldbaccess.models.dataset import Dataset, DatasetCounters
from fastdup.vldbaccess.sql_template_utils import QueryModule

logger = logging_init.get_vl_logger(__name__)
_MINIMAL_ACCESS: Final[List[AccessOperation]] = [AccessOperation.LIST, AccessOperation.READ]


class AccessDAO(BaseDB):

    @staticmethod
    def list_users(dataset_id: UUID) -> dict[UUID, List[AccessOperation]]:
        with get_session() as session:
            return session.execute(sa.text(
                """
                SELECT subject_id, ARRAY_AGG(operation) AS operations
                FROM access
                WHERE object_id = :dataset_id
                GROUP BY subject_id;
                """
            ), {"dataset_id": dataset_id}).fetchall()

    @staticmethod
    def grant_access(
            dataset_id: UUID,
            user_id: UUID,
            ops: List[AccessOperation] = _MINIMAL_ACCESS
    ):
        with get_session(autocommit=True) as session:
            AccessDAO._grant_access(session, dataset_id, user_id, ops)

    @staticmethod
    @log_exception_with_args
    def revoke_access(
            dataset_id: UUID,
            user_id: UUID,
            ops: Optional[List[AccessOperation]] = None
    ):
        if ops is None:
            ops = list(AccessOperation)  # Set default to all operations
        with get_session(autocommit=True) as session:
            session.execute(sa.text(
                """
                DELETE FROM access
                WHERE
                    subject_id = :user_id
                    AND object_id = :dataset_id
                    AND operation = ANY(:ops);
                """
            ), {"user_id": user_id, "dataset_id": dataset_id, "ops": ops})
