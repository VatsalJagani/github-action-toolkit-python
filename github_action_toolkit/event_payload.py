import json
import os
from functools import lru_cache
from typing import Any, Dict


@lru_cache(maxsize=1)
def event_payload() -> Dict[str, Any]:
    """
    gets GitHub event payload data.

    :returns: dictionary of event payload
    """
    with open(os.environ["GITHUB_EVENT_PATH"]) as f:
        data: Dict[str, Any] = json.load(f)
    return data
