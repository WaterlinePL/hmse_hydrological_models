from dataclasses import dataclass, field
from typing import Optional, List, Dict

import numpy as np


@dataclass
class ModflowExtraData:
    rch_shapes: List[np.ndarray]
    start_date: Optional[str]


def extract_extra_from_model(modflow_model) -> Dict:
    start_date = modflow_model.modeltime.start_datetime
    return {
        "start_date": start_date if start_date != '1-1-1970' else None
    }
