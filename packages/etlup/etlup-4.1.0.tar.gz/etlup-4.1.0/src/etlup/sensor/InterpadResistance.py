from pydantic import ConfigDict, Field
from typing import Literal, Union, Annotated
from .. import base_model
from .. import jinja_env

class InterpadResistanceV0(base_model.ConstructionBase):
    model_config = ConfigDict(json_schema_extra={
        'examples': [
            {
                "component": "FBK_LF1_ROL_054",
                "name": "Sensor Interpad Resistance",
                "measurement_date": "2023-01-01T12:00:00+01:00",
                "location": "Universita e INFN Torino",
                "user_created": "fsiviero",
                "version": "v0",
                "interpad_resistance_GOhm": 0.1,
            }
        ],
        'table': 'test',
        'component_types': ['Prototype LGAD'],
        'module_types': [],
        'description': 'LGAD interpad resistance test'
    })

    name: Literal['Sensor Interpad Resistance'] = 'Sensor Interpad Resistance'
    version: Literal["v0"] = "v0"
    
    # Inline the data field from InterpadResistanceData
    interpad_resistance_GOhm: float

    def plot(self):
        return None

    def html_display(self):
        display_data = {
            "interpad_resistance_GOhm": self.interpad_resistance_GOhm
        }
        template = jinja_env.get_template('sensors_plot.html')
        return template.render(
            plot = None,
            display_data = display_data
        )

InterpadResistanceType = Annotated[Union[InterpadResistanceV0], Field(discriminator="version")]