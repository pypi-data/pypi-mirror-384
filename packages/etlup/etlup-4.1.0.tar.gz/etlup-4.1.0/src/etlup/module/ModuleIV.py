from pydantic import ConfigDict, Field, model_validator
from typing import Union, Annotated, Literal, List
import matplotlib.pyplot as plt
import numpy as np
from .. import base_model as bm
from ..plot_utils import convert_fig_to_html_img

class ModuleIVV0(bm.ConstructionBase):
    model_config = ConfigDict(json_schema_extra={
        'examples': [
            {
                "module": "MV4002",
                "component_pos": 2,
                "name": "module iv",
                "measurement_date": "2023-01-01T12:00:00+01:00",
                "location": "BU",
                "user_created": "hayden",
                "version": "v0",
                "current": [0,1,2,3,4,5],
                "voltage": [0,1,2,3,4,5],
                "k_factor":  [0,1,2,3,4,5]
            },
        ],
        'table': 'test',
        'module_types': ["Prototype"],
        'description': 'IV curve of a sensor on a module.'
    })
    name: Literal['module iv'] = "module iv"
    version: Literal["v0"] = "v0"

    module: str
    component_pos: int = Field(ge=0, le=3, description="Component position (0-3)")
    
    current: List[float]
    voltage: List[float]
    k_factor: List[float]

    @model_validator(mode='after')
    def same_lengths(self):
        if self.current is not None and self.voltage is not None:
            if len(self.current) != len(self.voltage):
                raise ValueError(f'Current and voltage arrays should have the same lengths. Length of Current, Length of Voltage = ({len(self.current)}, {len(self.voltage)})')
        return self

    def plot(self):
        """
        A vector like [dX (um), dY (um), dZ (um), dRot (degrees)]
        """
        print("not implemented.")

        fig, ax = plt.subplots(figsize=(4, 4))
        return fig
    
    def html_display(self):
        fig = self.plot()
        return convert_fig_to_html_img(fig)
    
ModuleIVType = Annotated[Union[ModuleIVV0], Field(discriminator="version")]