from typing import NamedTuple, Optional


class BBox(NamedTuple):
    left: int
    upper: int
    right: int
    lower: int

    @classmethod
    def from_str(cls, bounding_box_str: Optional[str]):
        if bounding_box_str is not None:
            return cls(*(int(t) for t in bounding_box_str.split(',')))
        return None
