from pydantic import ConfigDict, field_validator, Field
from typing import Literal, Optional
from typing import Literal, Optional, Annotated, Union
from .. import jinja_env
from pathlib import Path
from io import BytesIO
import base64
from .. import base_model as bm
try:
    from webdav3.client import Client #for cloud talking webdav is old but it works for CERNbox
except ModuleNotFoundError as e:
    ...

def get_client_details():
    try:
        from application import the_config
        return {
            'webdav_hostname': the_config.WEBDAV_HOSTNAME,
            'webdav_login': the_config.WEBDAV_LOGIN,
            'webdav_password': the_config.WEBDAV_PASSWORD
        }
    except ModuleNotFoundError:
        return

class ImageTestV0(bm.ConstructionBase):
    model_config = ConfigDict(json_schema_extra={
        'examples': [
            {
                "component": "ET2.01-PT-NH21",
                "name": "IV Scan Image",
                "measurement_date": "2023-01-01T12:00:00+01:00",
                "location": "FL",
                "user_created": "hswanson",
                "version": "v0",
                "cernbox_img_path": "/eos/project/e/etl-construction-app-storage/TedTestResults/IV_Curve/IV_second_PT_NH_19_20_21_22.png",
                "comment": "this result was goods",
                "bias": 123
            }
        ],
        'table': 'test',
        'component_types': ['Prototype Hybrid'],
        'module_types': [],
        'description': 'IV curves from teds presentation: https://indico.cern.ch/event/1566730/contributions/6599657/attachments/3099619/5491873/Summary-of-bump-bonding-study-July2025.pdf'
    })
    name: Literal['IV Scan Image', "Baseline and Noisewidth Histogram Image", "Baseline and Noisewidth Image", "Time Resolution - Bias Voltage Scan Image"]
    version: Literal["v0"] = "v0"
    component: str

    cernbox_img_path: str
    comment: str
    bias: Optional[int] = None

    @field_validator("cernbox_img_path")
    @classmethod
    def check_img_exists(cls, v):
        client_details = get_client_details()
        if client_details is None:
            return v
        v_path = Path(v)
        cernbox_relative_path = v_path.relative_to("/eos/project/e/etl-construction-app-storage/")
        client = Client(client_details)
        if not client.check(str(cernbox_relative_path)):
            raise ValueError(f"This file ({cernbox_relative_path}) does not exist in the cernbox. The cernbox is the one for the web app, contact an admin to upload.")
        return v
    
    def plot(self):
        return None

    def html_display(self) -> str:
        client_details = get_client_details()
        if client_details is None:
            print("This feature only works on the web application, returning nothing.")
            return None
        
        if self.cernbox_img_path is not None:
            # the path should be obtained by copying the "fuse path" on cernbox
            eos_fuse_path = Path(self.cernbox_img_path)
            cernbox_relative_path = str(
                eos_fuse_path.relative_to("/eos/project/e/etl-construction-app-storage/"))
            
            client = Client(client_details)
            buff = BytesIO()
            client.download_from(
                remote_path = cernbox_relative_path, 
                buff = buff)
            buff.seek(0)
            encoded_img = base64.b64encode(buff.getvalue()).decode('utf-8')
            img_html = f'<img src="data:image/png;base64,{encoded_img}" alt="IV Scan Image">'
        else:
            img_html = "Resource image path not provided in test data"

        template = jinja_env.get_template('test_by_image.html')
        display_data = {
            "cernbox_img_path": self.cernbox_img_path,
            "comment": self.comment,
            "bias": self.bias
        }
        return template.render(
            display_data = display_data,
            img_html = img_html
        )
    
ImageTestType = Annotated[Union[ImageTestV0], Field(discriminator="version")]