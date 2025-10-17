import polars as pl

from fastdup.vl.utils.useful_decorators import timed
from fastdup.vldbaccess.base import BaseDB


class MediaCaptionsDB(BaseDB):
    BATCH_SIZE = 1000

    @staticmethod
    @timed
    def insert_media_to_captions(media_to_captions: pl.DataFrame) -> int:
        insert_query = """
            INSERT INTO media_to_captions
                (media_id, caption, dataset_id) 
            VALUES
                (:media_id, :caption, :dataset_id);
        """
        count: int = 0
        for i in range(0, len(media_to_captions), MediaCaptionsDB.BATCH_SIZE):
            batch = media_to_captions[i:i + MediaCaptionsDB.BATCH_SIZE]
            if len(batch):
                count += MediaCaptionsDB.execute_batch_stmt(insert_query, batch.to_dicts())

        return count
