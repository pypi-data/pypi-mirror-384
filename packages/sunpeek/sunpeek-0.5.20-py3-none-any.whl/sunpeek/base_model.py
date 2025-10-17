from pydantic import BaseModel as PydanticBaseModel
from pydantic import field_validator, ConfigDict
import pint
from typing import List
import numpy as np

class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
        use_enum_values=True,
        populate_by_name=True,
        alias_generator=None
    )

    @field_validator('*', mode='before')
    @classmethod
    def make_strings(cls, v):
        if isinstance(v, pint.Unit):
            v = str(v)
            return v
        # elif isinstance(v, pint.Quantity):
        #     return str(v.units)
        # elif isinstance(v, cmp.Collector):
        #     return v.name
        return v

    @field_validator('units', 'native_unit', mode='before', check_fields=False)
    @classmethod
    def validate_units(cls, v):
        if isinstance(v, pint.Quantity):
            return str(v.units)
        return v


def np_to_list(val):
    if isinstance(val, np.ndarray) and val.ndim == 1:
        return list(val)
    elif isinstance(val, np.ndarray) and val.ndim > 1:
        out = []
        for array in list(val):
            out.append(np_to_list(array))
        return out
    return val


class Quantity(BaseModel):
    magnitude: float | List[float] | List[List[float]]
    units: str

    @field_validator('magnitude', mode='before')
    @classmethod
    def convert_numpy(cls, val):
        return np_to_list(val)

    @field_validator('units', mode='before')
    @classmethod
    def pretty_unit(cls, val):
        if isinstance(val, pint.Unit):
            return f"{val:~P}"
        return val