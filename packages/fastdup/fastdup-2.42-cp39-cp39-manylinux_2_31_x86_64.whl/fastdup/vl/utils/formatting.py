from typing import Optional


def sizeof_fmt(num: Optional[int], suffix: str = "B", precision: int = 2, k_size: float = 1024.0) -> str:
    if num is None:
        return "N/A"
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < k_size:
            return f"{num:3.{precision}f}{unit}{suffix}".strip()
        num /= k_size
    return f"{num:3.{precision}f}Y{suffix}".strip()
