import sqlalchemy as sa

from typing import List, Optional, Dict
from uuid import UUID

from pydantic import BaseModel, validator

from fastdup.vl.utils.useful_decorators import log_exception_with_args
from fastdup.vldbaccess.base import Severity
from fastdup.vldbaccess.connection_manager import get_session


class IssueType(BaseModel):
    id: int
    name: str
    severity: Severity
    severity_display_name: Optional[str] = None

    @classmethod
    @validator("severity_display_name", always=True)
    def _severity_display_name(cls, v, values, **kwargs) -> str:
        return values['severity'].display_name()

    @staticmethod
    def from_dict_row(row: dict) -> 'IssueType':
        return IssueType(
            id=row['id'],
            name=row['name'],
            severity=Severity(row['severity']),
        )

    def __hash__(self):  # make hashable BaseModel subclass
        return hash((type(self),) + tuple(self.__dict__.values()))


class IssueTypeDal:
    @staticmethod
    @log_exception_with_args
    def get_issue_types() -> List[IssueType]:
        with get_session() as session:
            rows: List[Dict] = session.execute(sa.text("""
                SELECT
                    id,
                    name,
                    severity
                FROM
                    issue_type
                ;""")).mappings().all()

        return [IssueType.from_dict_row(row) for row in rows]

    @staticmethod
    @log_exception_with_args
    def get_image_count_by_issue_type(
            issue_type_id: int,
            dataset_id: UUID,
            user_id: UUID
    ) -> int:
        with get_session() as session:
            return session.execute(sa.text("""
                SELECT DISTINCT
                    COUNT(image_id)
                FROM
                    image_issues
                WHERE
                    type_id = :issue_type_id
                    AND dataset_id = :dataset_id
                ;"""), {"issue_type_id": issue_type_id, "dataset_id": dataset_id, "user_id": user_id}
             ).one()[0]
