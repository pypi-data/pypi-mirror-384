import inspect
import json
import logging
import os
import traceback
from pathlib import Path
from typing import Optional, TypeVar, Callable, Union, MutableMapping, Any, Generator, Tuple, Dict
from fastdup.vl.utils.common import parse_device_list, running_env, str2list

import yaml

from fastdup.vl.utils.common import str2bool, uuid_from_any, str2loglevel, str_args_to_list

T = TypeVar('T')

LOG_SET_CALLS: bool = False


class ConfigValue:
    def __init__(self, builder: Callable[[str], T] = str, default: Optional[T] = None, secret: bool = False) -> None:
        self.builder: Callable[[str], T] = builder
        self.value: Optional[T] = default
        self.default: Optional[T] = default
        self.tag: str = 'uninitialized' if default is None else 'default value'
        self.secret: bool = secret

    def _set_value(self, key: str, value: Any, tag: str) -> None:
        # TODO either use __set__ or call this method from __set__
        try:
            if value is None:
                self.value = self.default
            else:
                self.value = self.builder(value)
            self.tag = tag
        except Exception as e:
            logging.error(f'failed to assign value {value} to config field {key} {traceback.format_exc()}')

    def __get__(self, obj, objtype=None) -> T:
        return self.value

    def __set__(self, instance, value: T):
        try:
            frame: Optional[inspect.FrameInfo] = None
            for frame in inspect.stack():
                if not frame.function.startswith('__'):
                    break

            if frame:
                self.tag = f'set inline in {frame.filename}:{frame.lineno} by {frame.function}'
            else:
                self.tag = 'set inline (frame unavailable)'

            if value is None:
                self.value = self.default
            else:
                self.value = self.builder(value)

            if LOG_SET_CALLS:
                logging.info(f'Assigned "{value}" to a settings parameter: {self.tag}')

        except Exception as e:
            logging.exception(f'Failed to assign value "{value}" to a settings parameter: {self.tag}')
            logging.exception(e)
            raise e


class MyMeta(type):

    def __setattr__(self, key, value):
        self.__dict__[key].__set__(self, value)

    def __repr__(cls):
        res: str = 'Settings:\n'
        for attribute_name in sorted(Settings.__annotations__):
            config_value: ConfigValue = Settings.__getattribute__(Settings, attribute_name)
            if config_value.secret:
                value = '***'
            elif config_value.value == '':
                value = "''"
            else:
                value = config_value.value
            res += (f'{attribute_name:<45}{type(config_value.value).__name__:<15}'
                    f' {str(value):<40} {config_value.tag}\n')

        return res


