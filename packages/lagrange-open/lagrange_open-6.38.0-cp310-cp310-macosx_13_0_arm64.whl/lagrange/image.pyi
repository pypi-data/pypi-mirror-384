import enum
from typing import Annotated

import numpy
from numpy.typing import NDArray


class ImagePrecision(enum.Enum):
    """Image pixel precision"""

    uint8 = 0

    int8 = 1

    uint32 = 2

    int32 = 3

    float32 = 4

    float64 = 5

    float16 = 6

    unknown = 7

class ImageChannel(enum.Enum):
    """Image channel"""

    one = 1

    three = 3

    four = 4

    unknown = 5

class ImageStorage:
    """Image storage class"""

    def __init__(self, width: int, height: int, alignment: int) -> None: ...

    @property
    def width(self) -> int:
        """Image width"""

    @property
    def height(self) -> int:
        """Image height"""

    @property
    def stride(self) -> int:
        """Image stride"""

    @property
    def data(self) -> Annotated[NDArray[numpy.uint8], dict(order='C', device='cpu')]:
        """Raw image data"""
