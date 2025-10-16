from typing import Union, Optional
from pydantic import BaseModel, field_validator, model_validator, AwareDatetime, ConfigDict, PastDate
from datetime import datetime, date
import pytz
from .example_formatter import ExampleFormatterMixin
    
class ConstructionBase(BaseModel, ExampleFormatterMixin):
    model_config = ConfigDict(extra="forbid") #forbid any extra fields

    measurement_date: Union[PastDate, AwareDatetime] #force times to have timezone
    location: str
    user_created: str

    # make all 3 optional but enforce atleast module or component
    # in db, you can just enforce by the expected component type and module type
    module: Optional[str] = None
    component: Optional[str] = None
    component_pos: Optional[int] = None
    
    @field_validator('*')
    @classmethod
    def empty_str_to_none(cls, v):
        if isinstance(v, str) and v.strip() == '':
            return None
        return v
    
    @model_validator(mode='after')
    def enforce_part(self):
        """Makes sure a part is given, either module or component"""
        if not (self.module or self.component or self.component_pos):
            raise ValueError("Please specify a part")
        elif self.component_pos and not self.module:
            raise ValueError("Component position alone is not enough to identify a part for a test.")
        return self
    
    @classmethod
    def get_subclasses(cls):
        return tuple(cls.__subclasses__())

    @field_validator("measurement_date")
    @classmethod
    def validate_measurement_date(cls, v):
        if type(v) is date: #cannot do isinstance to differentiate between datetime and date objects!
            return v
        if not type(v) is datetime:
            raise ValueError(f"Inputted datetime is not a datetime object it is {type(v)}")
        if v.tzinfo is None:
            #need to do this otherwise it has a default for no timezone given!
            raise ValueError("Measurement data has no time zone information, see https://en.wikipedia.org/wiki/ISO_8601")
        
        #if measurement date has tz information, convert from that TZ to UTC time!
        return v.astimezone(pytz.utc) 
    
    def get_schema_val(self, key):
        """
        Gets you anything in the json schema, could be description, module_types, etc...
        """
        json_schema = self.model_config.get("json_schema_extra")
        return json_schema.get(key)
    
    