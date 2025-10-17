from enum import Enum


class AnchorType(str, Enum):
    MEDIA = "MEDIA"  # indexed media, either image or object  (default)
    UPLOAD = "UPLOAD"  # an image uploaded through the similarity-image-search

    def query_vector_table(self) -> str:
        if self == AnchorType.MEDIA:
            return "image_vector"
        elif self == AnchorType.UPLOAD:
            return "query_vector_embedding"

    def __str__(self) -> str:
        return str(self.value)
