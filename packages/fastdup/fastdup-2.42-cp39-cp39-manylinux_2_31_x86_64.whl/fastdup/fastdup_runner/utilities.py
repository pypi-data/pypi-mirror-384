from tqdm import tqdm
from typing import Union, Optional

GETTING_STARTED_LINK = 'https://docs.visual-layer.com/docs/getting-started-with-fastdup'
EXPLORATION_PORTS = [9990, 9991]

class ExplorationError(Exception):
    pass

def update_pbar(pbar: tqdm, desc: str) -> None:
    pbar.set_description_str(desc)
    pbar.update()

# this solution is super ugly and should be replaced ASAP
def switch_fastdup_log_level(log_level: Union[str, int]) -> Optional[int]:
    try:
        from fastdup import _LOGGER
        current_level = _LOGGER.level
        _LOGGER.setLevel(log_level)
    except Exception as e:
        current_level = None
    
    return current_level