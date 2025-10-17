from fastdup.vl.common.settings import Settings
from fastdup.vldbaccess.dataset import DatasetDB
from fastdup.vldbaccess.user import UserDB, User
from fastdup.vldbaccess.base import DatasetSourceType, SampleDataset, DatasetStatus


def create_dataset(user: User) -> None:
    DatasetDB.create(
        dataset_id=Settings.DATASET_ID,
        created_by=user.user_id,
        owned_by='VL',
        display_name=Settings.DATASET_NAME,
        preview_uri='imported',
        source_uri='',
        source_type=DatasetSourceType.VL,
        description='',
        size_bytes=Settings.DATASET_SIZE_BYTES,
        sample=SampleDataset.DEFAULT_SAMPLE,
        status=DatasetStatus.INDEXING
    )


def sync_data_to_db(user: User) -> None:
    from fastdup.vldbmigration.main import write_to_db # moved here as CDN_ROOT_PATH is initialized in init (after CdnContext)

    write_to_db(
        user=user,
        dataset_name='', # not relevant since dataset is not being created
        source_url='',
        dataset_id=Settings.DATASET_ID,
        create_dataset=False,
        should_persist_embeddings=Settings.PERSIST_EMBEDDINGS
    )


def run_sync_db() -> None:
    user = UserDB._get_system_user()  # uses DB
    create_dataset(user)  # uses DB
    sync_data_to_db(user)  # uses DB
