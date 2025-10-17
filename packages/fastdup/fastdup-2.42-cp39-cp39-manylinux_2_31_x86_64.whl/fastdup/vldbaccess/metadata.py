from typing import Optional, Union, List, Dict
from uuid import UUID

import sqlalchemy as sa
from pydantic import BaseModel

from fastdup.vl.common.settings import Settings
from fastdup.vl.utils.useful_decorators import timed
from fastdup.vldbaccess.connection_manager import get_session


class FileNode(BaseModel):
    full_path: str
    name: str
    type: str


class FolderNode(FileNode):
    children: list[Union[FileNode, "FolderNode"]]

    def get_child(self, name: str) -> Optional[Union[FileNode, "FolderNode"]]:
        if not self.children or len(self.children) == 0:
            return None
        for child in self.children:
            if child.name == name:
                return child
        return None


def _get_child_by_element(d: dict, element_name: str, element_value: str) -> Optional[dict]:
    if d.get('children') is None:
        return None
    for child in d['children']:
        if child.get(element_name) == element_value:
            return child
    return None


def get_file_tree(dataset_id: UUID, user_id: UUID) -> FolderNode:
    rows = retrieve_paths(dataset_id, user_id)
    root = build_file_tree(rows, Settings.FILE_FILTER_TREE_MAX_DEPTH, Settings.FILE_FILTER_TREE_INCLUDE_FILES)
    return root


@timed
def retrieve_paths(dataset_id, user_id):
    with get_session() as session:
        rows: List[Dict] = session.execute(sa.text(
            """
            SELECT
                CASE
                    WHEN metadata ->> 'video' IS NOT NULL THEN 'VIDEO'
                    WHEN metadata ->> 'original_filename' IS NOT NULL THEN 'FILE'
                    WHEN original_uri IS NOT NULL THEN 'LOCAL_FILE'
                    ELSE NULL
                END "type",
                coalesce(metadata ->> 'video', metadata ->> 'original_filename', original_uri) "path"
            FROM
                images
            WHERE
                dataset_id = :dataset_id
            GROUP BY "type","path"
            ORDER BY path
            LIMIT 100000
            ;
            """),
            {"dataset_id": dataset_id, "user_id": user_id}
        ).mappings().all()
    return rows


@timed
def build_file_tree(rows, max_depth: int = 1000, include_files: bool = True):
    root: FolderNode = FolderNode(name='/', type='ROOT', full_path='/', children=[])
    current_node: Union[FileNode, FolderNode]
    next_node: Union[FileNode, FolderNode]
    nodes_map: dict[tuple[str, str], Union[FileNode, FolderNode]] = {}

    full_path: str
    for row in rows:
        # iterate all file paths, for every path build the folder/file nodes
        # and append them to the tree if still not there
        current_node = root
        full_path = row['path']
        segments: list[str] = full_path.split('/')[:max_depth]
        segments_len = len(segments)
        segment: str
        for i, segment in enumerate(segments):
            if not segment:
                continue
            next_node = nodes_map.get((current_node.full_path, segment), None)
            # next_node = current_node.get_child(segment)
            if next_node is None:
                if i == segments_len - 1:  # last segment - this is a file
                    path_to_file = '/' + full_path
                    next_node = FileNode(name=segment, type=row['type'], full_path=path_to_file)
                else:  # folder
                    path_to_segment: str = '/' + '/'.join(segments[:i + 1])
                    next_node = FolderNode(name=segment, type='FOLDER', full_path=path_to_segment, children=[])
                nodes_map.setdefault((current_node.full_path, segment), next_node)
                if isinstance(next_node, FolderNode):
                    current_node.children.append(next_node)

                else:
                    if include_files:
                        current_node.children.append(next_node)

            current_node = next_node
    return root
