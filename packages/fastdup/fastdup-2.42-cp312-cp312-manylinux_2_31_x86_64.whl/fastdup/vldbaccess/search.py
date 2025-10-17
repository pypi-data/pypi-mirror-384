from typing import Optional
from uuid import UUID

from clustplorer.model.similarity_cluster import SimilarityThreshold


class SearchDal:
    @staticmethod
    def construct_similarity_clusters(similarity_threshold: SimilarityThreshold, image_id: Optional[UUID]):
        statement: str = """
            SELECT *
            FROM similarity_clusters simcl
            JOIN images_to_similarity_clusters i2simcl ON simcl.id = i2simcl.cluster_id
            JOIN images ON i2simcl.image_id = images.id
            WHERE simcl.similarity_threshold = %s
        """

        if image_id:
            statement += """
            AND
                simcl.id IN (
                    SELECT simcl.id
                    FROM similarity_clusters simcl, images_to_similairity_clusters i2simcl
                    WHERE simcl.id = i2simcl.cluster_id AND i2simcl.image_id = %s
                )
            """

        statement += """
            ORDER BY simcl.id, i2simcl.preview_order desc
        """