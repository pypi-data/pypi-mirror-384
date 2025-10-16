import Kratos
from typing import overload

@overload
def RandomFillConditionVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float, arg3: float) -> None:
    """RandomFillConditionVariable(*args, **kwargs)
    Overloaded function.

    1. RandomFillConditionVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float, arg3: float) -> None

    2. RandomFillConditionVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: float, arg3: float) -> None
    """
@overload
def RandomFillConditionVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: float, arg3: float) -> None:
    """RandomFillConditionVariable(*args, **kwargs)
    Overloaded function.

    1. RandomFillConditionVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float, arg3: float) -> None

    2. RandomFillConditionVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: float, arg3: float) -> None
    """
@overload
def RandomFillElementVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float, arg3: float) -> None:
    """RandomFillElementVariable(*args, **kwargs)
    Overloaded function.

    1. RandomFillElementVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float, arg3: float) -> None

    2. RandomFillElementVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: float, arg3: float) -> None
    """
@overload
def RandomFillElementVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: float, arg3: float) -> None:
    """RandomFillElementVariable(*args, **kwargs)
    Overloaded function.

    1. RandomFillElementVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float, arg3: float) -> None

    2. RandomFillElementVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: float, arg3: float) -> None
    """
@overload
def RandomFillNodalHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float, arg3: float, arg4: int) -> None:
    """RandomFillNodalHistoricalVariable(*args, **kwargs)
    Overloaded function.

    1. RandomFillNodalHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float, arg3: float, arg4: int) -> None

    2. RandomFillNodalHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: float, arg3: float, arg4: int) -> None
    """
@overload
def RandomFillNodalHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: float, arg3: float, arg4: int) -> None:
    """RandomFillNodalHistoricalVariable(*args, **kwargs)
    Overloaded function.

    1. RandomFillNodalHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float, arg3: float, arg4: int) -> None

    2. RandomFillNodalHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: float, arg3: float, arg4: int) -> None
    """
@overload
def RandomFillNodalNonHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float, arg3: float) -> None:
    """RandomFillNodalNonHistoricalVariable(*args, **kwargs)
    Overloaded function.

    1. RandomFillNodalNonHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float, arg3: float) -> None

    2. RandomFillNodalNonHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: float, arg3: float) -> None
    """
@overload
def RandomFillNodalNonHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: float, arg3: float) -> None:
    """RandomFillNodalNonHistoricalVariable(*args, **kwargs)
    Overloaded function.

    1. RandomFillNodalNonHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float, arg3: float) -> None

    2. RandomFillNodalNonHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: float, arg3: float) -> None
    """
