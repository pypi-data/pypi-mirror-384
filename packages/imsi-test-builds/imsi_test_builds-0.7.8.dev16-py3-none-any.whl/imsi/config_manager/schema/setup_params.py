from pydantic import BaseModel, ConfigDict


class SetupParams(BaseModel):
    """Sequencing configuration dataclass"""

    model_config = ConfigDict(extra='allow')
