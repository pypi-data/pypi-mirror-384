from pydantic import ConfigDict, Field
from typing import Literal
import matplotlib.pyplot as plt
from ..plot_utils import convert_fig_to_html_img
from .. import base_model as bm
from typing import Annotated, Union

class FakeTestComponentV0(bm.ConstructionBase):
    model_config = ConfigDict(json_schema_extra={
        'examples': [
            {
                "component": "TYL4U001",
                "name": "Fake ETL Test 1",
                "measurement_date": "2023-01-01T12:00:00+01:00",
                "location": "BU",
                "user_created": "hswanson",
                "version": "v0",
                "a_silly_integer": 420,
                "a_silly_string": "wooo", 
                "a_silly_array": [1.7981099942332435e-9, 2.1325199384136795e-9,2.3892399170222234e-9,2.6674600306364482e-9,2.9917699428949618e-9,3.3739500082674567e-9,3.8820999748168106e-9,4.47047021623348e-9,5.163700134147575e-9,5.982729867071157e-9,6.888820180961375e-9,7.861340023396224e-9,8.972140363994185e-9,9.177109738800482e-9,1.1357499829500739e-8,1.3345699656497345e-8,1.591829956737456e-8,1.9567799824926624e-8,2.4187400526898273e-8,2.9501000753384687e-8,4.2371500086346714e-8,5.5717400755384006e-6,0.000025144199753412977,0.000034218599466839805,0.000040536098822485656,0.00004414160139276646,0.000045468401367543265,0.00005196220081415959,0.00006523320189444348,0.00007574760093120858,0.00008891220204532146,0.00011379199713701382,0.00013335900439415127,0.00015114799316506833,0.0001657230022829026,0.00018318099319003522,0.00020124799630139023,0.00021330300660338253,0.00022421199537348002,0.00023484700068365782,0.00024567899527028203,0.00025691199698485434,0.0002710630069486797,0.00028676798683591187,0.0003011419903486967,0.00031354298698715866,0.0003255319898016751,0.00033718798658810556,0.00034998898627236485,0.00037184200482442975,0.0003914310073014349,0.0004061759973410517,0.00042100698919966817,0.0004358369915280491,0.0004506719997152686,0.00046582298818975687,0.0004808040102943778,0.0004961600061506033,0.0005116279935464263,0.0005280390032567084,0.000550133001524955,0.000574567005969584],
            }
        ],
        'table': 'test',
        'component_types': ['Fake ETROC', 'Fake LGAD', 'Fake Subassembly'],
        'module_types': [],
        'description': 'A phony tests for testing the database uploads'
    })

    name: Literal['Fake ETL Test 1', 'Fake ETL Test 2', 'Fake ETL Test 3', 'Fake ETL Test 4', 'Fake ETL Test 5']
    version: Literal["v0"] = "v0"

    # data
    a_silly_string: str
    a_silly_integer: int
    a_silly_array: list[float]

    #easier to probably get it in this class but cannot if we are doing cacheing buisness!
    def plot(self):
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot([i for i in range(len(self.a_silly_array))], self.a_silly_array, label='Silly Curve', marker='o')
        ax.set_xlabel('Counting')
        ax.set_ylabel('A random array')
        ax.set_title(f'Fake Test: {self.a_silly_integer} and {self.a_silly_string}')
        ax.legend()
        ax.grid(True)
        return fig

    def html_display(self):
        fig = self.plot()
        return convert_fig_to_html_img(fig)

FakeTestComponentType = Annotated[Union[FakeTestComponentV0], Field(discriminator="version")]
