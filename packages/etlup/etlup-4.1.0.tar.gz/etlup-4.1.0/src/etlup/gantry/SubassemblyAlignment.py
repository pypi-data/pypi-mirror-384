from pydantic import ConfigDict, Field
from typing import Union, Annotated, Literal, List
import matplotlib.pyplot as plt
import numpy as np
from .. import base_model as bm
from ..plot_utils import convert_fig_to_html_img

class SubassemblyAlignmentV0(bm.ConstructionBase):
    model_config = ConfigDict(json_schema_extra={
        'examples': [
            {
                "component": "PS0001",
                "name": "subassembly alignment",
                "measurement_date": "2023-01-01T12:00:00+01:00",
                "location": "BU",
                "user_created": "hayden",
                "version": "v0",
                "target": [639.141118, 287.244992, 64.009534,-0.048954],
                "actual": [639.141118, 287.244992, 64.009534,-0.048954],
                "delta":  [639.141118, 287.244992, 64.009534,-0.048954]
            },
        ],
        'table': 'assembly',
        'component_types': ['Production Subassembly', 'PreProduction Subassembly'],
        'module_types': [],
        'description': 'An assembly measurement for the relative alignment between the centers of the LGAD and ETROC'
    })
    name: Literal['subassembly alignment']
    version: Literal["v0"] = "v0"

    target: List[float]
    actual: List[float]
    delta: List[float]

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
        #have these be the default values and if the point goes outside it just zooms out with some wiggle room
        ax.set_xlim([-200, 200])
        ax.set_ylim([-200, 200])
        ax.set_title(f'ETROC+LGAD Alignment (um)') 
        
        ax.axhline(0, color='black', linewidth=1)
        ax.axvline(0, color='black', linewidth=1)
        return fig
    
    def html_display(self):
        fig = self.plot()
        return convert_fig_to_html_img(fig)
    
SubassemblyAlignmentType = Annotated[Union[SubassemblyAlignmentV0], Field(discriminator="version")]