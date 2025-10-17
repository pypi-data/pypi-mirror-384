import os
from pathlib import Path
from typing import Union, List, Optional
from tqdm import tqdm
import polars as pl

from fastdup.vl.common.settings import Settings
from fastdup.pipeline.k8s_job_steps.sync_data_to_local.common.dataset_preprocess import normalize_dataset
from fastdup.pipeline.k8s_job_steps.algo_steps.step_fastdup.job import main as step_fastdup
from fastdup.pipeline.k8s_job_steps.algo_steps.step_issues_generator.job import main as step_issues_generator
from fastdup.pipeline.k8s_job_steps.algo_steps.step_exploration.job import main as step_exploration
from fastdup.fastdup_runner.utilities import update_pbar

def prepare_image_serving() -> None:
    def _move_dir(src: Union[str, Path], dst: Union[str, Path], check_src_exists: bool = False) -> None:
        if check_src_exists and not src.exists():
            return

        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        os.rename(src, dst)

    root: Path = Settings.PIPELINE_ROOT
    step_fastdup_dir = root / 'processing' / 'step_fastdup'
    cdn_dir = Settings.PIPELINE_ROOT / Settings.CDN_FULLPATH

    # original images
    _move_dir(root / 'input' / 'images', cdn_dir / 'images')

    # image thumbnails
    _move_dir(step_fastdup_dir / 'images' / 'thumbnails', cdn_dir / 'image_thumbs')

    # object thumbnails
    _move_dir(step_fastdup_dir / 'objects' / 'thumbnails', cdn_dir / 'object_thumbs', check_src_exists=True)


def run_pipeline(input_dir: Union[str, Path, List[str], pl.Series], pbar: tqdm) -> None:
    pbar.set_description_str('Extracting metadata')
    Settings.DATASET_SIZE_BYTES = normalize_dataset(Settings.DATASET_ID, input_dir,
                                                    Settings.PIPELINE_ROOT, update_db=False)

    update_pbar(pbar, 'Building index')
    step_fastdup()
    step_issues_generator()

    update_pbar(pbar, 'Creating visualization')
    step_exploration()
    prepare_image_serving() # since this moves the folders no point in additional pbar update as it's instant