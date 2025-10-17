import asyncio
import dataclasses
import math
import time as python_time
from datetime import datetime, timedelta, time
from typing import Optional
from uuid import UUID

import numpy as np
import sqlalchemy as sa
from starlette.datastructures import URL

from fastdup.vl.common import logging_helpers
from fastdup.vl.common.logging_init import get_vl_logger

from fastdup.vl.common.settings import Settings
from fastdup.vl.utils import formatting
from fastdup.vl.utils.useful_decorators import timed
from fastdup.vldbaccess import sql_template_utils
from fastdup.vldbaccess.cluster_model import ClusterType
from fastdup.vldbaccess.connection_manager import get_async_session, get_async_engine, get_engine_dialect
from fastdup.vldbaccess.models.dataset import Dataset
from fastdup.vldbaccess.models.exploration_context import ExplorationContext
from fastdup.vldbaccess.models.export_info import (
    ExportInfo, GeneralExportInfo, MetadataExportInfo, MediaType, MetadataType, ExportTask,
    ExportTaskStatus, MetadataPropertiesObjects, MetadataPropertiesLabels, ImageExportInfo, MetadataPropertiesIssues)
from fastdup.vldbaccess.sql_template_utils import QueryModule
from fastdup.vldbaccess.user import User


logger = get_vl_logger(__name__)

USE_STREAMING_DATA_FROM_SQL = False  # streaming performance seems inferior
SOURCE_DISPLAY_NAME = {
    "VL": "Visual Layer",
    "USER": "User",
}


@dataclasses.dataclass
class ExportProgressService:
    export_task_id: UUID
    include_images: bool = False
    download_images: int = 0
    total_images: int = Settings.MAX_NUM_OF_IMAGES_TO_EXPORT
    metadata_records: int = 0
    metadata_records_total: Optional[int] = None
    _last_status: ExportTaskStatus = ExportTaskStatus.INIT
    _update_progress_task: Optional[asyncio.Task] = None

    def __repr__(self) -> str:
        return (f"ExportProgress: {self.export_task_id} {self._last_status} {self.metadata_records} "
                f"{self.download_images} Progress: {self._progress()}")

    def _metadata_progress(self) -> float:
        if self.metadata_records_total:
            return self.metadata_records / self.metadata_records_total
        elif self.metadata_records:
            return self.metadata_records / (self.metadata_records + math.log2(self.metadata_records))
        else:
            return 0.0

    def _download_progress(self) -> float:
        if self.include_images:
            return self.download_images / self.total_images
        else:
            return 1.0

    def _progress(self) -> float:
        return np.average(
            [self._metadata_progress(), self._download_progress()],
            weights=[0.5, int(self.include_images)]
        ) * 100.0  # render as percent

    async def update_progress(self, status: Optional[ExportTaskStatus] = None, progress=None, download_uri=None):
        if status is not None:
            self._last_status = status
        logger.debug("Export task progress: %s" % self)
        await update_export_task_in_db(
            self.export_task_id,
            self._last_status,
            progress=progress or self._progress(),
            download_uri=download_uri
        )

    async def _create_update_progress_task(self):
        while self._last_status not in (ExportTaskStatus.FAILED, ExportTaskStatus.COMPLETED):
            await self.update_progress()
            await asyncio.sleep(5)

    async def create_update_progress_task(self):
        self._update_progress_task = asyncio.create_task(
            self._create_update_progress_task()
        )

    async def stop_update_progress_task(self):
        self._update_progress_task.cancel()


def concat_uuids(u1: UUID, u2: UUID) -> UUID:
    return UUID(((u1.int + u2.int) % (2 ** 128)).to_bytes(16, "big").hex())


async def _stream_query_results(
        query, ctx, export_progress_service: Optional[ExportProgressService] = None
):
    t0 = python_time.monotonic()
    if USE_STREAMING_DATA_FROM_SQL and get_engine_dialect() == "postgresql":
        async with (get_async_engine()).connect() as conn:
            async_result = await conn.stream(sa.text(query), ctx)
            async for row in async_result.mappings():
                if export_progress_service is not None:
                    export_progress_service.metadata_records += 1
                yield row
    else:
        async with get_async_session() as session:
            result = await session.execute(sa.text(query), ctx)
            # TODO: as implemented this might make the progress status decrease,
            # if export_progress_service is not None:
            #     export_progress_service.metadata_records_total = (
            #         (export_progress_service.metadata_records_total or 0) + result.rowcount
            #     )
            for row in result.mappings().all():
                if export_progress_service is not None:
                    export_progress_service.metadata_records += 1
                yield row
                await asyncio.sleep(0)
    if export_progress_service is not None:
        await export_progress_service.update_progress()

