from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict


class Utilities(BaseModel):
    """Sequencing configuration dataclass"""

    model_config = ConfigDict(extra='allow')
    files_to_extract: Optional[Dict[str, str]] = {}
