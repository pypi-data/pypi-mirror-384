import json
import typing
from typing import Optional, List

import pandas as pd
from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate
from pydantic import BaseModel

from fastdup.vl.common import logging_init
from fastdup.vl.utils import fs_utils

logger = logging_init.get_vl_logger(__name__)


def validate_annotations_filenames(filenames: List[str]) -> tuple[bool, Optional[str]]:
    def validate_json(json_files: List[str]) -> bool:
        return len(json_files) == 1 and json_files[0] == 'annotations.json'

    def validate_csv(csv_files: List[str]) -> bool:
        return (1 <= len(csv_files) <= 2
                and set(csv_files) <= {'image_annotations.csv', 'object_annotations.csv'})

    def validate_parquet(parquet_files: List[str]) -> bool:
        return (1 <= len(parquet_files) <= 2
                and set(parquet_files) <= {'image_annotations.parquet', 'object_annotations.parquet'})

    def validate_files_types() -> bool:
        file_exts = {fs_utils.get_file_ext(f) for f in filenames}
        return len(file_exts) == 1 and file_exts <= {'json', 'csv', 'parquet'} or \
            len(file_exts) == 2 and file_exts <= {'csv', 'parquet'}

    if validate_json(filenames) or validate_csv(filenames) or validate_parquet(filenames):
        return True, None

    if not validate_files_types():
        return False, 'Unsupported files types'
    else:
        return False, 'Invalid annotations filenames'


def normalize_bbox(scale_factor, col_x, row_y, width, height):
    return tuple(dim * scale_factor for dim in (int(col_x), int(row_y), int(width), int(height)))


class AnnotatedBoundingBox(BaseModel):
    col_x: int
    row_y: int
    width: int
    height: int
    annotations: List[str]


class AnnotationsMap:
    images_table_data: Optional[pd.DataFrame] = None
    objects_table_data: Optional[pd.DataFrame] = None

    def __init__(self, images_table_data: Optional[pd.DataFrame] = None,
                 objects_table_data: Optional[pd.DataFrame] = None):
        self.images_table_data = images_table_data
        self.objects_table_data = objects_table_data

    def is_empty(self) -> bool:
        return ((self.images_table_data is None or self.images_table_data.empty)
                and (self.objects_table_data is None or self.objects_table_data.empty))

    def load_single_table_data(self, data: pd.DataFrame):
        if 'col_x' not in data.columns:
            self.images_table_data = data
        else:
            self.objects_table_data = data

    def load_from_json_data(self, data):
        image_id_to_filename = {img['id']: img['file_name'] for img in data['images']}
        category_id_to_label = {category['id']: category['name'] for category in data['categories']}

        image_annotations = []
        object_annotations = []

        for annotation in data['annotations']:
            image_id = annotation['image_id']
            category_id = annotation['category_id']
            filename = image_id_to_filename[image_id]
            label = category_id_to_label[category_id]

            if 'bbox' in annotation:
                col_x, row_y, width, height = annotation['bbox']
                object_annotations.append({
                    'filename': filename,
                    'col_x': col_x,
                    'row_y': row_y,
                    'width': width,
                    'height': height,
                    'label': label
                })
            else:
                image_annotations.append({
                    'filename': filename,
                    'label': label
                })

        self.images_table_data = pd.DataFrame(image_annotations)
        self.objects_table_data = pd.DataFrame(object_annotations)

    def check_duplicates(self) -> bool:
        return (self.images_table_data is not None and self.images_table_data.duplicated().any()) \
            or (self.objects_table_data is not None and self.objects_table_data.duplicated().any())

    def get_image_labels_from_filename(self, filename: str):
        if self.images_table_data is None or self.images_table_data.empty:
            return []
        labels = self.images_table_data.loc[self.images_table_data['filename'] == filename, 'label'].tolist()
        return labels

    def get_object_labels_from_filename(self, filename: str, scale_factor: float):
        if self.objects_table_data is None or self.objects_table_data.empty:
            return []

        filtered_by_filename = self.objects_table_data[self.objects_table_data['filename'] == filename]

        grouped_by_bbx = filtered_by_filename.groupby(['col_x', 'row_y', 'width', 'height'])['label'].apply(list)

        object_annotations = []

        for (col_x, row_y, width, height), labels in grouped_by_bbx.items():
            col_x, row_y, width, height = normalize_bbox(scale_factor, col_x, row_y, width, height)

            annotated_bbox = AnnotatedBoundingBox(
                col_x=col_x,
                row_y=row_y,
                width=width,
                height=height,
                annotations=labels
            )
            object_annotations.append(annotated_bbox)

        return object_annotations

    def get_unique_filenames(self) -> list[str]:
        unique_filenames = set()

        if self.images_table_data is not None and not self.images_table_data.empty:
            unique_filenames.update(self.images_table_data['filename'].unique())

        if self.objects_table_data is not None and not self.objects_table_data.empty:
            unique_filenames.update(self.objects_table_data['filename'].unique())

        return list(unique_filenames)


COCO_SCHEMA = {
    "type": "object",
    "properties": {
        "images": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "file_name": {"type": "string"}
                },
                "required": ["id", "file_name"]
            }
        },
        "categories": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"}
                },
                "required": ["id", "name"]
            }
        },
        "annotations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "image_id": {"type": "integer"},
                    "category_id": {"type": "integer"},
                    "bbox": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 4,
                        "maxItems": 4
                    }
                },
                "required": ["id", "image_id", "category_id"]
            }
        }
    },
    "required": ["images", "categories", "annotations"]
}


def validate_json_file(file: typing.BinaryIO) -> tuple[bool, Optional[AnnotationsMap], Optional[str]]:
    """
    returns a tuple of [is_valid, data, message]
    """
    try:
        content = file.read()
        if not content:
            return False, None, 'Empty file'

        data = json.loads(content)

        validate(instance=data, schema=COCO_SCHEMA)

        annotations = AnnotationsMap()
        annotations.load_from_json_data(data)

        return True, annotations, None

    except json.decoder.JSONDecodeError as e:
        logger.exception(e, exc_info=True)
        return False, None, f'Invalid JSON file {e}'
    except Exception as e:
        logger.exception(e, exc_info=True)
        return False, None, f'Invalid COCO JSON format {e}'



REQUIRED_IMAGE_COLUMNS = {"filename": str, "label": str}
REQUIRED_OBJECT_COLUMNS = {"filename": str, "col_x": (int, float), "row_y": (int, float), "width": (int, float),
                           "height": (int, float), "label": str}


def validate_df_format(df: pd.DataFrame, filename: str) -> Optional[str]:
    required_columns = REQUIRED_IMAGE_COLUMNS if 'image' in filename else REQUIRED_OBJECT_COLUMNS

    for col_name, col_type in required_columns.items():
        if col_name not in df.columns:
            return f'Missing required field: {col_name}'
        if not df[col_name].apply(lambda x: isinstance(x, col_type)).all():
            return f'Invalid data type in column: {col_name}'


def validate_table_file(
        file: typing.BinaryIO, filename: str
) -> tuple[bool, Optional[typing.Any], Optional[str]]:
    try:
        file.seek(0)
        read_function = pd.read_csv if 'csv' in filename else pd.read_parquet
        data = read_function(file)
    except Exception as e:
        logger.exception(e, exc_info=True)
        return False, None, 'Unreadable file'

    reason = validate_df_format(data, filename)
    if reason:
        return False, data, reason

    return True, data, None
