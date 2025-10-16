from pydantic import ConfigDict, Field, AliasChoices
from typing import Literal, Union, Annotated
from .. import base_model, jinja_env

class InterpadWidthV0(base_model.ConstructionBase):
    model_config = ConfigDict(json_schema_extra={
        'examples': [
            {
                "component": "FBK_LF1_ROL_054",
                "name": "Sensor Interpad Width",
                "measurement_date": "2023-01-01T12:00:00+01:00",
                "location": "UT",
                "user_created": "fsiviero",
                "version": "v0",
                "side": "B", 
                "geometry": "1x1 LGAD",
                "irradiation_level": 1E15,
                "interpad_width": 1.1,
            }
        ],
        'table': 'test',
        'component_types': ['Prototype LGAD'],
        'module_types': [],
        'description': 'Tests for QA-QC test structures'
    })

    name: Literal['Sensor Interpad Width'] = 'Sensor Interpad Width'
    version: Literal["v0"] = "v0"
    
    # Inline the data fields from InterpadWidthData
    side: Union[None, Literal["A", "B"]] = Field(validation_alias=AliasChoices('side','Side'))
    geometry: Union[None, Literal["1x1 LGAD", "1x1 PIN", "1x2 PIN"]] = Field(validation_alias=AliasChoices('geometry','Geometry'))
    irradiation_level: Union[None, float] = Field(validation_alias=AliasChoices('irradiation_level','Irradiation Level'))
    interpad_width: Union[None, float] = Field(validation_alias=AliasChoices('interpad_width','Interpad Width'))

    def plot(self):
        return None

    def html_display(self):
        display_data = {
            "side": self.side,
            "geometry": self.geometry,
            "irradiation_level": self.irradiation_level,
            "interpad_width": self.interpad_width
        }
        template = jinja_env.get_template('sensors_plot.html')
        return template.render(
            plot = None,
            display_data = display_data
        )

InterpadWidthType = Annotated[Union[InterpadWidthV0], Field(discriminator="version")]