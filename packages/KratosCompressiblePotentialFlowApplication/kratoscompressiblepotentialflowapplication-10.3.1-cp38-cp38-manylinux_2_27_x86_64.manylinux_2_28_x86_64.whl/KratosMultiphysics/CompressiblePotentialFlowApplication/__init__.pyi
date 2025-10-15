import Kratos
from . import PotentialFlowUtilities as PotentialFlowUtilities
from typing import overload

class AdjointLiftFarFieldResponseFunction(Kratos.AdjointResponseFunction):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosCompressiblePotentialFlowApplication.AdjointLiftFarFieldResponseFunction, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class AdjointLiftJumpCoordinatesResponseFunction(Kratos.AdjointResponseFunction):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosCompressiblePotentialFlowApplication.AdjointLiftJumpCoordinatesResponseFunction, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class ApplyFarFieldProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: float, arg2: bool, arg3: bool) -> None:
        """__init__(self: KratosCompressiblePotentialFlowApplication.ApplyFarFieldProcess, arg0: Kratos.ModelPart, arg1: float, arg2: bool, arg3: bool) -> None"""

class ComputeEmbeddedLiftProcess2D(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Vector) -> None:
        """__init__(self: KratosCompressiblePotentialFlowApplication.ComputeEmbeddedLiftProcess2D, arg0: Kratos.ModelPart, arg1: Kratos.Vector) -> None"""

class ComputeEmbeddedLiftProcess3D(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Vector) -> None:
        """__init__(self: KratosCompressiblePotentialFlowApplication.ComputeEmbeddedLiftProcess3D, arg0: Kratos.ModelPart, arg1: Kratos.Vector) -> None"""

class ComputeEmbeddedWingSectionVariableProcess(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array3, arg3: Kratos.Array3) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosCompressiblePotentialFlowApplication.ComputeEmbeddedWingSectionVariableProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array3, arg3: Kratos.Array3) -> None

        2. __init__(self: KratosCompressiblePotentialFlowApplication.ComputeEmbeddedWingSectionVariableProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array3, arg3: Kratos.Array3, arg4: list[str]) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array3, arg3: Kratos.Array3, arg4: list[str]) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosCompressiblePotentialFlowApplication.ComputeEmbeddedWingSectionVariableProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array3, arg3: Kratos.Array3) -> None

        2. __init__(self: KratosCompressiblePotentialFlowApplication.ComputeEmbeddedWingSectionVariableProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array3, arg3: Kratos.Array3, arg4: list[str]) -> None
        """

class ComputeNodalValueProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: list[str]) -> None:
        """__init__(self: KratosCompressiblePotentialFlowApplication.ComputeNodalValueProcess, arg0: Kratos.ModelPart, arg1: list[str]) -> None"""

class ComputeWingSectionVariableProcess(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array3, arg3: Kratos.Array3) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosCompressiblePotentialFlowApplication.ComputeWingSectionVariableProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array3, arg3: Kratos.Array3) -> None

        2. __init__(self: KratosCompressiblePotentialFlowApplication.ComputeWingSectionVariableProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array3, arg3: Kratos.Array3, arg4: list[str]) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array3, arg3: Kratos.Array3, arg4: list[str]) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosCompressiblePotentialFlowApplication.ComputeWingSectionVariableProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array3, arg3: Kratos.Array3) -> None

        2. __init__(self: KratosCompressiblePotentialFlowApplication.ComputeWingSectionVariableProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array3, arg3: Kratos.Array3, arg4: list[str]) -> None
        """

class Define2DWakeOperation(Kratos.Operation):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosCompressiblePotentialFlowApplication.Define2DWakeOperation, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class Define3DWakeOperation(Kratos.Operation):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosCompressiblePotentialFlowApplication.Define3DWakeOperation, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class DefineEmbeddedWakeProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """__init__(self: KratosCompressiblePotentialFlowApplication.DefineEmbeddedWakeProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""

class KratosCompressiblePotentialFlowApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosCompressiblePotentialFlowApplication.KratosCompressiblePotentialFlowApplication) -> None"""

class MoveModelPartProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosCompressiblePotentialFlowApplication.MoveModelPartProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class PotentialFlowResidualBasedIncrementalUpdateStaticScheme(Kratos.ResidualBasedIncrementalUpdateStaticScheme):
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosCompressiblePotentialFlowApplication.PotentialFlowResidualBasedIncrementalUpdateStaticScheme, arg0: Kratos.Parameters) -> None

        2. __init__(self: KratosCompressiblePotentialFlowApplication.PotentialFlowResidualBasedIncrementalUpdateStaticScheme) -> None
        """
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosCompressiblePotentialFlowApplication.PotentialFlowResidualBasedIncrementalUpdateStaticScheme, arg0: Kratos.Parameters) -> None

        2. __init__(self: KratosCompressiblePotentialFlowApplication.PotentialFlowResidualBasedIncrementalUpdateStaticScheme) -> None
        """

class PotentialToCompressibleNavierStokesOperation(Kratos.Operation):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosCompressiblePotentialFlowApplication.PotentialToCompressibleNavierStokesOperation, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""
