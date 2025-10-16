from pydantic import BaseModel, ConfigDict


class Compiler(BaseModel):
    """Compiler configuration dataclass"""

    model_config = ConfigDict(extra='allow')
    name: str