@timed
async def _export_info_images(
    ctx: dict, base_url: URL, export_progress_service: Optional[ExportProgressService] = None
) -> dict[UUID, ImageExportInfo]:
    dataset_id = ctx["dataset_id"]
    media: dict[UUID, ImageExportInfo] = {}
    query = sql_template_utils.render(
        QueryModule.EXPLORATION,
        f"export/export_medias_images.jinja2", expend_selection=True, **ctx,
    )
    with logging_helpers.log_sql_query_time(__name__, "export_medias_images", query, ctx, ):
        async for row in _stream_query_results(query, ctx, export_progress_service):
            metadata_items = []
            metadata = row["metadata"] or {}
            video = metadata.get("video")
            frame_timestamp = metadata.get("frame_timestamp")
            if frame_timestamp and isinstance(frame_timestamp, float):
                frame_timestamp_ = (datetime.min + timedelta(seconds=frame_timestamp)).time()
            elif frame_timestamp and isinstance(frame_timestamp, str):
                frame_timestamp_ = time.fromisoformat(frame_timestamp)
            else:
                frame_timestamp_ = None

            if video:
                media_type = MediaType.VIDEO
                metadata_items.append(
                    MetadataExportInfo(
                        id=row["image_id"],
                        media_id=row["image_id"],
                        type=MetadataType.VIDEO_INFO,
                        properties={
                            "video_name": video,
                            "frame_timestamp": frame_timestamp_
                        }
                    )
                )
            else:
                media_type = MediaType.IMAGE
            image_id = row["image_id"]
            media[row["media_id"]] = ImageExportInfo(
                media_id=image_id,
                image_id=image_id,
                media_type=media_type,
                file_name=row["image_original_uri"].split("/")[-1],
                file_path=row["image_original_uri"],
                cluster_id=row["cluster_id"],
                file_size=formatting.sizeof_fmt(row["image_file_size"]),
                height=row["image_height"],
                width=row["image_width"],
                url=str(base_url.replace(
                    path=f"/dataset/{dataset_id}/data/image/{image_id}", port=Settings.WEBSERVER_PORT
                )),
                download_url=row["image_uri"],
                metadata_items=metadata_items
            )
        return media


@timed
async def _export_info_objects(
        ctx: dict, base_url: URL, export_progress_service: Optional[ExportProgressService] = None
) -> dict[UUID, MetadataExportInfo]:
    dataset_id = ctx["dataset_id"]
    metadata: dict[UUID, MetadataExportInfo] = {}
    query = sql_template_utils.render(
        QueryModule.EXPLORATION,
        f"export/export_medias_objects.jinja2", **ctx,
    )
    with logging_helpers.log_sql_query_time(__name__, "export_medias", query, ctx, ):
        async for row in _stream_query_results(query, ctx, export_progress_service):
            image_id = row["image_id"]
            media_id = row["media_id"]
            metadata[row["media_id"]] = MetadataExportInfo(
                id=row["media_id"],
                type=MetadataType.OBJECT_LABEL,
                media_id=row["image_id"],
                properties=MetadataPropertiesObjects(
                    original_id=row["original_id"],
                    category_id=row["category_id"],
                    category_name=row["category_display_name"],
                    source=row["source"],
                    bbox=row["bounding_box"],
                    url=str(base_url.replace(
                        path=f"/dataset/{dataset_id}/data/image/{image_id}?&object_id={media_id}",
                        port=Settings.WEBSERVER_PORT
                    )),
                    metadata_items=[]
                )
            )
        return metadata


