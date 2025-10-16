
from pydantic import AfterValidator
from typing import List, Annotated
import numpy as np

def _pix_arr_shape(value: List[List[int]]) -> List[List[int]]:
    v_arr = np.array(value)
    if v_arr.shape != (16,16):
        raise ValueError(f"Your array is not the correct shape, it should be 16x16, you gave: {v_arr.shape}")
    return value

PixArr = Annotated[
    List[List[int]],
    AfterValidator(_pix_arr_shape),
]