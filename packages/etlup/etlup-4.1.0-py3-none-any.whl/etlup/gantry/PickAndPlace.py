from typing import Literal, List, Annotated, Union
from pydantic import ConfigDict, field_validator, Field
import numpy as np
import matplotlib.pyplot as plt
from ..plot_utils import convert_fig_to_html_img
from .. import base_model

class PickAndPlaceV0(base_model.ConstructionBase):
    model_config = ConfigDict(json_schema_extra={
        'examples': [
            {
                "module": "PBU0001",
                "component": "PE0001",
                "component_pos": 1, 
                "version": "v0",
                "name": "pick and place survey",
                "measurement_date": "2023-01-01T12:00:00+01:00",
                "location": "BU",
                "user_created": "hayden",
                "stage": "precure",
                "target": [639.141118, 287.244992, 64.009534,-0.048954],
                "actual": [639.141118, 287.244992, 64.009534,-0.048954],
                "delta":  [639.141118, 287.244992, 64.009534,-0.048954]
            },
            {
                "module": "PBU0001",
                "component": "PE0001",
                "component_pos": 1, 
                "version": "v0",
                "name": "pick and place survey",
                "measurement_date": "2023-01-01T12:00:00+01:00",
                "stage": "precure",
                "location": "BU",
                "user_created": "hayden",
                "stage": "postcure",
                "target": [639.141118, 287.244992, 64.009534,-0.048954],
                "actual": [639.141118, 287.244992, 64.009534,-0.048954],
                "delta":  [639.141118, 287.244992, 64.009534,-0.048954]
            }
        ],
        'table': 'assembly',
        'component_types': ['Production Subassembly', 'PreProduction Subassembly', 'Ghost ETROC'],
        'module_types': ['PreProduction', 'Production', 'Digital'],
        'description': 'Gantry assembly step to measure the position of the subassemblies on the module (either before curing or after curing)'
    })
    name: Literal['pick and place survey']
    version: Literal["v0"] = "v0"

    stage: Literal["precure", "postcure"]
    target: List[float]
    actual: List[float]
    delta: List[float]

    @field_validator('target', 'actual', 'delta', mode="after")
    @classmethod
    def length_check(cls, v):
        if len(v) != 4:
            raise ValueError("The required length is 4 for target, actual and delta. It is [x, y, z, rot]")
        return v

    def plot(self):
        """
        A vector like [dX (um), dY (um), dZ (um), dRot (degrees)]
        """
        assy_data = np.array(self.delta)
        fig, ax = plt.subplots(figsize=(4, 4))
        # add your plot command here
        ax.plot(assy_data[0]*1000, assy_data[1]*1000, 'o') # 'o' specifies points
        ax.set_xlabel('dx')
        ax.set_ylabel('dy')
        ax.grid()

        ax.set_title(f'Pick and Place Alignment (um)') 
        ax.set_xlim([-20, 20])
        ax.set_ylim([-20, 20])                

        ax.axhline(0, color='black', linewidth=1)
        ax.axvline(0, color='black', linewidth=1)
        return fig
    
    def html_display(self):
        fig = self.plot()
        return convert_fig_to_html_img(fig)
    
PickAndPlaceType = Annotated[Union[PickAndPlaceV0], Field(discriminator="version")]