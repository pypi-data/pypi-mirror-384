from .Baseline import BaselineV0
from ..plot_utils import module_plot
import numpy as np
from pydantic import ConfigDict, Field
from typing import Literal, Annotated, Union

class NoisewidthV0(BaselineV0):
    model_config = ConfigDict(json_schema_extra={
        'examples': [
            {
                "module": "PBU0001",
                "version": "v0",
                "name": "noisewidth",
                "measurement_date": "2023-01-01T12:00:00+01:00",
                "location": "BU",
                "user_created": "hayden",
                'ambient_celcius': 20,
                "etroc_0_Vtemp": 2713,
                "etroc_1_Vtemp": 2713,
                '3':np.ones((16,16), dtype=int).tolist(),
                '1':np.ones((16,16), dtype=int).tolist(),
                '2':np.ones((16,16), dtype=int).tolist(),
                '0':np.ones((16,16), dtype=int).tolist()
            },   
        ],
        'table': 'test',
        'component_types': [],
        'module_types': ['Production', 'PreProduction', 'Digital', 'Prototype', 'Fake Production'],
        'description': 'Baseline / Noisewidth for a module. Each position follows the standard of this module pcb version in this lablog, it should never change again: https://bu.nebraskadetectorlab.com/submission/4879'
    })
    name: Literal['noisewidth'] = 'noisewidth'

    def plot(self):
        """Plot all 4 16x16 arrays (3, 2, 1, 0) in a 2x2 subplot layout"""
        return module_plot(
            self,
            vmin = 0,
            vmax = 16
        )
    
NoisewidthType = Annotated[Union[NoisewidthV0], Field(discriminator="version")]