class Settings(metaclass=MyMeta):
    # Common
    ENV_NAME = ConfigValue(default=running_env())
    MAX_NUM_OF_IMAGES_TO_EXPORT = ConfigValue(int, 5000)
    MAX_NUM_OF_CONCURENT_EXPORT_TASKS = ConfigValue(int, 0)
    VL_HOME: ConfigValue = ConfigValue(Path, default=Path(__file__).parent.parent.parent / '.vl')
    AWS_ACCESS_KEY: ConfigValue = ConfigValue(str)
    AWS_SECRET_KEY: ConfigValue = ConfigValue(str)
    EMAIL_API_KEY: ConfigValue = ConfigValue(str)
    PG_URI: ConfigValue = ConfigValue(secret=True)
    STORAGE_KEY: ConfigValue = ConfigValue(secret=True)
    PG_SECRET: ConfigValue = ConfigValue()
    MIN_PG_CONNECTION_POOL_SIZE: ConfigValue = ConfigValue(int, 2)
    MAX_PG_CONNECTION_POOL_SIZE: ConfigValue = ConfigValue(int, 10)
    LOGGING_CONFIG_FILE: ConfigValue = ConfigValue(str, "flat-logging.yaml")
    PREFECT_LOGGING_ENABLED: ConfigValue = ConfigValue(str2bool, default=False)
    SENTRY_OPT_OUT: ConfigValue = ConfigValue(str2bool, default=True)
    SENTRY_PROJ: ConfigValue = ConfigValue(
        str,
        "https://d79dd3832b804d63921b8858ad766e43@o4504135122944000.ingest.sentry.io/4505317881020416"
    )
    DEPLOYMENT_REMOTE_ACCESS: ConfigValue = ConfigValue(str2bool, True)
    CUSTOMER_NAME: ConfigValue = ConfigValue(default='Undefined')
    CDN_DISTR_ID: ConfigValue = ConfigValue(str)
    CDN_HOST: ConfigValue = ConfigValue(str, default='')
    CDN_PROTOCOL: ConfigValue = ConfigValue(str, default='')
    CDN_ROOT_PATH: ConfigValue = ConfigValue(str, default='')
    LOG_LEVEL: ConfigValue = ConfigValue(str2loglevel, default=logging.INFO)

    # Backend
    DISABLE_AUTH: ConfigValue = ConfigValue(str2bool, default=False)
    VIDEO_HOSTING_URI: ConfigValue = ConfigValue(str, '')
    VIDEO_HOSTING_SKIP_PATH_SEGMENTS_N: ConfigValue = ConfigValue(int, 0)
    SORT_EXPLORATION_RESULTS_BY_TEXT_RELEVANCE: ConfigValue = ConfigValue(str2bool, True)
    SORT_EXPLORATION_RESULTS_BY_CLUSTER_FORMED: ConfigValue = ConfigValue(str2bool, False)
    PREFER_IMAGES_OVER_OBJECTS: ConfigValue = ConfigValue(int, 0)
    DATE_DATA_EXISTS: ConfigValue = ConfigValue(str2bool, False)
    ISSUES_DATA_EXISTS: ConfigValue = ConfigValue(str2bool, False)
    LABEL_FILTER__BEHAVIOR_OF_AND: ConfigValue = ConfigValue(str2bool, False)
    MUTUALLY_EXCLUSIVE_ENTITY_TYPE_SELECTOR: ConfigValue = ConfigValue(str2bool, True)
    SERVICE_HEALTH_MESSAGE: ConfigValue = ConfigValue(default='none')
    CLUSTER_ENTITIES_PAGE_SIZE: ConfigValue = ConfigValue(int, default=100)
    CLUSTERS_PAGE_SIZE: ConfigValue = ConfigValue(int, default=100)
    CLUSTER_LABELS_COUNT: ConfigValue = ConfigValue(int, default=10)
    FILE_FILTER_TREE_MAX_DEPTH: ConfigValue = ConfigValue(int, default=3)
    FILE_FILTER_TREE_INCLUDE_FILES: ConfigValue = ConfigValue(str2bool, default=False)
    SEARCH_SIMILAR_CLUSTERS_MAX_PREVIEWS: ConfigValue = ConfigValue(int, default=9)
    SEARCH_SIMILAR_CLUSTERS_USE_VECTOR_DB: ConfigValue = ConfigValue(str2bool, default=False)
    SEARCH_SIMILAR_CLUSTERS_PRE_FILTER_RESULTS: ConfigValue = ConfigValue(int, default=1000)
    SEARCH_SIMILAR_SIMILARITY_THRESHOLD: ConfigValue = ConfigValue(float, default=0.3)
    S3_ARTIFACTS_BUCKET_NAME: ConfigValue = ConfigValue(str, default="")
    S3_VL_INGESTION_SERVICE_STORAGE: ConfigValue = ConfigValue(str, default="vl-ingestion-service-storage")
    LOG_EVENT_LOOP_BLOCKED_S = ConfigValue(int, default=5)

    # Features gating
    USER_TAGS_ENABLED: ConfigValue = ConfigValue(str2bool, default=False)
    ACTIONS_CART_ENABLED: ConfigValue = ConfigValue(str2bool, default=False)
    FILE_FILTER_ENABLED: ConfigValue = ConfigValue(str2bool, default=False)
    CLUSTER_METADATA_SUMMARY_ENABLED: ConfigValue = ConfigValue(str2bool, default=False)
    VISUAL_SEARCH_ENABLED: ConfigValue = ConfigValue(str2bool, default=False)
    VISUAL_SEARCH_ENABLED_DATASET_ID: ConfigValue = ConfigValue(uuid_from_any)
    VISUAL_SEARCH_PERSIST_CROPPED_IMAGE: ConfigValue = ConfigValue(str2bool, default=True)
    VECTOR_SEARCH_ENABLED: ConfigValue = ConfigValue(str2bool, default=True)
    AUTO_SUGGEST_RECENT_SEARCHES: ConfigValue = ConfigValue(str2bool, default=True)
    AUTO_SUGGEST_QUERY: ConfigValue = ConfigValue(str2bool, default=False)
    ASSET_PREVIEW_ENABLED: ConfigValue = ConfigValue(str2bool, default=False)
    EXPORT_ENTITIES_ENABLED: ConfigValue = ConfigValue(str2bool, default=False)
    EXPORT_ENTITIES_ENABLED_EMAILS: ConfigValue = ConfigValue(str2list, default=[])
    EXPORT_ENTITIES_CONCURRENT_DOWNLOADS: ConfigValue = ConfigValue(int, default=50)
    EXPORT_ENTITIES_RESULT_BUCKET: ConfigValue = ConfigValue(str, default=None)
    DATA_INGESTION_UX_ENABLED: ConfigValue = ConfigValue(str2bool, default=True)
    DATA_INGESTION_UX_ENABLED_FOR_ALL_AUDIENCES: ConfigValue = ConfigValue(str2bool, default=True)
    DATA_INGESTION_MAX_PREVIEWS: ConfigValue = ConfigValue(int, default=12)
    DATA_INGESTION_MAX_FILE_SIZE: ConfigValue = ConfigValue(int, default=10 * 1024 * 1024)  # 10M
    DATA_INGESTION_MAX_SIZE_BYTES: ConfigValue = ConfigValue(int, default=50 * 1024 * 1024 * 1024)  # 50G
    USAGE_REPORT_ENABLED: ConfigValue = ConfigValue(str2bool, default=False)
    EXPLORATION_DEBUG_INFO: ConfigValue = ConfigValue(str2bool, default=False)
    INVENTORY_FILTER_ENABLED: ConfigValue = ConfigValue(str2bool, default=True)
    DATASET_SHARE_ENABLED: ConfigValue = ConfigValue(str2bool, default=True)

    # Pipeline parameters
    DEPLOYMENT_ROOT: ConfigValue = ConfigValue(Path)
    PROCESSING_MACHINE_ADDRESS: ConfigValue = ConfigValue(str, "localhost")
    DATASET_ID: ConfigValue = ConfigValue(uuid_from_any)
    PIPELINE_ROOT: ConfigValue = ConfigValue(Path)
    DATASET_SOURCE_DIR: ConfigValue = ConfigValue(Path)
    STEPS_TO_EXECUTE: ConfigValue = ConfigValue(str, 'LOCAL_INIT-PUBLISH_MEDIA')
    STEPS_TO_EXCLUDE: ConfigValue = ConfigValue(str, None)
    DATASET_NAME: ConfigValue = ConfigValue(str)
    DATASET_SIZE_BYTES: ConfigValue = ConfigValue(int, -1)
    MIN_NUM_OF_IMAGES: ConfigValue = ConfigValue(int, 2)
    MAX_NUM_OF_IMAGES: ConfigValue = ConfigValue(int, 2_000_000)
    MAX_OBJECT_COUNT: ConfigValue = ConfigValue(int, 10_000_000)
    MANUAL_FLOW: ConfigValue = ConfigValue(str2bool, False)
    SUPPORTED_IMG_FORMATS: ConfigValue = ConfigValue(
        list,
        [".png", ".jpg", ".jpeg", ".gif", ".giff", ".tif", ".tiff", ".heic", ".heif", ".bmp", ".webp", ".jfif", ".jp2"]
    )
    SUPPORTED_IMG_FORMATS_BY_CONVERSION: ConfigValue = ConfigValue(
        list,
        [".tif", ".tiff", ".heic", ".heif"]
    )
    SUPPORTED_VID_FORMATS: ConfigValue = ConfigValue(
        list,
        [".mp4", ".avi", ".dav", ".m4v", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".mpg", ".mpeg", ".3gp"]
    )
    RUN_LABEL_RANK: ConfigValue = ConfigValue(str2bool, True)
    FLOW_RUN_ID: ConfigValue = ConfigValue(int)
    SAVE_THUMBNAILS_METHOD: ConfigValue = ConfigValue(str, 'python')  # 'fastdup', 'python', None
    IS_FASTDUP: ConfigValue = ConfigValue(str2bool, False)
    LIMIT_NUM_IMAGES: ConfigValue = ConfigValue(
        int)  # if number of images > LIMIT_NUM_IMAGES then take random LIMIT_NUM_IMAGES
    LIMIT_NUM_OBJECTS: ConfigValue = ConfigValue(
        int)  # if number of objects > LIMIT_NUM_OBJECTS then take random LIMIT_NUM_OBJECTS

    # Preprocessing
    PREFECT_PIPELINE_ENABLED: ConfigValue = ConfigValue(str2bool, False)
    PREFECT_API_URL: ConfigValue = ConfigValue(str, 'http://prefect-server:4200/api')
    PREPROCESS_ROOT: ConfigValue = ConfigValue()  # required
    SNAPSHOT_DIR: ConfigValue = ConfigValue()  # logics to implement
    SOURCE_URI: ConfigValue = ConfigValue()
    UNTRACK_BAD_VIDEOS: ConfigValue = ConfigValue(str2bool, default=False)
    CLEAN_THRESHOLD: ConfigValue = ConfigValue(float, 0.96)
    VIDEO_CLEAN_THRESHOLD: ConfigValue = ConfigValue(float, 0.9215)
    OBJECTS_CLEAN_THRESHOLD: ConfigValue = ConfigValue(float, 0.94)
    OBJECTS_ONLY_SAME_VIDEO: ConfigValue = ConfigValue(str2bool, True)
    MIN_FACE_BBOX_SIZE: ConfigValue = ConfigValue(int, 25)
    MIN_OBJECT_BBOX_SIZE: ConfigValue = ConfigValue(int, 50)
    EXPORT_VIDEOS: ConfigValue = ConfigValue(str2bool, False)
    RESUME: ConfigValue = ConfigValue(str2bool, False)
    IMAGES_PER_TAR: ConfigValue = ConfigValue(int, 10000)
    REPORT_LOG_PATH: ConfigValue = ConfigValue()
    CONFIG_FILE: ConfigValue = ConfigValue(Path)
    USE_BLIP2_EMBEDDINGS: ConfigValue = ConfigValue(str2bool, True)
    OBJECT_DETECTION_DEVICES: ConfigValue = ConfigValue(parse_device_list, 'auto')
    CAPTIONING_DEVICES: ConfigValue = ConfigValue(parse_device_list, 'auto')
    TAGGING_DEVICES: ConfigValue = ConfigValue(parse_device_list, 'auto')
    MODELS_SAVE_DIR: ConfigValue = ConfigValue(Path, Path('~/.vl/models').expanduser())
    COPY_LOCAL_SOURCE: ConfigValue = ConfigValue(str2bool, False)
    S3_ADDITIONAL_FLAGS: ConfigValue = ConfigValue(str, default="")
    SPLIT_DATA_SKIP_DIRS: ConfigValue = ConfigValue(str_args_to_list, [])
    PREPROCESS_IMAGES_OUTDIR: ConfigValue = ConfigValue(Path)
    PREPROCESS_METADATA_OUTDIR: ConfigValue = ConfigValue(Path)
    PREPROCESS_NORMALIZE_OUTPUT: ConfigValue = ConfigValue(str2bool, False)
    SKIP_EXISTING_ENRICHMENT: ConfigValue = ConfigValue(str2bool, True)
    IMAGES_PER_PARTITION: ConfigValue = ConfigValue(int, 1000)
    CAPTION_USER_OBJECTS: ConfigValue = ConfigValue(str2bool, False)
    SOURCE_USE_FULLPATH: ConfigValue = ConfigValue(str2bool, False)
    DATA_LOADER_NUM_WORKERS: ConfigValue = ConfigValue(int, 4)
    PRIVATE_MODELS_CKPT_FILENAMES: ConfigValue = ConfigValue(dict,
                                                             default={'object_detection': "yolov8l_sprint213_ckpt.pt",
                                                                      'caption_images': 'blip2_feature_extraction_adapter_state_dict.pt',
                                                                      'caption_objects': 'blip2_feature_extraction_adapter_state_dict.pt'})
    OBJECT_DETECTION_CONF_THRESH: ConfigValue = ConfigValue(float, 0.3)
    OBJECT_DETECTION_IMG_SIZE: ConfigValue = ConfigValue(int, 640)
    OBJECT_DETECTION_BATCH_SIZE: ConfigValue = ConfigValue(int, 16)
    PREPROCESS_ENABLED: ConfigValue = ConfigValue(str2bool, False)
    PREPROCESS_SECTION: ConfigValue = ConfigValue(str)
    USE_TENSORRT: ConfigValue = ConfigValue(str2bool, False)
    PREPROCESS_STEPS: ConfigValue = ConfigValue(str_args_to_list)
    ROOT_FORCE_ABSPATH: ConfigValue = ConfigValue(str2bool, True)
    PERSIST_EMBEDDINGS: ConfigValue = ConfigValue(str2bool, True)
    COPY_IMAGE_WITH_SYMLINK: ConfigValue = ConfigValue(str2bool, False)

    # Profiler
    SKIP_FASTDUP_IMAGE_RUN: ConfigValue = ConfigValue(str2bool, False)

    # Toolkit
    LOCAL_WEBSERVER_HOST: ConfigValue = ConfigValue(str, 'localhost')
    LOCAL_WEBSERVER_PORT: ConfigValue = ConfigValue(int, 2080)
    LOCAL_VL_MOUNT: ConfigValue = ConfigValue(str, '/.vl')

    WEBSERVER_PORT: ConfigValue = ConfigValue(int, None)

    # fastdup integration
    LOCAL_FE_DIR: ConfigValue = ConfigValue(Path, Path())
    CDN_FULLPATH: ConfigValue = ConfigValue(Path)
    GITHUB_CLIENT_ID: ConfigValue = ConfigValue(str)
    GITHUB_CLIENT_SECRET: ConfigValue = ConfigValue(str)
    GOOGLE_OAUTH_APP_AUDIENCE: ConfigValue = ConfigValue(str, default="438566617424-csk23v2m8kg02bj201m4ue9dvq0pfmiq.apps.googleusercontent.com")

    # onprem object store
    OBJECT_STORE_URL: ConfigValue = ConfigValue(str)
    DATASET_OBJECT_STORE_PATH: ConfigValue = ConfigValue(str)

    # pgvector
    PGVECTOR_MAINTENANCE_WORK_MEM_GB = ConfigValue(int, default=2)
    PGVECTOR_MAX_PARALLEL_MAINTENANCE_WORKERS = ConfigValue(int, default=4)

    @staticmethod
    def _attrs() -> Generator[Tuple[str, ConfigValue], None, None]:
        for attribute_name in Settings.__annotations__:
            yield attribute_name, Settings.__getattribute__(Settings, attribute_name)

    @staticmethod
    def dump() -> dict:
        d = {}
        for k, v in Settings._attrs():
            config_var_dict: Dict[str, Any] = {'tag': v.tag}
            if v.value is None:
                config_var_dict['value'] = None
            elif isinstance(v.value, dict) or isinstance(v.value, list):
                config_var_dict['value'] = v.value
            else:
                config_var_dict['value'] = str(v.value)
            d[k] = config_var_dict

        return d

    @staticmethod
    def restore(d: dict):
        for k, v in Settings._attrs():
            if k in d:
                v._set_value(k, d[k]['value'], f"loaded, orig from {d[k]['tag']}")

    @staticmethod
    def apply_json(file_path: Path):
        with open(file_path) as file:
            d: dict = json.load(file)
            caller = inspect.stack()[1]
            tag: str = f'loaded from file {file_path.absolute()} at {caller.filename} line {caller.lineno}'
            Settings._apply_mapping(d, tag)

    @staticmethod
    def apply_yaml(file_path: Path):
        with open(file_path) as file:
            d = yaml.load(file, yaml.Loader)
            caller = inspect.stack()[1]
            tag: str = f'loaded from file {file_path.absolute()} at {caller.filename} line {caller.lineno}'
            Settings._apply_mapping(d, tag)

    @staticmethod
    def apply_mapping(mapping: Union[dict, MutableMapping], tag: str):
        if mapping is None:
            return
        caller = inspect.stack()[1]
        tag: str = f'{tag} at {caller.filename} line {caller.lineno}'
        Settings._apply_mapping(mapping, tag)

    @staticmethod
    def apply_os_envvars():
        caller = inspect.stack()[1]
        tag: str = f'read from os.environ at {caller.filename} line {caller.lineno}'
        Settings.apply_mapping(os.environ, tag)

    @staticmethod
    def _apply_mapping(mapping: Union[dict, MutableMapping], tag: str):
        for attribute_name in Settings.__annotations__:
            if attribute_name in mapping:
                config_value = ConfigValue.__getattribute__(Settings, attribute_name)
                config_value._set_value(attribute_name, mapping[attribute_name], tag)

    @staticmethod
    def get(key: str, cast_to: callable = None, required: bool = False) -> Optional[T]:
        if key in Settings.__annotations__:
            config_value: ConfigValue = Settings.__getattribute__(Settings, key)
            if config_value.value is None and required:
                raise Exception(f"Required setting {key} is None")
            if cast_to is None or cast_to == config_value.builder:
                return config_value.value
            else:
                return cast_to(config_value.value)
        elif required:
            raise Exception(f"Missing required setting {key}")
        else:
            return None

    @classmethod
    def init(cls):
        if os.environ.get('CONFIG_FILE'):
            cls.apply_json(Path(os.environ.get('CONFIG_FILE')))

        cls.apply_os_envvars()


Settings.init()

logging.debug('Settings:\n' + repr(Settings))
