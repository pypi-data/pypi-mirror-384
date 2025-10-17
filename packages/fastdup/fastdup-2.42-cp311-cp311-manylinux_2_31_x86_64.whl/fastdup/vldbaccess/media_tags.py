from datetime import datetime
from typing import Dict, Any, Optional, Sequence, List
from uuid import UUID
from pydantic import BaseModel

import sqlalchemy as sa
from sqlalchemy import RowMapping

from fastdup.vl.common import logging_helpers, utils
from fastdup.vl.common.settings import Settings
from fastdup.vl.utils.useful_decorators import timed
from fastdup.vldbaccess.base import BaseDB
from fastdup.vldbaccess.connection_manager import get_session, get_async_session
from fastdup.vldbaccess import sql_template_utils
from fastdup.vldbaccess.exploration_sqls import ExplorationContext
from fastdup.vldbaccess.sql_template_utils import QueryModule
from fastdup.vldbaccess.user import User


class TagSet(BaseModel):
    tags: List[Dict] = []

    def extend(self, other: 'TagSet') -> None:
        for tag in other.tags:
            if not any(t['id'] == tag['id'] for t in self.tags):
                self.tags.append(tag)

    def add_tags_from_rows_mapping(self, rows: List[RowMapping]) -> None:
        for row in rows:
            tag_id = row.get('id')
            if not any(tag['id'] == tag_id for tag in self.tags):
                new_tag = {'id': tag_id, 'name': row.get('name')}
                self.tags.append(new_tag)


