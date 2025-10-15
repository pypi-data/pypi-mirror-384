import Kratos
from typing import overload

@overload
def CalculateArea(arg0: Kratos.ElementsArray) -> float:
    """CalculateArea(*args, **kwargs)
    Overloaded function.

    1. CalculateArea(arg0: Kratos.ElementsArray) -> float

    2. CalculateArea(arg0: Kratos.ConditionsArray) -> float
    """
@overload
def CalculateArea(arg0: Kratos.ConditionsArray) -> float:
    """CalculateArea(*args, **kwargs)
    Overloaded function.

    1. CalculateArea(arg0: Kratos.ElementsArray) -> float

    2. CalculateArea(arg0: Kratos.ConditionsArray) -> float
    """
def CheckIfWakeConditionsAreFulfilled2D(arg0: Kratos.ModelPart, arg1: float, arg2: int) -> None:
    """CheckIfWakeConditionsAreFulfilled2D(arg0: Kratos.ModelPart, arg1: float, arg2: int) -> None"""
def CheckIfWakeConditionsAreFulfilled3D(arg0: Kratos.ModelPart, arg1: float, arg2: int) -> None:
    """CheckIfWakeConditionsAreFulfilled3D(arg0: Kratos.ModelPart, arg1: float, arg2: int) -> None"""
def ComputePotentialJump2D(arg0: Kratos.ModelPart) -> None:
    """ComputePotentialJump2D(arg0: Kratos.ModelPart) -> None"""
def ComputePotentialJump3D(arg0: Kratos.ModelPart) -> None:
    """ComputePotentialJump3D(arg0: Kratos.ModelPart) -> None"""
