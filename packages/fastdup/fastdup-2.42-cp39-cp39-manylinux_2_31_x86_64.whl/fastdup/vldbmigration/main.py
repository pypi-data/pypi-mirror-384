import logging
from typing import Optional
from uuid import UUID

import fastdup.pipeline.k8s_job_steps.sync_db.job
from fastdup.vl.common.settings import Settings
from fastdup.vl.common.logging_init import get_vl_logger
from fastdup.vldbaccess.sync_db_context import SyncDbContext
from fastdup.vldbaccess.base import DatasetSourceType, SampleDataset, DatasetStatus
from fastdup.vldbaccess.dataset import Dataset, DatasetDB
from fastdup.vldbaccess.user import User

logger = get_vl_logger(__name__)

# parser = argparse.ArgumentParser(description='Repack a published wheel file')
#
# parser.add_argument(
#     '-n', '--name', type=str, dest='dataset_name', required=True,
#     help='human readable dataset name'
# )
#
# parser.add_argument(
#     '-s', '--shared', action='store_true', dest='default_sample', required=False,
#     help='make the dataset the DEFAULT_SAMPLE'
# )
#
# parser.add_argument(
#     '-d', '--dataset-id', type=UUID, dest='dataset_id', required=False,
#     help='dataset id'
# )


def write_to_db(
        user: User,
        dataset_name: str,
        source_url: str,
        sample: Optional[SampleDataset] = SampleDataset.DEFAULT_SAMPLE,
        dataset_id: Optional[UUID] = None,
        create_dataset: bool = True,
        should_persist_embeddings: bool = False
) -> UUID:
    logger.info("Creating dataset")
    if create_dataset:
        dataset: Dataset = DatasetDB.create(
            dataset_id=dataset_id,
            created_by=user.user_id,
            owned_by='VL',
            display_name=dataset_name,
            preview_uri='imported',
            source_uri=source_url,
            source_type=DatasetSourceType.VL,
            description='imported from ' + source_url,
            size_bytes=123456789,
            sample=sample
        )
    else:
        dataset: Dataset = DatasetDB.get_by_id(dataset_id, user.user_id)

    context: SyncDbContext = SyncDbContext(
        input_dir=Settings.get('PIPELINE_ROOT', required=True),
        dataset_id=dataset.dataset_id,
        should_persist_issues=True,
        should_persist_entities=True,
        should_persist_similarities=True,
        should_persist_embeddings=should_persist_embeddings
    )

    fastdup.pipeline.k8s_job_steps.sync_db.job.run(context)
    DatasetDB.update(dataset.dataset_id, status=DatasetStatus.READY)
    logger.info("Done")
    return dataset.dataset_id
