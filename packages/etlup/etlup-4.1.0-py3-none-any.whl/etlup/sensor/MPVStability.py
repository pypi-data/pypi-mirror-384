from pydantic import ConfigDict, Field, AliasChoices, model_validator
from typing import Literal, List, Union, Annotated
import matplotlib.pyplot as plt

from ..plot_utils import convert_fig_to_html_img
from .. import base_model, jinja_env

class MPVStabilityV0(base_model.ConstructionBase):
    model_config = ConfigDict(json_schema_extra={
        'examples': [
            {
                "component": "FBK_LF1_ROL_054",
                "name": "Sensor MPV Stability",
                "measurement_date": "2023-01-01T12:00:00+01:00",
                "location": "UT",
                "user_created": "fsiviero",
                "version": "v0",
                "side": "B", 
                "geometry": "1x1 LGAD",
                "mpv": [1,2,3,4,5],
                "time": [1,2,3,4,5],
                "mpv_stability": 0.2
            }
        ],
        'table': 'test',
        'component_types': ['Prototype LGAD'],
        'module_types': [],
        'description': 'Tests for QA-QC test structures'
    })

    name: Literal['Sensor MPV Stability'] = 'Sensor MPV Stability'
    version: Literal["v0"] = "v0"
    
    # Inline the data fields from MPVStabilityData
    side: Union[None, Literal["A", "B"]] = Field(validation_alias=AliasChoices('side','Side'))
    geometry: Union[None, Literal["1x1 LGAD", "1x1 PIN", "1x2 PIN"]] = Field(validation_alias=AliasChoices('geometry','Geometry'))
    mpv: Union[None, List[float]] = Field(validation_alias=AliasChoices('mpv','MPV'))
    time: Union[None, List[float]] = Field(validation_alias=AliasChoices('time','Time'))
    mpv_stability: Union[None, float] = Field(validation_alias=AliasChoices('mpv_stability','MPV Stability'))
    
    @model_validator(mode='after')
    def same_lengths(self):
        if self.mpv is not None and self.time is not None:
            if len(self.mpv) != len(self.time):
                raise ValueError(f'MPV and Time arrays should have the same lengths. Length of MPV, Length of Time = ({len(self.mpv)}, {len(self.time)})')
        return self

    def plot(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        if self.time is not None and self.mpv is not None:
            ax.plot(self.time, self.mpv, marker='o', color='black')
            ax.set_xlabel('Time')
            ax.set_ylabel('MPV')
            ax.set_title(f'MPV Stability')
            ax.grid(True)
        return fig

    def html_display(self):
        display_data = {
            "side": self.side,
            "geometry": self.geometry,
            "mpv_stability": self.mpv_stability
        }
        fig = self.plot()

        template = jinja_env.get_template('sensors_plot.html')
        return template.render(
            plot = convert_fig_to_html_img(fig),
            display_data = display_data
        )

MPVStabilityType = Annotated[Union[MPVStabilityV0], Field(discriminator="version")]