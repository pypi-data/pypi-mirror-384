from pydantic import ConfigDict, Field, AliasChoices, model_validator
from typing import Literal, List, Union, Annotated
import matplotlib.pyplot as plt
from ..plot_utils import convert_fig_to_html_img
from .. import base_model, jinja_env

class TestArrayIVV0(base_model.ConstructionBase):
    model_config = ConfigDict(json_schema_extra={
        'examples': [
            {
                "component": "FBK_LF1_ROL_054",
                "name": "Sensor Test Array IV",
                "measurement_date": "2023-01-01T12:00:00+01:00",
                "location": "UT",
                "user_created": "fsiviero",
                "version": "v0",
                "leakage_current_uA": 158.176,
                "breakdown_voltage_V": 282.0,
                "side": "A", 
                "geometry": "1x2 PIN",
                "current": [1.798e-9, 2.132e-9,2.389e-9,2.667e-9,2.991e-9,3.373e-9,3.882e-9,4.470e-9,5.163e-9,5.98e-9,6.888e-9,7.861e-9,8.972e-9,9.177e-9,1.135e-8,1.334e-8,1.591e-8,1.956e-8,2.418e-8,2.950e-8,4.237e-8,5.572e-6,0.0000257,0.0000342,0.0000405,0.0000441,0.0000454,0.0000519,0.0000652,0.0000757,0.00008891,0.0001137,0.000133,0.000151,0.000165,0.0001832,0.000201,0.000213,0.000224,0.000234,0.000245,0.000256,0.000271,0.000286,0.000301,0.000313,0.000325,0.000337,0.000349],
                "voltage": [0.0,2.0,4.0,6.0,8.0,10.0,12.0,14.0,16.0,18.0,20.0,22.0,23.0,25.0,26.0,28.0,30.0,32.0,34.0,36.0,38.0,40.0,41.0,43.0,45.0,47.0,49.0,50.0,55.0,60.0,65.0,70.0,75.0,80.0,85.0,90.0,95.0,100.0,105.0,110.0,115.0,120.0,125.0,130.0,135.0,140.0,145.0,150.0,155.0],
            }
        ],
        'table': 'test',
        'component_types': ['Prototype LGAD', 'Prototype PIN'],
        'module_types': [],
        'description': 'Tests for QA-QC test structures'
    })

    name: Literal['Sensor Test Array IV'] = 'Sensor Test Array IV'
    version: Literal["v0"] = "v0"
    
    # Inline the data fields from TestArrayIVData
    leakage_current_uA: Union[None, float] = Field(validation_alias=AliasChoices('leakage_current_uA','Leakage Current [uA]'))
    breakdown_voltage_V: Union[None, float] = Field(validation_alias=AliasChoices('breakdown_voltage_V','Breakdown Voltage [V]'))
    side: Union[None, Literal["A", "B"]] = Field(validation_alias=AliasChoices('side','Side'))
    geometry: Union[None, Literal["1x1 LGAD", "1x1 PIN", "1x2 PIN"]] = Field(validation_alias=AliasChoices('geometry','Geometry'))
    current: Union[None, List[float]] = Field(validation_alias=AliasChoices('current','Current'))
    voltage: Union[None, List[float]] = Field(validation_alias=AliasChoices('voltage','Voltage'))
    
    @model_validator(mode='after')
    def same_lengths(self):
        if self.current is not None and self.voltage is not None:
            if len(self.current) != len(self.voltage):
                raise ValueError(f'Current and voltage arrays should have the same lengths. Length of Current, Length of Voltage = ({len(self.current)}, {len(self.voltage)})')
        return self

    def plot(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        if self.voltage is not None and self.current is not None:
            ax.plot(self.voltage, self.current, label='IV Curve', marker='o', color='blue')
            ax.set_xlabel('Voltage (V)')
            ax.set_ylabel('Current (uA)')
            ax.set_title(f'IV Curve')
            ax.legend()
            ax.grid(True)
            ax.set_yscale('log')
        return fig

    def html_display(self):
        display_data = {
            "leakage_current_uA": self.leakage_current_uA,
            "breakdown_voltage_V": self.breakdown_voltage_V,
            "side": self.side,
            "geometry": self.geometry
        }
        fig = self.plot()

        template = jinja_env.get_template('sensors_plot.html')
        return template.render(
            plot = convert_fig_to_html_img(fig),
            display_data = display_data
        )

TestArrayIVType = Annotated[Union[TestArrayIVV0], Field(discriminator="version")]