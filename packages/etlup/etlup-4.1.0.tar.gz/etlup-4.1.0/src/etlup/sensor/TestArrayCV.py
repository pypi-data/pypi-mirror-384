from pydantic import ConfigDict, Field, AliasChoices, model_validator
from typing import Literal, List, Union, Annotated
import matplotlib.pyplot as plt
from ..plot_utils import convert_fig_to_html_img
from .. import base_model, jinja_env

class TestArrayCVV0(base_model.ConstructionBase):
    model_config = ConfigDict(json_schema_extra={
        'examples': [
            {
                "component": "FBK_LF1_ROL_054",
                "name": "Sensor Test Array CV",
                "measurement_date": "2023-01-01T12:00:00+01:00",
                "location": "UT",
                "user_created": "fsiviero",
                "version": "v0",
                "vgl": 158.176,
                "vbulk": 282.0,
                "side": "A", 
                "geometry": "1x1 PIN",
                "gain_category": "A",
                "voltage": [1.798e-9, 2.132e-9,2.389e-9,2.667e-9,2.991e-9,3.373e-9,3.882e-9,4.470e-9,5.163e-9,5.98e-9,6.888e-9,7.861e-9,8.972e-9,9.177e-9,1.135e-8,1.334e-8,1.591e-8,1.956e-8,2.418e-8,2.950e-8,4.237e-8,5.572e-6,0.0000257,0.0000342,0.0000405,0.0000441,0.0000454,0.0000519,0.0000652,0.0000757,0.00008891,0.0001137,0.000133,0.000151,0.000165,0.0001832,0.000201,0.000213,0.000224,0.000234,0.000245,0.000256,0.000271,0.000286,0.000301,0.000313,0.000325,0.000337,0.000349,0.000371,0.0003914,0.000406,0.000421,0.000435,0.000450,0.000465,0.000480,0.000496,0.000511,0.000528,0.000550,0.000574],
                "capacitance": [0.0,2.0,4.0,6.0,8.0,10.0,12.0,14.0,16.0,18.0,20.0,22.0,23.0,25.0,26.0,28.0,30.0,32.0,34.0,36.0,38.0,40.0,41.0,43.0,45.0,47.0,49.0,50.0,55.0,60.0,65.0,70.0,75.0,80.0,85.0,90.0,95.0,100.0,105.0,110.0,115.0,120.0,125.0,130.0,135.0,140.0,145.0,150.0,155.0,160.0,165.0,170.0,175.0,180.0,185.0,190.0,195.0,200.0,205.0,210.0,215.0,220.0],
            }
        ],
        'table': 'test',
        'component_types': ['Prototype LGAD', 'Prototype PIN'],
        'module_types': [],
        'description': 'Tests for QA-QC test structures'
    })

    name: Literal['Sensor Test Array CV'] = 'Sensor Test Array CV'
    version: Literal["v0"] = "v0"

    # Inline the data fields from TestArrayCVData
    vgl: Union[None, float] = Field(validation_alias=AliasChoices('vgl_V','vgl'))
    vbulk: Union[None, float] = Field(validation_alias=AliasChoices('vbulk_V','vbulk'))
    side: Union[None, Literal["A", "B"]] = Field(validation_alias=AliasChoices('side','Side'))
    geometry: Union[None, Literal["1x1 LGAD", "1x1 PIN", "1x2 PIN"]] = Field(validation_alias=AliasChoices('geometry','Geometry'))
    gain_category: Union[None, Literal["A", "B", "C"]] = Field(validation_alias=AliasChoices('gain_category','Gain Category'))
    voltage: Union[None, List[float]] = Field(validation_alias=AliasChoices('voltage','Voltage'))
    capacitance: Union[None, List[float]] = Field(validation_alias=AliasChoices('capacitance','Capacitance'))
    
    @model_validator(mode='after')
    def same_lengths(self):
        if self.voltage is not None and self.capacitance is not None:
            if len(self.voltage) != len(self.capacitance):
                raise ValueError(f'Voltage and Capacitance arrays should have the same lengths. Length of Voltage, Length of Capacitance = ({len(self.voltage)}, {len(self.capacitance)})')
        return self

    def plot(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        if self.voltage is not None and self.capacitance is not None:
            ax.plot(self.voltage, self.capacitance, label='CV Curve', marker='o', color='orange')
            ax.set_xlabel('Voltage (V)')
            ax.set_ylabel('Capacitance (pF)')

            ax.set_title(f'CV Curve')
            if self.gain_category is not None:
                ax.set_title(f'CV Curve - Gain Category: {self.gain_category}')

            ax.legend()
            ax.grid(True)
        return fig

    def html_display(self):
        display_data = {
            "vgl": self.vgl,
            "vbulk": self.vbulk,
            "side": self.side,
            "geometry": self.geometry,
            "gain_category": self.gain_category
        }
        fig = self.plot()

        template = jinja_env.get_template('sensors_plot.html')
        return template.render(
            plot = convert_fig_to_html_img(fig),
            display_data = display_data
        )

TestArrayCVType = Annotated[Union[TestArrayCVV0], Field(discriminator="version")]