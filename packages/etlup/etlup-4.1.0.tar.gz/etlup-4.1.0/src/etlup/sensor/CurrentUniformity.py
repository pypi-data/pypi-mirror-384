from pydantic import ConfigDict, Field, AliasChoices, model_validator
from typing import Literal, List, Union, Annotated
import matplotlib.pyplot as plt

from ..plot_utils import convert_fig_to_html_img
from .. import base_model
from .. import jinja_env

class CurrentUniformityV0(base_model.ConstructionBase):
    model_config = ConfigDict(json_schema_extra={
        'examples': [
            {
                "component": "FBK_LF1_ROL_054",
                "name": "Sensor Current Uniformity",
                "measurement_date": "2023-01-01T12:00:00+01:00",
                "location": "Universita e INFN Torino",
                "user_created": "fsiviero",
                "version": "v0",
                "current_uniformity": "A",
                "current": [[1,2,3,4,5],[2,3,4,5,6],[3,4,5,6,7],[4,5,6,7,8],[5,6,7,8,9]],
                "voltage": [[1,2,3,4,5],[2,3,4,5,6],[3,4,5,6,7],[4,5,6,7,8],[5,6,7,8,9]]
            }
        ],
        'table': 'test',
        'component_types': ['Prototype LGAD'],
        'module_types': [],
        'description': 'LGAD current uniformity test'
    })

    name: Literal['Sensor Current Uniformity'] = 'Sensor Current Uniformity'
    version: Literal["v0"] = "v0"
    
    # Inline the data fields from CurrentUniformityData
    current_uniformity: Union[None, Literal["A", "B", "C"]] = Field(validation_alias=AliasChoices('current_uniformity','Current Uniformity'))
    current: Union[None, List[List[float]]] = Field(validation_alias=AliasChoices('current','Current'))
    voltage: Union[None, List[List[float]]] = Field(validation_alias=AliasChoices('voltage','Voltage'))

    @model_validator(mode='after')
    def same_lengths(self):
        if self.current is not None and self.voltage is not None:
            if len(self.current) != len(self.voltage):
                raise ValueError(f'Current and voltage arrays should have the same lengths. Length of Current, Length of Voltage = ({len(self.current)}, {len(self.voltage)})')
        return self
    
    @model_validator(mode='after')
    def max_length(self):
        if self.current is not None and self.voltage is not None:
            if len(self.current) > 256 or len(self.voltage) > 256:
                raise ValueError(f'Length of Current, Length of Voltage = ({len(self.current)}, {len(self.voltage)}) one of these is longer than 256, the max number of arrays.')
        return self

    def plot(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        if self.current is not None and self.voltage is not None:
            for c, v in zip(self.current, self.voltage):
                ax.plot(c, v)
            ax.set_xlabel('Current')
            ax.set_ylabel('Voltage')
            ax.set_title(f'Current vs Voltage')
            ax.grid(True)
        return fig

    def html_display(self):
        display_data = {
            "current_uniformity": self.current_uniformity
        }
        fig = self.plot()

        template = jinja_env.get_template('sensors_plot.html')
        return template.render(
            plot = convert_fig_to_html_img(fig),
            display_data = display_data
        )

CurrentUniformityType = Annotated[Union[CurrentUniformityV0], Field(discriminator="version")]