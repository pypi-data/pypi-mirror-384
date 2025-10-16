from pydantic import ConfigDict, Field, AliasChoices, model_validator
from typing import Literal, List, Union, Annotated
import matplotlib.pyplot as plt

from ..plot_utils import convert_fig_to_html_img
from .. import base_model
from .. import jinja_env  # relative to the top-level package "etlup"

class ChargeCollectionV0(base_model.ConstructionBase):
    model_config = ConfigDict(json_schema_extra={
        'examples': [
            {
                "component": "FBK_LF1_ROL_054",
                "name": "Sensor Charge Collection",
                "measurement_date": "2023-01-01T12:00:00+01:00",
                "location": "UT",
                "user_created": "fsiviero",
                "version": "v0",
                "irradiation_level": 1E15,
                "side": "B", 
                "geometry": "1x2 PIN",
                "measuring_temperature": -20,
                "charge": [1,2,3,4,5],
                "voltage": [1,2,3,4,5],
            }
        ],
        'table': 'test',
        'component_types': ['Prototype LGAD'],
        'module_types': [],
        'description': 'Tests for QA-QC test structures'
    })

    name: Literal['Sensor Charge Collection'] = 'Sensor Charge Collection'
    version: Literal["v0"] = "v0"
    
    # Inline the data fields from ChargeCollectionData
    side: Union[None, Literal["A", "B"]]      = Field(validation_alias=AliasChoices('side','Side'))
    geometry: Union[None, Literal["1x1 LGAD", 
                                  "1x1 PIN", 
                                  "1x2 PIN"]] = Field(validation_alias=AliasChoices('geometry','Geometry'))
    irradiation_level: Union[None, float]     = Field(validation_alias=AliasChoices('irradiation_level','Irradiation Level'))
    measuring_temperature: Union[None, float] = Field(validation_alias=AliasChoices('measuring_temperature','Measuring Temperature'))
    voltage: Union[None, List[float]]         = Field(validation_alias=AliasChoices('voltage','Voltage'))
    charge: Union[None, List[float]]          = Field(validation_alias=AliasChoices('charge','Charge'))

    @model_validator(mode='after')
    def same_lengths(self):
        if self.charge is not None and self.voltage is not None:
            if len(self.charge) != len(self.voltage):
                raise ValueError(f'Charge and Voltage arrays should have the same lengths. Length of Charge, Length of Voltage = ({len(self.charge)}, {len(self.voltage)})')
        return self

    def plot(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        if self.voltage is not None and self.charge is not None:
            ax.plot(self.voltage, self.charge, marker='o', color='green')
            ax.set_xlabel('Voltage')
            ax.set_ylabel('Charge')
            ax.set_title(f'Charge vs Voltage')
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

# class ChargeCollectionV1(ChargeCollectionV0):
#     version: Literal['v1'] = "v1"
#     boop: str

ChargeCollectionType = Annotated[Union[ChargeCollectionV0], Field(discriminator="version")]