class MediaTagsDB(BaseDB):
    BATCH_SIZE = 1000

    @staticmethod
    @timed
    def get_tags_for_media(user_id: UUID, media_id: UUID):
        sql = """
            SELECT tag_id, name FROM media_to_tags, tags
            WHERE media_id = :media_id 
            AND media_to_tags.tag_id = tags.id;
        """
        with get_session() as session:
            rows: Sequence[RowMapping] = session.execute(
                sa.text(sql), {'media_id': media_id, 'user_id': user_id}
            ).mappings().all()
        return [{'id': row['tag_id'], 'name': row['name']} for row in rows]

    @staticmethod
    @timed
    def get_tags_for_dataset(user_id: UUID, dataset_id: UUID):
        sql = """
            SELECT tag_id, name FROM media_to_tags, tags
            WHERE media_to_tags.dataset_id = :dataset_id 
            AND media_to_tags.tag_id = tags.id;            
        """
        with get_session() as session:
            rows: Sequence[RowMapping] = session.execute(
                sa.text(sql),
                {'dataset_id': dataset_id, 'user_id': user_id}).mappings().all()
        return [{'id': row['tag_id'], 'name': row['name']} for row in rows]

    @staticmethod
    @timed
    def get_tags_for_cluster(user_id: UUID, dataset_id: UUID, cluster_id: UUID) -> list[dict[str, Any]]:
        sql = """
            WITH media AS (
                SELECT image_id AS media_id FROM images_to_similarity_clusters WHERE cluster_id = :cluster_id
                UNION
                SELECT object_id AS media_id FROM objects_to_similarity_clusters WHERE cluster_id = :cluster_id
            )
            SELECT
                tag_id, name
            FROM
                media, media_to_tags, tags
            WHERE media.media_id =  media_to_tags.media_id
                AND media_to_tags.tag_id = tags.id
        """
        with get_session() as session:
            rows: Sequence[RowMapping] = session.execute(
                sa.text(sql), {'dataset_id': dataset_id, 'cluster_id': cluster_id, 'user_id': user_id}
            ).mappings().all()
        return [{'id': row['tag_id'], 'name': row['name']} for row in rows]

    @staticmethod
    @timed
    def add_tag(user_id, dataset_id, media_id, tag_id):
        add_statement = """
            INSERT INTO media_to_tags (media_id, dataset_id, tag_id) VALUES (:media_id, :dataset_id, :tag_id)
            ON CONFLICT (media_id, dataset_id, tag_id) DO NOTHING;
        """
        with get_session(autocommit=True) as session:
            session.execute(sa.text(add_statement), {"media_id": media_id, "dataset_id": dataset_id, "tag_id": tag_id})
        return MediaTagsDB.get_tags_for_media(user_id, media_id)

    @staticmethod
    @timed
    async def add_tag_to_cluster(
            context: ExplorationContext, tag_id: UUID, exclude_media_ids: Optional[list[UUID]] = None):
        async with get_async_session(autocommit=True) as session:
            ctx = context.dict() | {
                "exclude_media_ids": exclude_media_ids,
                "tag_id": tag_id,
            }
            query = sql_template_utils.render(
                QueryModule.EXPLORATION, "add_tag_to_cluster.jinja2", **ctx
            )
            logging_helpers.log_sql_query(__name__, "add_tag_to_cluster", query, ctx)
            await session.execute(sa.text(query), ctx)

    @staticmethod
    @timed
    async def remove_tag_from_cluster(
            context: ExplorationContext, tag_id: UUID, exclude_media_ids: Optional[list[UUID]] = None):
        async with get_async_session(autocommit=True) as session:
            ctx = context.dict() | {
                "exclude_media_ids": exclude_media_ids,
                "tag_id": tag_id,
            }
            query = (
                sql_template_utils
                .get_sql_templates_environment("exploration")
                .get_template("remove_tag_from_cluster.jinja2")
                .render(
                    Settings=Settings,
                    **ctx
                )
            )
            logging_helpers.log_sql_query(__name__, "remove_tag_to_cluster", query, ctx)
            await session.execute(sa.text(query), ctx)

    @staticmethod
    @timed
    async def get_tags_from_cluster(context: ExplorationContext, exclude_media_ids: Optional[list[UUID]] = None):
        async with get_async_session(autocommit=True) as session:
            ctx = context.dict() | {
                "exclude_media_ids": exclude_media_ids
            }
            query = (
                sql_template_utils
                .get_sql_templates_environment("exploration")
                .get_template("get_cluster_tags.jinja2")
                .render(
                    Settings=Settings,
                    **ctx
                )
            )
            logging_helpers.log_sql_query(__name__, "get_cluster_tags", query, ctx)

            tag_set = TagSet()
            res = await session.execute(sa.text(query), ctx)
            rows = res.mappings().all()
            tag_set.add_tags_from_rows_mapping(rows)

            return tag_set

    @staticmethod
    @timed
    def add_tag_to_multiple_media(user_id, dataset_id, media_ids, tag_id) -> None:
        statement = """
            INSERT INTO media_to_tags (media_id, dataset_id, tag_id, created_at) 
            VALUES (:media_id, :dataset_id, :tag_id, :created_at)
            ON CONFLICT (media_id, dataset_id, tag_id) DO NOTHING;
        """

        for batch in utils.iter_batches(
                media_ids, MediaTagsDB.BATCH_SIZE,
                func=lambda media_id: {"media_id": media_id, "dataset_id": dataset_id, "tag_id": tag_id,
                                       "created_at": datetime.utcnow()}
        ):
            MediaTagsDB.execute_batch_stmt(statement, batch)

    @staticmethod
    @timed
    def get_tags_from_multiple_media(dataset_id, media_ids) -> TagSet:
        statement = """
            SELECT tags.id, tags.name
            FROM media_to_tags
            JOIN tags
            ON media_to_tags.tag_id = tags.id 
            WHERE media_to_tags.dataset_id = :dataset_id 
            AND media_to_tags.media_id = :media_id
        """

        tag_set = TagSet()
        with get_session(autocommit=True) as session:
            for media_id in media_ids:
                res = session.execute(sa.text(statement), {"media_id": media_id, "dataset_id": dataset_id})
                rows = res.mappings().all()
                tag_set.add_tags_from_rows_mapping(rows)

        return tag_set

    @staticmethod
    @timed
    def remove_tag_from_multiple_media(user_id, dataset_id, media_ids, tag_id) -> None:
        statement = """
            DELETE FROM media_to_tags 
            WHERE media_id = :media_id 
            AND dataset_id = :dataset_id 
            AND tag_id = :tag_id;
        """

        for batch in utils.iter_batches(
                media_ids, MediaTagsDB.BATCH_SIZE,
                func=lambda media_id: {"media_id": media_id, "dataset_id": dataset_id, "tag_id": tag_id}
        ):
            MediaTagsDB.execute_batch_stmt(statement, batch)

    @staticmethod
    @timed
    def delete_tag(user_id, dataset_id, media_id, tag_id):
        statement = """
            DELETE FROM media_to_tags WHERE media_id = :media_id AND dataset_id = :dataset_id AND 
            tag_id = :tag_id;
        """
        with get_session(autocommit=True) as session:
            session.execute(sa.text(statement), {"media_id": media_id, "dataset_id": dataset_id, "tag_id": tag_id})
        return MediaTagsDB.get_tags_for_media(user_id, media_id)

    @staticmethod
    @timed
    def get_all_tags_created_after(timestamp) -> Sequence[RowMapping]:
        # cursor is the timestamp of the last tag in the previous page
        # so return all tags with timestamp > cursor
        statement = """
            SELECT * FROM media_to_tags WHERE created_at > :timestamp ORDER BY created_at ASC;
        """
        with get_session() as session:
            rows: Sequence[RowMapping] = session.execute(sa.text(statement), {"timestamp": timestamp}).mappings().all()
        return rows

    @staticmethod
    def explore_tags(dataset_id: UUID, user: User, media_original_uris: list[str]):
        context: ExplorationContext = ExplorationContext(
            dataset_id=dataset_id,
            user_id=user.user_id,
            user=user,
            select_dataset_id_from='flat_similarity_clusters')
        ctx = context.dict() | {"media_original_uris": media_original_uris}
        query = sql_template_utils.render(
            QueryModule.EXPLORATION,"explore_media_tags.jinja2", **ctx
        )
        with get_session() as session:
            logging_helpers.log_sql_query(__name__, "explore_tags", query, ctx)
            rows: Sequence[RowMapping] = session.execute(sa.text(query), ctx).mappings().all()
        return rows
