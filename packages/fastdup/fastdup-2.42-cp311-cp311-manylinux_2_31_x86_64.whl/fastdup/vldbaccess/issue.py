import sqlalchemy as sa

from typing import List, Optional, Dict
from uuid import UUID

from pydantic import BaseModel, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from fastdup.vl.common.settings import Settings
from fastdup.vl.utils import formatting
from fastdup.vl.utils.useful_decorators import log_exception_with_args, timed
from fastdup.vldbaccess import sql_template_utils
from fastdup.vldbaccess.base import Severity
from fastdup.vldbaccess.cluster_model import ClusterType
from fastdup.vldbaccess.connection_manager import get_session, get_async_session
from fastdup.vldbaccess.exploration_sqls import ExplorationContext
from fastdup.vldbaccess.previews import get_previews
from fastdup.vldbaccess.sql_template_utils import QueryModule


class Issue(BaseModel):
    issue_id: UUID
    dataset_id: UUID
    display_name: str
    type_id: int
    type_display_name: str
    severity: Severity
    n_clusters: int
    n_child_clusters: int
    n_images: int
    n_objects: int
    root_cluster_id: UUID
    cluster_type: ClusterType
    previews: Optional[List[str]] = None
    preview_boxes: Optional[str] = None
    # calculated fields
    n_images_display_value: Optional[str] = None
    n_clusters_display_value: Optional[str] = None
    severity_display_name: Optional[str] = None

    @validator("n_images_display_value", always=True)
    def _n_images_display_value(cls, v, values, **kwargs):
        return formatting.sizeof_fmt(values['n_images'], suffix='', precision=0, k_size=1000)

    @validator("n_clusters_display_value", always=True)
    def _n_clusters_display_value(cls, v, values, **kwargs):
        return formatting.sizeof_fmt(values['n_clusters'], suffix='', precision=0, k_size=1000)

    @validator("severity_display_name", always=True)
    def _severity_display_name(cls, v, values, **kwargs):
        return values['severity'].display_name()

    @staticmethod
    @log_exception_with_args
    def from_dict_row(row: dict) -> 'Issue':
        return Issue(
            issue_id=row['id'],
            type_id=row['type_id'],
            dataset_id=row['dataset_id'],
            root_cluster_id=row['cluster_id'],
            cluster_type=ClusterType[row['type']],
            display_name=row['display_name'],
            type_display_name=row['type_display_name'],
            severity=Severity(row['severity']),
            n_clusters=row['n_clusters'] + 1,  # add the root cluster
            n_child_clusters=row['n_child_clusters'],
            n_images=row['n_images'],
            n_objects=row['n_objects'],
        )


class IssueDB:

    @staticmethod
    @log_exception_with_args
    async def get_by_dataset_id(
            session: AsyncSession,
            dataset_id: UUID,
            user_id: UUID,
            max_previews: int = 0
    ) -> List[Issue]:
        qr = await session.execute(sa.text("""
            SELECT
                dataset_issues.id,
                dataset_issues.type_id,
                dataset_issues.dataset_id,
                dataset_issues.cluster_id,
                dataset_issues.display_name,
                issue_type.severity,
                issue_type.name AS type_display_name,
                clusters.n_images,
                clusters.n_objects,
                clusters.n_clusters,
                clusters.n_child_clusters,
                clusters.type
            FROM
                dataset_issues,
                issue_type,
                clusters
            WHERE
                dataset_issues.dataset_id = :dataset_id
                AND dataset_issues.dataset_id = clusters.dataset_id
                AND dataset_issues.type_id = issue_type.id
                AND dataset_issues.cluster_id = clusters.id
            ;"""), {"dataset_id": dataset_id, "user_id": user_id})
        rows = qr.mappings().all()
        issues: List[Issue] = [Issue.from_dict_row(row) for row in rows]

        if max_previews > 0:
            cluster_ids: List[UUID] = [issue.root_cluster_id for issue in issues]
            previews: Dict[UUID, List[str]] = await get_previews(
                user_id, dataset_id, cluster_ids, max_previews, session)

            for issue in issues:
                issue.previews = previews.get(issue.root_cluster_id)

        return issues

    @staticmethod
    @log_exception_with_args
    @timed
    def get_by_entities(context: ExplorationContext) -> list[dict]:
        query = sql_template_utils.render(
            QueryModule.EXPLORATION, "get_issues_by_entities.jinja2", **context.dict()
        )
        with get_session() as session:
            rows: List[Dict] = session.execute(sa.text(query), context.dict()).mappings().all()

        return rows

    @staticmethod
    @log_exception_with_args
    def insert_issue(
            type_id: int,
            dataset_id: UUID,
            cluster_id: UUID,
            display_name: str,
            session: Session,
    ) -> UUID:
        issue_id: UUID = session.execute(sa.text(  # type: ignore
            """    
            INSERT INTO
                dataset_issues (type_id, dataset_id, cluster_id, display_name)
            VALUES
                (:type_id, :dataset_id, :cluster_id, :display_name)
            RETURNING 
                id
            ;"""), {"type_id": type_id, "dataset_id": dataset_id,
                    "cluster_id": cluster_id, "display_name": display_name}
        ).one()[0]
        return issue_id
