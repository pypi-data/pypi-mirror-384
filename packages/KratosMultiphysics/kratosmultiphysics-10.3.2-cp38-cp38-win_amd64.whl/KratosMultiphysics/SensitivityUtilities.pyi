import Kratos
from typing import overload

def AssignConditionDerivativesToNodes(arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.MatrixVariable, arg3: dict[int, list[int]], arg4: float, arg5: Kratos.Flags, arg6: bool) -> None:
    """AssignConditionDerivativesToNodes(arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.MatrixVariable, arg3: dict[int, list[int]], arg4: float, arg5: Kratos.Flags, arg6: bool) -> None"""
def AssignElementDerivativesToNodes(arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.MatrixVariable, arg3: dict[int, list[int]], arg4: float, arg5: Kratos.Flags, arg6: bool) -> None:
    """AssignElementDerivativesToNodes(arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.MatrixVariable, arg3: dict[int, list[int]], arg4: float, arg5: Kratos.Flags, arg6: bool) -> None"""
@overload
def GetSensitivityVariableName(variable: Kratos.BoolVariable) -> str:
    """GetSensitivityVariableName(*args, **kwargs)
    Overloaded function.

    1. GetSensitivityVariableName(variable: Kratos.BoolVariable) -> str

    2. GetSensitivityVariableName(variable: Kratos.IntegerVariable) -> str

    3. GetSensitivityVariableName(variable: Kratos.DoubleVariable) -> str

    4. GetSensitivityVariableName(variable: Kratos.Array1DVariable3) -> str

    5. GetSensitivityVariableName(variable: Kratos.Array1DVariable4) -> str

    6. GetSensitivityVariableName(variable: Kratos.Array1DVariable6) -> str

    7. GetSensitivityVariableName(variable: Kratos.Array1DVariable9) -> str

    8. GetSensitivityVariableName(variable: Kratos.VectorVariable) -> str

    9. GetSensitivityVariableName(variable: Kratos.MatrixVariable) -> str
    """
@overload
def GetSensitivityVariableName(variable: Kratos.IntegerVariable) -> str:
    """GetSensitivityVariableName(*args, **kwargs)
    Overloaded function.

    1. GetSensitivityVariableName(variable: Kratos.BoolVariable) -> str

    2. GetSensitivityVariableName(variable: Kratos.IntegerVariable) -> str

    3. GetSensitivityVariableName(variable: Kratos.DoubleVariable) -> str

    4. GetSensitivityVariableName(variable: Kratos.Array1DVariable3) -> str

    5. GetSensitivityVariableName(variable: Kratos.Array1DVariable4) -> str

    6. GetSensitivityVariableName(variable: Kratos.Array1DVariable6) -> str

    7. GetSensitivityVariableName(variable: Kratos.Array1DVariable9) -> str

    8. GetSensitivityVariableName(variable: Kratos.VectorVariable) -> str

    9. GetSensitivityVariableName(variable: Kratos.MatrixVariable) -> str
    """
@overload
def GetSensitivityVariableName(variable: Kratos.DoubleVariable) -> str:
    """GetSensitivityVariableName(*args, **kwargs)
    Overloaded function.

    1. GetSensitivityVariableName(variable: Kratos.BoolVariable) -> str

    2. GetSensitivityVariableName(variable: Kratos.IntegerVariable) -> str

    3. GetSensitivityVariableName(variable: Kratos.DoubleVariable) -> str

    4. GetSensitivityVariableName(variable: Kratos.Array1DVariable3) -> str

    5. GetSensitivityVariableName(variable: Kratos.Array1DVariable4) -> str

    6. GetSensitivityVariableName(variable: Kratos.Array1DVariable6) -> str

    7. GetSensitivityVariableName(variable: Kratos.Array1DVariable9) -> str

    8. GetSensitivityVariableName(variable: Kratos.VectorVariable) -> str

    9. GetSensitivityVariableName(variable: Kratos.MatrixVariable) -> str
    """
@overload
def GetSensitivityVariableName(variable: Kratos.Array1DVariable3) -> str:
    """GetSensitivityVariableName(*args, **kwargs)
    Overloaded function.

    1. GetSensitivityVariableName(variable: Kratos.BoolVariable) -> str

    2. GetSensitivityVariableName(variable: Kratos.IntegerVariable) -> str

    3. GetSensitivityVariableName(variable: Kratos.DoubleVariable) -> str

    4. GetSensitivityVariableName(variable: Kratos.Array1DVariable3) -> str

    5. GetSensitivityVariableName(variable: Kratos.Array1DVariable4) -> str

    6. GetSensitivityVariableName(variable: Kratos.Array1DVariable6) -> str

    7. GetSensitivityVariableName(variable: Kratos.Array1DVariable9) -> str

    8. GetSensitivityVariableName(variable: Kratos.VectorVariable) -> str

    9. GetSensitivityVariableName(variable: Kratos.MatrixVariable) -> str
    """
