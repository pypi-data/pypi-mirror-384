from pydantic import ConfigDict, Field, AliasChoices, model_validator
from typing import Literal, Optional, List, Union, Annotated
import matplotlib.pyplot as plt
from ..plot_utils import convert_fig_to_html_img
from .. import base_model
from .. import jinja_env

class GainLayerUniformityV0(base_model.ConstructionBase):
    model_config = ConfigDict(json_schema_extra={
        'examples': [
            {
                "component": "FBK_LF1_ROL_054",
                "name": "Sensor Gain Layer Uniformity",
                "measurement_date": "2023-01-01T12:00:00+01:00",
                "location": "Universita e INFN Torino",
                "user_created": "fsiviero",
                "version": "v0",
                "gain_layer_uniformity": "A",
                "capacitance": [[1],[2],[3],[4],[5]],
                "voltage": [[1],[2],[3],[4],[5]]
            }
        ],
        'table': 'test',
        'component_types': ['Prototype LGAD'],
        'module_types': [],
        'description': 'LGAD gain layer uniformity test'
    })

    name: Literal['Sensor Gain Layer Uniformity'] = 'Sensor Gain Layer Uniformity'
    version: Literal["v0"] = "v0"
    
    # Inline the data fields from GainLayerUniformityData
    gain_layer_uniformity: Union[None, Literal["A", "B", "C"]] = Field(validation_alias=AliasChoices('gain_layer_uniformity','Gain Layer Uniformity'))
    capacitance: Union[None, List[List[float]]] = Field(validation_alias=AliasChoices('capacitance','Capacitance'))
    voltage: Union[None, List[List[float]]] = Field(validation_alias=AliasChoices('voltage','Voltage'))

    @model_validator(mode='after')
    def same_lengths(self):
        if self.capacitance is not None and self.voltage is not None:
            if len(self.capacitance) != len(self.voltage):
                raise ValueError(f'Capacitance and voltage arrays should have the same lengths. Length of Capacitance, Length of Voltage = ({len(self.capacitance)}, {len(self.voltage)})')
        return self
    
    @model_validator(mode='after')
    def max_length(self):
        if self.capacitance is not None and self.voltage is not None:
            if len(self.capacitance) > 256 or len(self.voltage) > 256:
                raise ValueError(f'Length of Capacitance, Length of Voltage = ({len(self.capacitance)}, {len(self.voltage)}) one of these is longer than 256, the max number of arrays.')
        return self

    def plot(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        if self.capacitance is not None and self.voltage is not None:
            for c, v in zip(self.capacitance, self.voltage):
                ax.plot(c, v)
            ax.set_xlabel('Capacitance (pF)')
            ax.set_ylabel('Voltage')
            ax.set_title(f'Capacitance vs Voltage')
            ax.grid(True)
        return fig

    def html_display(self):
        display_data = {
            "gain_layer_uniformity": self.gain_layer_uniformity
        }
        fig = self.plot()

        template = jinja_env.get_template('sensors_plot.html')
        return template.render(
            plot = convert_fig_to_html_img(fig),
            display_data = display_data
        )

GainLayerUniformityType = Annotated[Union[GainLayerUniformityV0], Field(discriminator="version")]