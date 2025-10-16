from pydantic import BaseModel, ConfigDict, Field
from imsi.config_manager.schema.types import DateCoerce


class RunDates(BaseModel):
    model_config = ConfigDict(extra='allow')
    run_start_time: DateCoerce = Field(..., description='Start time of the run.')
    run_stop_time: DateCoerce = Field(..., description='End time of the run.')
    run_segment_start_time: DateCoerce = Field(
        ..., description='Start time of the run segment.'
    )
    run_segment_stop_time: DateCoerce = Field(
        ..., description='End time of the run segment.'
    )
    model_chunk_size: str = Field(..., description='Size of the model chunk.')
    model_internal_chunk_size: str = Field(
        ..., description='Size of the model internal chunk.'
    )
    postproc_chunk_size: str = Field(..., description='Size of the postproc chunk.')


class Sequencing(BaseModel):
    """Sequencing configuration dataclass"""

    model_config = ConfigDict(extra='allow')
    run_dates: RunDates
