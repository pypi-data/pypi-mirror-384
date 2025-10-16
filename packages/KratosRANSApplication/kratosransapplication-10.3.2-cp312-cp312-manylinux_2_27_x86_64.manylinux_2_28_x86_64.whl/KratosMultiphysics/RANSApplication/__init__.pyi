import Kratos
from . import RansCalculationUtilities as RansCalculationUtilities, RansTestUtilities as RansTestUtilities, RansVariableUtilities as RansVariableUtilities
from typing import overload

class AlgebraicFluxCorrectedSteadyScalarScheme(Kratos.Scheme):
    @overload
    def __init__(self, arg0: float, arg1: Kratos.Flags) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosRANSApplication.AlgebraicFluxCorrectedSteadyScalarScheme, arg0: float, arg1: Kratos.Flags) -> None

        2. __init__(self: KratosRANSApplication.AlgebraicFluxCorrectedSteadyScalarScheme, arg0: float, arg1: Kratos.Flags, arg2: Kratos.IntegerVariable) -> None
        """
    @overload
    def __init__(self, arg0: float, arg1: Kratos.Flags, arg2: Kratos.IntegerVariable) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosRANSApplication.AlgebraicFluxCorrectedSteadyScalarScheme, arg0: float, arg1: Kratos.Flags) -> None

        2. __init__(self: KratosRANSApplication.AlgebraicFluxCorrectedSteadyScalarScheme, arg0: float, arg1: Kratos.Flags, arg2: Kratos.IntegerVariable) -> None
        """

class BossakRelaxationScalarScheme(Kratos.Scheme):
    def __init__(self, arg0: float, arg1: float, arg2: Kratos.DoubleVariable) -> None:
        """__init__(self: KratosRANSApplication.BossakRelaxationScalarScheme, arg0: float, arg1: float, arg2: Kratos.DoubleVariable) -> None"""

class KratosRANSApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosRANSApplication.KratosRANSApplication) -> None"""

class RansApplyExactNodalPeriodicConditionProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosRANSApplication.RansApplyExactNodalPeriodicConditionProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class RansApplyFlagToSkinProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosRANSApplication.RansApplyFlagToSkinProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class RansClipScalarVariableProcess(RansFormulationProcess):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosRANSApplication.RansClipScalarVariableProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class RansComputeReactionsProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosRANSApplication.RansComputeReactionsProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class RansEpsilonTurbulentMixingLengthInletProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosRANSApplication.RansEpsilonTurbulentMixingLengthInletProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class RansFormulationProcess(Kratos.Process):
    def __init__(self) -> None:
        """__init__(self: KratosRANSApplication.RansFormulationProcess) -> None"""
    def ExecuteAfterCouplingSolveStep(self) -> None:
        """ExecuteAfterCouplingSolveStep(self: KratosRANSApplication.RansFormulationProcess) -> None"""
    def ExecuteBeforeCouplingSolveStep(self) -> None:
        """ExecuteBeforeCouplingSolveStep(self: KratosRANSApplication.RansFormulationProcess) -> None"""

class RansKTurbulentIntensityInletProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosRANSApplication.RansKTurbulentIntensityInletProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class RansLineOutputProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosRANSApplication.RansLineOutputProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class RansNutKEpsilonUpdateProcess(RansFormulationProcess):
    @overload
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosRANSApplication.RansNutKEpsilonUpdateProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosRANSApplication.RansNutKEpsilonUpdateProcess, arg0: Kratos.Model, arg1: str, arg2: float, arg3: int) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Model, arg1: str, arg2: float, arg3: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosRANSApplication.RansNutKEpsilonUpdateProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosRANSApplication.RansNutKEpsilonUpdateProcess, arg0: Kratos.Model, arg1: str, arg2: float, arg3: int) -> None
        """

class RansNutKOmegaSSTUpdateProcess(RansFormulationProcess):
    @overload
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosRANSApplication.RansNutKOmegaSSTUpdateProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosRANSApplication.RansNutKOmegaSSTUpdateProcess, arg0: Kratos.Model, arg1: str, arg2: float, arg3: int) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Model, arg1: str, arg2: float, arg3: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosRANSApplication.RansNutKOmegaSSTUpdateProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosRANSApplication.RansNutKOmegaSSTUpdateProcess, arg0: Kratos.Model, arg1: str, arg2: float, arg3: int) -> None
        """

class RansNutKOmegaUpdateProcess(RansFormulationProcess):
    @overload
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosRANSApplication.RansNutKOmegaUpdateProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosRANSApplication.RansNutKOmegaUpdateProcess, arg0: Kratos.Model, arg1: str, arg2: float, arg3: int) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Model, arg1: str, arg2: float, arg3: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosRANSApplication.RansNutKOmegaUpdateProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosRANSApplication.RansNutKOmegaUpdateProcess, arg0: Kratos.Model, arg1: str, arg2: float, arg3: int) -> None
        """

class RansNutNodalUpdateProcess(RansFormulationProcess):
    @overload
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosRANSApplication.RansNutNodalUpdateProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosRANSApplication.RansNutNodalUpdateProcess, arg0: Kratos.Model, arg1: str, arg2: int) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Model, arg1: str, arg2: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosRANSApplication.RansNutNodalUpdateProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosRANSApplication.RansNutNodalUpdateProcess, arg0: Kratos.Model, arg1: str, arg2: int) -> None
        """

class RansNutYPlusWallFunctionUpdateProcess(RansFormulationProcess):
    @overload
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosRANSApplication.RansNutYPlusWallFunctionUpdateProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosRANSApplication.RansNutYPlusWallFunctionUpdateProcess, arg0: Kratos.Model, arg1: str, arg2: float, arg3: int) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Model, arg1: str, arg2: float, arg3: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosRANSApplication.RansNutYPlusWallFunctionUpdateProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosRANSApplication.RansNutYPlusWallFunctionUpdateProcess, arg0: Kratos.Model, arg1: str, arg2: float, arg3: int) -> None
        """

class RansOmegaTurbulentMixingLengthInletProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosRANSApplication.RansOmegaTurbulentMixingLengthInletProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class RansWallDistanceCalculationProcess(RansFormulationProcess):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosRANSApplication.RansWallDistanceCalculationProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class RansWallFunctionUpdateProcess(RansFormulationProcess):
    @overload
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosRANSApplication.RansWallFunctionUpdateProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosRANSApplication.RansWallFunctionUpdateProcess, arg0: Kratos.Model, arg1: str, arg2: int) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Model, arg1: str, arg2: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosRANSApplication.RansWallFunctionUpdateProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosRANSApplication.RansWallFunctionUpdateProcess, arg0: Kratos.Model, arg1: str, arg2: int) -> None
        """

class ScalarVariableDifferenceNormCalculationUtility:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None:
        """__init__(self: KratosRANSApplication.ScalarVariableDifferenceNormCalculationUtility, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None"""
    def CalculateDifferenceNorm(self) -> tuple[float, float]:
        """CalculateDifferenceNorm(self: KratosRANSApplication.ScalarVariableDifferenceNormCalculationUtility) -> tuple[float, float]"""
    def InitializeCalculation(self) -> None:
        """InitializeCalculation(self: KratosRANSApplication.ScalarVariableDifferenceNormCalculationUtility) -> None"""

class SteadyScalarScheme(Kratos.Scheme):
    def __init__(self, arg0: float) -> None:
        """__init__(self: KratosRANSApplication.SteadyScalarScheme, arg0: float) -> None"""
