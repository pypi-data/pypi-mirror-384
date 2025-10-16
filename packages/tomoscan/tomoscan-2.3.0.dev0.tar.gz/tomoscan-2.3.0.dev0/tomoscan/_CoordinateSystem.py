from enum import Enum


class CoordinateSystem(Enum):
    """
    * ESRF coordinate system

                     Z axis
                            ^    Y axis
                            | /
          x-ray             |/
          -------->          ------> X axis

    * McStas coordinate system

                          Y axis
                            ^   X axis
                            |  /
          x-ray             | /
          -------->          ------> Z axis

    """

    McStas = "McStas"
    ESRF = "ESRF"
