from pydantic import ConfigDict, Field, AliasChoices, model_validator
from typing import Literal, List, Union, Annotated
import matplotlib.pyplot as plt

from ..plot_utils import convert_fig_to_html_img
from .. import base_model as bm
from .. import jinja_env

class GainCurveV0(bm.ConstructionBase):
    model_config = ConfigDict(json_schema_extra={
        'examples': [
            {
                "component": "FBK_LF1_ROL_054",
                "name": "Sensor Gain Curve",
                "measurement_date": "2023-01-01T12:00:00+01:00",
                "location": "UT",
                "user_created": "fsiviero",
                "version": "v0",
                "side": "A", 
                "geometry": "1x2 PIN",
                "gain": [1, 2, 3, 4, 5],
                "voltage": [1, 2, 3, 4, 5]
            }
        ],
        'table': 'test',
        'component_types': ['Prototype LGAD'],
        'module_types': [],
        'description': 'Tests for QA-QC test structures'
    })

    name: Literal['Sensor Gain Curve'] = 'Sensor Gain Curve'
    version: Literal["v0"] = "v0"
    
    # Inline the data fields from GainCurveData
    side: Union[None, Literal["A", "B"]] = Field(validation_alias=AliasChoices('side','Side'))
    geometry: Union[None, Literal["1x1 LGAD", "1x1 PIN", "1x2 PIN"]] = Field(validation_alias=AliasChoices('geometry','Geometry'))
    gain: Union[None, List[float]] = Field(validation_alias=AliasChoices('gain','Gain'))
    voltage: Union[None, List[float]] = Field(validation_alias=AliasChoices('voltage','Voltage'))
    
    @model_validator(mode='after')
    def same_lengths(self):
        if self.gain is not None and self.voltage is not None:
            if len(self.gain) != len(self.voltage):
                raise ValueError(f'Voltage and Gain arrays should have the same lengths. Length of Gain, Length of Voltage = ({len(self.gain)}, {len(self.voltage)})')
        return self

    def plot(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        if self.gain is not None and self.voltage is not None:
            ax.plot(self.gain, self.voltage, marker='o', color='purple')
            ax.set_xlabel('Gain')
            ax.set_ylabel('Voltage')
            ax.set_title(f'Gain vs Voltage')
            ax.grid(True)
        return fig

    def html_display(self):
        display_data = {
            "side": self.side,
            "geometry": self.geometry
        }
        fig = self.plot()

        template = jinja_env.get_template('sensors_plot.html')
        return template.render(
            plot = convert_fig_to_html_img(fig),
            display_data = display_data
        )

GainCurveType = Annotated[Union[GainCurveV0], Field(discriminator="version")]