@timed
async def _export_info_labels(
    ctx: dict,
    entity_type: ClusterType,
) -> dict[UUID, MetadataExportInfo]:
    query_name = f"export/export_labels_{entity_type.value.lower()}.jinja2"

    metadata: dict[UUID, MetadataExportInfo] = {}
    query = sql_template_utils.render(QueryModule.EXPLORATION, query_name, **ctx)
    with logging_helpers.log_sql_query_time(__name__, query_name, query, ctx, ):
        async for row in _stream_query_results(query, ctx):
            metadata[row["label_id"]] = MetadataExportInfo(
                id=row["label_id"],
                type=MetadataType.IMAGE_LABEL,
                media_id=row["media_id"],
                properties=MetadataPropertiesLabels(
                    original_id=row["original_id"],
                    category_id=row["category_id"],
                    name=f'{row["label_type"].lower()}_label',
                    category_name=row["category_display_name"],
                    # value=row["category_display_name"],
                    source=SOURCE_DISPLAY_NAME.get(row["source"], row["source"]),
                    bbox=row.get("bounding_box")
                )
            )
    return metadata


@timed
async def _export_info_issues(
        ctx: dict
) -> dict[UUID, MetadataExportInfo]:
    query = sql_template_utils.render(QueryModule.EXPLORATION, "export/export_issues.jinja2", **ctx)
    metadata: dict[UUID, MetadataExportInfo] = {}
    async for row in _stream_query_results(query, ctx):
        if row["issue_type_name"] != "normal":
            metadata[row["issue_id"]] = MetadataExportInfo(
                id=row["issue_id"],
                type=MetadataType.ISSUE,
                media_id=row["media_id"],
                properties=MetadataPropertiesIssues(
                    issue_type=row["issue_type_name"],
                    issues_description=row["issues_description"],
                    confidence=row["issue_confidence"],
                    duplicate_group_id=row["issue_subject_id"] if row["issue_type_name"] == "duplicates" else None,
                )
            )
    return metadata


@timed
async def _export_info_tags(
        ctx: dict
) -> dict[UUID, MetadataExportInfo]:
    query = sql_template_utils.render(QueryModule.EXPLORATION, "export/export_tags.jinja2", **ctx)
    metadata: dict[UUID, MetadataExportInfo] = {}
    with logging_helpers.log_sql_query_time(__name__, 'export_tags', query, ctx, ):
        async for row in _stream_query_results(query, ctx):
            media_tag_id = concat_uuids(row["media_id"], row["tag_id"])  # TODO: add an id to media_to_tags table
            metadata[media_tag_id] = MetadataExportInfo(
                id=media_tag_id,
                type=MetadataType.USER_TAG,
                media_id=row["media_id"],
                properties={
                    "tag_name": row["tag_name"],
                    "assigned_date": row["media_to_tags_created_at"],
                }
            )
    return metadata


@timed(context_keys=["context.dataset_id"])
async def generate_export_info(
    context: ExplorationContext,
    base_url: URL,
    cluster_ids: Optional[list[UUID]] = None,
    media_ids: Optional[list[UUID]] = None,
    export_progress_service: Optional[ExportProgressService] = None
):
    ctx = context.dict() | {"cluster_ids": cluster_ids, "media_ids": media_ids}
    (export_info_images, export_info_objects, export_info_labels_images, export_info_issues, export_info_tags) = (
        await asyncio.gather(
            _export_info_images(ctx, base_url, export_progress_service),
            _export_info_objects(ctx, base_url, export_progress_service),
            _export_info_labels(ctx, ClusterType.IMAGES),
            _export_info_issues(ctx),
            _export_info_tags(ctx)
        )
    )
    return (
        export_info_images, export_info_objects, export_info_labels_images, export_info_issues, export_info_tags
    )


