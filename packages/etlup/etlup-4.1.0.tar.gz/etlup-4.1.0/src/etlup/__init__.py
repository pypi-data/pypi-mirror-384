# SPDX-FileCopyrightText: 2024-present Hayden Swanson <hayden_swanson22@yahoo.com>
#
# SPDX-License-Identifier: MIT
from jinja2 import Environment, PackageLoader, select_autoescape
from typing import Any, Union, Annotated
from pydantic import Field, TypeAdapter

from matplotlib import use as pltuse
pltuse("agg")

jinja_env = Environment(
    loader=PackageLoader(__name__),
    autoescape=select_autoescape()
)

##########################################################################
# Tamalero
from .tamalero.Baseline import BaselineType
from .tamalero.Noisewidth import NoisewidthType
# Sensor
from .sensor.ChargeCollection import ChargeCollectionType
from .sensor.CurrentStability import CurrentStabilityType
from .sensor.CurrentUniformity import CurrentUniformityType
from .sensor.CurrentUniformity import CurrentUniformityType
from .sensor.GainCurve import GainCurveType
from .sensor.GainLayerUniformity import GainLayerUniformityType
from .sensor.InterpadResistance import InterpadResistanceType
from .sensor.InterpadWidth import InterpadWidthType
from .sensor.MPVStability import MPVStabilityType
from .sensor.SensorIV import SensorIVType
from .sensor.TestArrayCV import TestArrayCVType
from .sensor.TestArrayIV import TestArrayIVType
from .sensor.TimeResolution import TimeResolutionType
# Module
from .module.ModuleIV import ModuleIVType
# Gantry
from .gantry.PickAndPlace import PickAndPlaceType
from .gantry.SubassemblyAlignment import SubassemblyAlignmentType
# Fake
from .fake.fake_test_component import FakeTestComponentType
from .fake.fake_test_module import FakeTestModuleType
# TestByImage
from .image_tests.ImageTest import ImageTestType
# Get all test types
_test_types = (
    ChargeCollectionType,
    CurrentStabilityType,
    CurrentUniformityType,
    GainCurveType,
    GainLayerUniformityType,
    InterpadResistanceType,
    InterpadWidthType,
    MPVStabilityType,
    SensorIVType,
    TestArrayCVType,
    TestArrayIVType,
    TimeResolutionType,
    BaselineType,
    NoisewidthType,
    ModuleIVType,
    PickAndPlaceType,
    SubassemblyAlignmentType,
    FakeTestComponentType,
    FakeTestModuleType,
    ImageTestType    
)
##########################################################################

TestType = Annotated[Union[_test_types], Field(discriminator="name")]
TestModel = TypeAdapter(TestType)
TestArrModel = TypeAdapter(list[TestType])

from .upload import Session, get_model, now_utc, localize_datetime

prod_session = Session(prod=True)
staging_session = Session(prod=False)

def _get_all_subclasses(cls):
    """Recursively get all subclasses of a class"""
    subclasses = set(cls.__subclasses__())
    for subclass in list(subclasses):
        subclasses.update(_get_all_subclasses(subclass))
    return subclasses

# Get all ConstructionBaseMixin subclasses
from .base_model import ConstructionBase
Tests = _get_all_subclasses(ConstructionBase)



