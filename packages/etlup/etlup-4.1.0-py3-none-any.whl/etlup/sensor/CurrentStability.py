from pydantic import ConfigDict, Field, AliasChoices, model_validator
from typing import Literal, List, Union, Annotated
import matplotlib.pyplot as plt

from ..plot_utils import convert_fig_to_html_img
from .. import base_model as bm
from .. import jinja_env

class CurrentStabilityV0(bm.ConstructionBase):
    model_config = ConfigDict(json_schema_extra={
        'examples': [
            {
                "component": "FBK_LF1_ROL_054",
                "name": "Sensor Current Stability",
                "measurement_date": "2023-01-01T12:00:00+01:00",
                "location": "Universita e INFN Torino",
                "user_created": "fsiviero",
                "version": "v0",
                "current_stability": "A",
                "current": [1,2,3,4,5],
                "time": [1,2,3,4,5]
            }
        ],
        'table': 'test',
        'component_types': ['Prototype LGAD'],
        'module_types': [],
        'description': 'LGAD current stability test'
    })

    name: Literal['Sensor Current Stability'] = 'Sensor Current Stability'
    version: Literal["v0"] = "v0"
    
    # Inline the data fields from CurrentStabilityData
    current_stability: Union[None, Literal["A", "B", "C"]]
    current: Union[None, List[float]] = Field(validation_alias=AliasChoices('current','Current'))
    time: Union[None, List[float]] = Field(validation_alias=AliasChoices('time','Time'))

    @model_validator(mode='after')
    def same_lengths(self):
        if self.current is not None and self.time is not None:
            if len(self.current) != len(self.time):
                raise ValueError(f'Current and Time arrays should have the same lengths. Length of Current, Length of Time = ({len(self.current)}, {len(self.time)})')
        return self

    def plot(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        if self.current is not None and self.time is not None:
            ax.plot(self.time, self.current, marker='o', color='deeppink')
            ax.set_xlabel('Time')
            ax.set_ylabel('Current')
            ax.set_title(f'Time vs Current')
            ax.grid(True)
        return fig

    def html_display(self):
        display_data = {
            "current_stability": self.current_stability
        }
        fig = self.plot()

        template = jinja_env.get_template('sensors_plot.html')
        return template.render(
            plot = convert_fig_to_html_img(fig),
            display_data = display_data
        )

CurrentStabilityType = Annotated[Union[CurrentStabilityV0], Field(discriminator="version")]