@timed
def _build_export_info(
        export_task_id: UUID,
        user: User,
        dataset: Dataset,
        base_url: URL,
        export_info_images: dict[UUID, ImageExportInfo],
        export_info_objects: dict[UUID, MetadataExportInfo],
        export_info_labels_images: dict[UUID, MetadataExportInfo],
        export_info_issues: dict[UUID, MetadataExportInfo],
        export_info_tags: dict[UUID, MetadataExportInfo],
) -> ExportInfo:
    for metadata_item in (export_info_issues | export_info_tags).values():
        if metadata_item.media_id in export_info_objects:
            export_info_objects[metadata_item.media_id].properties.metadata_items.append(metadata_item)

    for metadata_item in (export_info_issues | export_info_tags | export_info_labels_images).values():
        if metadata_item.media_id in export_info_images:
            export_info_images[metadata_item.media_id].metadata_items.append(metadata_item)

    for object_info in export_info_objects.values():
        export_info_images[object_info.media_id].metadata_items.append(object_info)

    export_info = ExportInfo(
        info=GeneralExportInfo(
            dataset=dataset.display_name,
            description=f"Exported from {dataset.display_name} at Visual Layer",
            dataset_url=str(base_url.replace(path=f"/dataset/{dataset.dataset_id}/data", port=Settings.WEBSERVER_PORT)),
            export_time=datetime.now(),
            dataset_creation_time=dataset.created_at,
            exported_by=str(user.name or user.email or user.user_identity or user.user_id or ''),
            total_media_items=len(export_info_images),
            export_task_id=export_task_id,
        ),
        media_items=list(export_info_images.values()),
    )

    return export_info


async def build_export_info(
    export_task_id: UUID,
    context: ExplorationContext,
    base_url: URL,
    export_progress_service: ExportProgressService,
    cluster_ids: Optional[list[UUID]] = None,
    media_ids: Optional[list[UUID]] = None,
) -> ExportInfo:
    await export_progress_service.update_progress(ExportTaskStatus.INIT)
    await export_progress_service.create_update_progress_task()
    if media_ids:
        assert context.threshold is not None
    (
        export_info_images, export_info_objects, export_info_labels_images,
        export_info_issues, export_info_tags
     ) = await generate_export_info(
        context, base_url, cluster_ids, media_ids, export_progress_service=export_progress_service
    )
    export_progress_service.metadata_records_total = export_progress_service.metadata_records_total
    await export_progress_service.update_progress(ExportTaskStatus.IN_PROGRESS)
    export_info = _build_export_info(
        export_task_id, context.user, context.dataset, base_url, export_info_images, export_info_objects,
        export_info_labels_images, export_info_issues, export_info_tags)
    return export_info


async def check_for_concurrent_export_task(
        user_id: UUID,
        max_concurrent_tasks=Settings.MAX_NUM_OF_CONCURENT_EXPORT_TASKS
) -> bool:
    if max_concurrent_tasks:
        async with get_async_session() as session:
            res = (await session.execute(
                sa.text("""
                SELECT 1 FROM export_task 
                WHERE user_id = :user_id AND status NOT IN ('COMPLETED', 'FAILED') and created_at > :duration_window
                """), {"user_id": user_id, "duration_window": datetime.now() - timedelta(days=1)},
            )).all()
        return res and (len(res) >= max_concurrent_tasks)
    else:
        return False


async def create_export_task_in_db(dataset_id: UUID, user_id: UUID) -> ExportTask:
    async with get_async_session(autocommit=True) as session:
        export_task_raw = (await session.execute(
            sa.text("""
            INSERT INTO export_task(dataset_id, user_id) VALUES(:dataset_id, :user_id)
            RETURNING *
            """),
            {"dataset_id": dataset_id, "user_id": user_id},
        )).mappings().one()
    return ExportTask(**export_task_raw)


async def update_export_task_in_db(
        export_task_id: UUID,
        export_task_status: ExportTaskStatus,
        progress=None,
        download_uri: Optional[str] = None
):
    async with get_async_session(autocommit=True) as session:
        ctx = {
            "export_task_id": export_task_id,
            "export_task_status": export_task_status,
            "progress": progress,
            "download_uri": download_uri
        }
        query = sql_template_utils.render(
            QueryModule.EXPLORATION,
            f"export/update_export_task.jinja2",
            **ctx,
        )
        await session.execute(sa.text(query), ctx)


async def get_export_task_status(
        export_task_id: UUID, user_id: UUID) -> ExportTask:
    async with get_async_session(autocommit=True) as session:
        res = (await session.execute(sa.text("""
            SELECT * FROM export_task WHERE id = :export_task_id AND user_id = :user_id
        """), {
            "export_task_id": export_task_id,
            "user_id": user_id
        })).mappings().one_or_none()
    if res:
        return ExportTask(**res)
