from pydantic import BaseModel, ConfigDict


class PostProcessing(BaseModel):
    """Post-processing configuration dataclass"""

    # Current this is just a big dict, ingested straight from
    # what is in the database. Almost certainly though it will
    # need to be developed to make it more useful.
    # Likely, these settings need to also appear and be modifiable within
    # experiment definitions (ala components).
    model_config = ConfigDict(extra='allow')
