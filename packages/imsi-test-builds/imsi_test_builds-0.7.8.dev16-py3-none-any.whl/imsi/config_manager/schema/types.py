from typing import Annotated
from pydantic.functional_validators import BeforeValidator

# Custom type that coerces integers to strings from the config
DateCoerce = Annotated[
    str, BeforeValidator(lambda v: str(v) if isinstance(v, int) else v)
]
