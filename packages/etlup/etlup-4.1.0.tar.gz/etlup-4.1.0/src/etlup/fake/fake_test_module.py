from pydantic import ConfigDict, Field
from typing import Literal, Union, Annotated
import matplotlib.pyplot as plt
from ..plot_utils import convert_fig_to_html_img
from .. import base_model as bm

class FakeTestModuleV0(bm.ConstructionBase):
    model_config = ConfigDict(json_schema_extra={
        'examples': [
            {
                "module": "PBU0001",
                "component": "TYL4U001",
                "component_pos": 2,
                "name": "Fake ETL Test 6",
                "measurement_date": "2023-01-01T12:00:00+01:00",
                "location": "BU",
                "user_created": "hswanson",
                "version": "v0",
                "crazy_name": "yabba dabba doo",
                "crazy_array": [1,23,4,21,234,5,2,22,3,2,2,3442], 
                "another_crazy_array": [1,23,4,21,234,5,2,22,3,2,2,3442],
            }
        ],
        'table': 'test',
        'component_types': ['Fake ETROC', 'Fake LGAD', 'Fake Subassembly'],
        'module_types': ['Fake Production'],
        'description': 'A phony tests for testing the database uploads'
    })

    name: Literal['Fake ETL Test 6', 'Fake ETL Test 7', 'Fake ETL Test 8', 'Fake ETL Test 9', 'Fake ETL Test 10']
    version: Literal["v0"] = "v0"
    module: str
    component: str
    component_pos: int

    # data
    crazy_name: str
    crazy_array: list[float]
    another_crazy_array: list[float]

    def plot(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(self.crazy_array, self.another_crazy_array, label='Crazy Curve', marker='o')
        ax.set_xlabel('Counting')
        ax.set_ylabel('A random array')
        ax.set_title(f'Fake Test - crazy_name: {self.crazy_name}')
        ax.legend()
        ax.grid(True)
        return fig

    def html_display(self):
        fig = self.plot()
        return convert_fig_to_html_img(fig)
    
FakeTestModuleType = Annotated[Union[FakeTestModuleV0], Field(discriminator="version")]
