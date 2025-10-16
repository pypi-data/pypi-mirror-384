from pydantic import ConfigDict, Field, AliasChoices, model_validator
from typing import Literal, Optional, List, Union, Annotated
import matplotlib.pyplot as plt

from ..plot_utils import convert_fig_to_html_img
from .. import base_model, jinja_env

class TimeResolutionV0(base_model.ConstructionBase):
    model_config = ConfigDict(json_schema_extra={
        'examples': [
            {
                "component": "FBK_LF1_ROL_054",
                "name": "Sensor Time Resolution",
                "measurement_date": "2023-01-01T12:00:00+01:00",
                "location": "UT",
                "user_created": "fsiviero",
                "version": "v0",
                "irradiation_level": 1E15,
                "side": "B", 
                "geometry": "1x2 PIN",
                "measuring_temperature": -20,
                "time_resolution": [1,2,3,4,5],
                "voltage": [1,2,3,4,5],
            }
        ],
        'table': 'test',
        'component_types': ['Prototype LGAD'],
        'module_types': [],
        'description': 'Tests for QA-QC test structures'
    })

    name: Literal['Sensor Time Resolution'] = 'Sensor Time Resolution'
    version: Literal["v0"] = "v0"
    
    # Inline the data fields from TimeResolutionData
    side: Union[None, Literal["A", "B"]] = Field(validation_alias=AliasChoices('side','Side'))
    geometry: Union[None, Literal["1x1 LGAD", "1x1 PIN", "1x2 PIN"]] = Field(validation_alias=AliasChoices('geometry','geometry'))
    irradiation_level: Union[None, float] = Field(validation_alias=AliasChoices('irradiation_level','Irradiation Level'))
    measuring_temperature: Union[None, float] = Field(validation_alias=AliasChoices('measuring_temperature','Measuring Temperature'))
    time_resolution: Union[None, List[float]] = Field(validation_alias=AliasChoices('time_resolution','Time Resolution'))
    voltage: Union[None, List[float]] = Field(validation_alias=AliasChoices('voltage','Voltage'))
    
    @model_validator(mode='after')
    def same_lengths(self):
        if self.time_resolution is not None and self.voltage is not None:
            if len(self.time_resolution) != len(self.voltage):
                raise ValueError(f'Time Resolution and Voltage arrays should have the same lengths. Length of Time Resolution, Length of Voltage = ({len(self.time_resolution)}, {len(self.voltage)})')
        return self

    def plot(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        if self.voltage is not None and self.time_resolution is not None:
            ax.plot(self.voltage, self.time_resolution, marker='o', color='red')
            ax.set_xlabel('Voltage')
            ax.set_ylabel('Time Resolution')
            ax.set_title(f'Voltage vs Time Resolution')
            ax.grid(True)
        return fig

    def html_display(self):
        display_data = {
            "side": self.side,
            "geometry": self.geometry,
            "irradiation_level": self.irradiation_level,
            "measuring_temperature": self.measuring_temperature
        }
        fig = self.plot()

        template = jinja_env.get_template('sensors_plot.html')
        return template.render(
            plot = convert_fig_to_html_img(fig),
            display_data = display_data
        )

TimeResolutionType = Annotated[Union[TimeResolutionV0], Field(discriminator="version")]