from pydantic import ConfigDict, model_validator, Field, AliasChoices
import numpy as np
from ..plot_utils import convert_fig_to_html_img, module_plot
from ..  import base_model as bm
from typing import Optional, Literal, Annotated, Union
from .. custom_types import PixArr

class BaselineV0(bm.ConstructionBase):
    model_config = ConfigDict(json_schema_extra={
        'examples': [
            {
                "module": "PBU0001",
                "version": "v0",
                "name": "baseline",
                "measurement_date": "2023-01-01T12:00:00+01:00",
                "location": "BU",
                "user_created": "hayden",
                'ambient_celcius': 20,
                "etroc_0_Vtemp": 2713,
                "etroc_1_Vtemp": 2713,
                "etroc_2_Vtemp": 2713,
                "etroc_3_Vtemp": 2713,
                "bias_volts": 150,
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
    name: Literal['baseline'] = 'baseline'
    version: Literal["v0"] = "v0"
    module: str

    ambient_celcius: Optional[float] = None
    etroc_0_Vtemp: Optional[int] = None # raw voltage temperature (uses lpgbt adc calibrations)
    etroc_1_Vtemp: Optional[int] = None
    etroc_2_Vtemp: Optional[int] = None
    etroc_3_Vtemp: Optional[int] = None
    bias_volts: Optional[float] = None

    pos_3: Optional[PixArr] = Field(
        default=None,
        validation_alias=AliasChoices('3', 'U4', "pos_3"),
        serialization_alias="3"
    )
    pos_1: Optional[PixArr] = Field(
        default=None,
        validation_alias=AliasChoices('1', 'U3', "pos_1"),
        serialization_alias="1"
    )
    pos_2: Optional[PixArr] = Field(
        default=None,
        validation_alias=AliasChoices('2', 'U2', "pos_2"),
        serialization_alias="2"
    )
    pos_0: Optional[PixArr] = Field(
        default=None,
        validation_alias=AliasChoices('0', 'U1', "pos_0"),
        serialization_alias="0"
    )

    # Read-only convenience properties matching old names
    @property
    def U4(self):
        return self.pos_3
    @property
    def U3(self):
        return self.pos_1
    @property
    def U2(self):
        return self.pos_2
    @property
    def U1(self):
        return self.pos_0

    @model_validator(mode='before')
    @classmethod
    def coerce_int_keys_to_str(cls, value):
        # Accept both {"0": ...} and {0: ...}
        if isinstance(value, dict):
            return { str(k): v for k, v in value.items() }
        return value

    @model_validator(mode='after')
    def at_least_one_required(self):
        if not any([self.pos_0, self.pos_1, self.pos_2, self.pos_3]):
            raise ValueError("At least one position must be provided")
        return self

    def plot(self):
        """Plot all 4 16x16 arrays (3, 2, 1, 0) in a 2x2 subplot layout"""
        matrices = [self.pos_3, self.pos_1, self.pos_2, self.pos_0]
        # vmin = 0
        # vmax = 16
        vmin = min([np.min(matrix) for matrix in matrices if matrix])
        vmax = max([np.max(matrix) for matrix in matrices if matrix])
        
        return module_plot(
            self,
            vmin=vmin,
            vmax=vmax
        )
    
    def _db_validation(self, session, models):
        """Perform database validation to check the provided module has positions in the provided data"""
        module = session.query(models.Module).filter(models.Module.serial_number == self.module).first()
        if not module:
            raise ValueError(f"This module {self.module} not found in database")
        if not module.components:
            raise ValueError(f"This module does not have any components. Please contact an admin.")
        
        # Get the positions that have data provided
        provided_positions = []
        if self.pos_3 is not None:
            provided_positions.append(3)
        if self.pos_1 is not None:
            provided_positions.append(1)
        if self.pos_2 is not None:
            provided_positions.append(2)
        if self.pos_0 is not None:
            provided_positions.append(0)
        
        # Check if the provided positions match the component positions in the database
        db_positions = [comp.component_pos for comp in module.components]
        for position in provided_positions:
            if position not in db_positions:
                raise ValueError(f"Position {position} provided in data but no component found at this position in the database for module {self.module}")

    def html_display(self):
        fig = self.plot()
        return convert_fig_to_html_img(fig)



BaselineType = Annotated[Union[BaselineV0], Field(discriminator="version")]