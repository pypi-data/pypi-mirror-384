from typing import Optional, List

from pydantic import Field, BaseModel, ConfigDict

from imsi.config_manager.schema.types import DateCoerce


class Experiment(BaseModel):
    """Experiment configuration Pydantic model"""

    model_config = ConfigDict(extra='allow')
    name: Optional[str] = Field(None, description='Experiment name')
    experiment_id: str
    subexperiment_id: str
    activity_id: str
    mip_era: str
    model_type: str
    start_time: DateCoerce = Field(
        ..., description='Start time of the experiment', pattern=r'^\d{4}$'
    )
    end_time: DateCoerce = Field(
        ..., description='End time of the experiment', pattern=r'^\d{4}$'
    )
    parent_runid: str
    parent_branch_time: str
    inherits_from: Optional[str] = None
    supported_models: List[str]

    def validate_model_name(self, model_name: str):
        if model_name not in self.supported_models:
            raise ValueError(
                f"For the selected experiment '{self.name}', the selected model '{model_name}' "
                f'is not supported. Valid models for this experiment are: {self.supported_models}.'
            )