@overload
def GetSensitivityVariableName(variable: Kratos.Array1DVariable4) -> str:
    """GetSensitivityVariableName(*args, **kwargs)
    Overloaded function.

    1. GetSensitivityVariableName(variable: Kratos.BoolVariable) -> str

    2. GetSensitivityVariableName(variable: Kratos.IntegerVariable) -> str

    3. GetSensitivityVariableName(variable: Kratos.DoubleVariable) -> str

    4. GetSensitivityVariableName(variable: Kratos.Array1DVariable3) -> str

    5. GetSensitivityVariableName(variable: Kratos.Array1DVariable4) -> str

    6. GetSensitivityVariableName(variable: Kratos.Array1DVariable6) -> str

    7. GetSensitivityVariableName(variable: Kratos.Array1DVariable9) -> str

    8. GetSensitivityVariableName(variable: Kratos.VectorVariable) -> str

    9. GetSensitivityVariableName(variable: Kratos.MatrixVariable) -> str
    """
@overload
def GetSensitivityVariableName(variable: Kratos.Array1DVariable6) -> str:
    """GetSensitivityVariableName(*args, **kwargs)
    Overloaded function.

    1. GetSensitivityVariableName(variable: Kratos.BoolVariable) -> str

    2. GetSensitivityVariableName(variable: Kratos.IntegerVariable) -> str

    3. GetSensitivityVariableName(variable: Kratos.DoubleVariable) -> str

    4. GetSensitivityVariableName(variable: Kratos.Array1DVariable3) -> str

    5. GetSensitivityVariableName(variable: Kratos.Array1DVariable4) -> str

    6. GetSensitivityVariableName(variable: Kratos.Array1DVariable6) -> str

    7. GetSensitivityVariableName(variable: Kratos.Array1DVariable9) -> str

    8. GetSensitivityVariableName(variable: Kratos.VectorVariable) -> str

    9. GetSensitivityVariableName(variable: Kratos.MatrixVariable) -> str
    """
@overload
def GetSensitivityVariableName(variable: Kratos.Array1DVariable9) -> str:
    """GetSensitivityVariableName(*args, **kwargs)
    Overloaded function.

    1. GetSensitivityVariableName(variable: Kratos.BoolVariable) -> str

    2. GetSensitivityVariableName(variable: Kratos.IntegerVariable) -> str

    3. GetSensitivityVariableName(variable: Kratos.DoubleVariable) -> str

    4. GetSensitivityVariableName(variable: Kratos.Array1DVariable3) -> str

    5. GetSensitivityVariableName(variable: Kratos.Array1DVariable4) -> str

    6. GetSensitivityVariableName(variable: Kratos.Array1DVariable6) -> str

    7. GetSensitivityVariableName(variable: Kratos.Array1DVariable9) -> str

    8. GetSensitivityVariableName(variable: Kratos.VectorVariable) -> str

    9. GetSensitivityVariableName(variable: Kratos.MatrixVariable) -> str
    """
@overload
def GetSensitivityVariableName(variable: Kratos.VectorVariable) -> str:
    """GetSensitivityVariableName(*args, **kwargs)
    Overloaded function.

    1. GetSensitivityVariableName(variable: Kratos.BoolVariable) -> str

    2. GetSensitivityVariableName(variable: Kratos.IntegerVariable) -> str

    3. GetSensitivityVariableName(variable: Kratos.DoubleVariable) -> str

    4. GetSensitivityVariableName(variable: Kratos.Array1DVariable3) -> str

    5. GetSensitivityVariableName(variable: Kratos.Array1DVariable4) -> str

    6. GetSensitivityVariableName(variable: Kratos.Array1DVariable6) -> str

    7. GetSensitivityVariableName(variable: Kratos.Array1DVariable9) -> str

    8. GetSensitivityVariableName(variable: Kratos.VectorVariable) -> str

    9. GetSensitivityVariableName(variable: Kratos.MatrixVariable) -> str
    """
@overload
def GetSensitivityVariableName(variable: Kratos.MatrixVariable) -> str:
    """GetSensitivityVariableName(*args, **kwargs)
    Overloaded function.

    1. GetSensitivityVariableName(variable: Kratos.BoolVariable) -> str

    2. GetSensitivityVariableName(variable: Kratos.IntegerVariable) -> str

    3. GetSensitivityVariableName(variable: Kratos.DoubleVariable) -> str

    4. GetSensitivityVariableName(variable: Kratos.Array1DVariable3) -> str

    5. GetSensitivityVariableName(variable: Kratos.Array1DVariable4) -> str

    6. GetSensitivityVariableName(variable: Kratos.Array1DVariable6) -> str

    7. GetSensitivityVariableName(variable: Kratos.Array1DVariable9) -> str

    8. GetSensitivityVariableName(variable: Kratos.VectorVariable) -> str

    9. GetSensitivityVariableName(variable: Kratos.MatrixVariable) -> str
    """
