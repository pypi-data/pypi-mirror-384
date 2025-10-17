import os
from fastdup.vl.common.logging_init import get_vl_logger
logger = get_vl_logger(__name__)

def snake_to_camel_case(s):
    s = s.lower().title().replace("_", "")
    return s[0].lower() + s[1:]


def get_version_config(version_names, camel_case=False):
    version_config = {}
    for env_var_name in version_names:
        value = os.environ.get(env_var_name, None)
        if value:
            env_var_name = env_var_name.lower()
            if camel_case:
                env_var_name = snake_to_camel_case(env_var_name)
            version_config[env_var_name] = value
        else:
            logger.warning(f"Missing env var: {env_var_name}")
    return version_config


def get_pipeline_version(camel_case=False):
    pipeline_version_env_vars = [
        "PIPELINE_VERSION",
        "SETUP_LAMBDA_NAME",
        "POST_STEP_LAMBDA_NAME",
        "SYNC_DB_STEP_VERSION",
        "DOWNLOAD_ZIP_STEP_VERSION",
        "UPLOAD_IMAGE_THUMBS_STEP_VERSION",
        "FASTDUP_STEP_VERSION",
        "DELETE_LOCAL_STEP_VERSION",
        "PIPELINE_STATE_MACHINE_ARN",
        "UPLOAD_IMAGES_STEP_VERSION",
        "TREE_STEP_VERSION",
        "EXPLORATION_STEP_VERSION",
        "UPLOAD_OBJECT_THUMBS_STEP_VERSION",
        "UPLOAD_PROCESSING_STEP_VERSION",
        "DOWNLOAD_S3_STEP_VERSION",
        "ISSUES_GEN_STEP_VERSION",
        "PREPROCESS_STEP_VERSION",
    ]
    return get_version_config(pipeline_version_env_vars, camel_case=camel_case)


def get_server_version(camel_case=False):
    server_version_env_vars = ["PROFILER_BE_VERSION", "PROFILER_FE_VERSION"]
    return get_version_config(server_version_env_vars, camel_case=camel_case)
