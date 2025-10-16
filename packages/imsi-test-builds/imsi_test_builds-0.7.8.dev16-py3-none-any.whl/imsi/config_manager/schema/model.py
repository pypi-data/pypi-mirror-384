from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Union


class Model(BaseModel):
    """Model configuration Pydantic model"""

    model_config = ConfigDict(extra='allow')
    name: str = Field(..., description='Model name')
    source_id: str
    variant_id: str
    short_name: str
    description: str
    postproc_profile: str
    inherits_from: Optional[Union[List[str], str]] = None
    Scientifically_validated: Optional[bool] = None
    repository_tag: Optional[str] = None
    uxxx: Optional[str] = None
    prefix: Optional[str] = None
    model_filename_prefix: Optional[str] = None
    model_rs_filename_prefix: Optional[str] = None
