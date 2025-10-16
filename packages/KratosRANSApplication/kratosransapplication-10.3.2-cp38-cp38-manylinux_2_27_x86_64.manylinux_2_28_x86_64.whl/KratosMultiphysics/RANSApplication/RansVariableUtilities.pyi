import Kratos
from typing import overload

def AddAnalysisStep(arg0: Kratos.ModelPart, arg1: str) -> None:
    """AddAnalysisStep(arg0: Kratos.ModelPart, arg1: str) -> None"""
def AssignBoundaryFlagsToGeometries(arg0: Kratos.ModelPart) -> None:
    """AssignBoundaryFlagsToGeometries(arg0: Kratos.ModelPart) -> None"""
@overload
def AssignConditionVariableValuesToNodes(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, flag: Kratos.Flags, flag_value: bool = ...) -> None:
    """AssignConditionVariableValuesToNodes(*args, **kwargs)
    Overloaded function.

    1. AssignConditionVariableValuesToNodes(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, flag: Kratos.Flags, flag_value: bool = True) -> None

    2. AssignConditionVariableValuesToNodes(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, flag: Kratos.Flags, flag_value: bool = True) -> None
    """
@overload
def AssignConditionVariableValuesToNodes(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, flag: Kratos.Flags, flag_value: bool = ...) -> None:
    """AssignConditionVariableValuesToNodes(*args, **kwargs)
    Overloaded function.

    1. AssignConditionVariableValuesToNodes(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, flag: Kratos.Flags, flag_value: bool = True) -> None

    2. AssignConditionVariableValuesToNodes(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, flag: Kratos.Flags, flag_value: bool = True) -> None
    """
@overload
def CalculateTransientVariableConvergence(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> tuple[float, float]:
    """CalculateTransientVariableConvergence(*args, **kwargs)
    Overloaded function.

    1. CalculateTransientVariableConvergence(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> tuple[float, float]

    2. CalculateTransientVariableConvergence(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> tuple[float, float]
    """
@overload
def CalculateTransientVariableConvergence(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> tuple[float, float]:
    """CalculateTransientVariableConvergence(*args, **kwargs)
    Overloaded function.

    1. CalculateTransientVariableConvergence(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> tuple[float, float]

    2. CalculateTransientVariableConvergence(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> tuple[float, float]
    """
def ClipScalarVariable(arg0: float, arg1: float, arg2: Kratos.DoubleVariable, arg3: Kratos.ModelPart) -> tuple[int, int]:
    """ClipScalarVariable(arg0: float, arg1: float, arg2: Kratos.DoubleVariable, arg3: Kratos.ModelPart) -> tuple[int, int]"""
def CopyNodalSolutionStepVariablesList(arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
    """CopyNodalSolutionStepVariablesList(arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
def GetMaximumScalarValue(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float:
    """GetMaximumScalarValue(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float"""
def GetMinimumScalarValue(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float:
    """GetMinimumScalarValue(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float"""
def IsAnalysisStepCompleted(arg0: Kratos.ModelPart, arg1: str) -> bool:
    """IsAnalysisStepCompleted(arg0: Kratos.ModelPart, arg1: str) -> bool"""
def SetElementConstitutiveLaws(arg0: Kratos.ElementsArray) -> None:
    """SetElementConstitutiveLaws(arg0: Kratos.ElementsArray) -> None"""
