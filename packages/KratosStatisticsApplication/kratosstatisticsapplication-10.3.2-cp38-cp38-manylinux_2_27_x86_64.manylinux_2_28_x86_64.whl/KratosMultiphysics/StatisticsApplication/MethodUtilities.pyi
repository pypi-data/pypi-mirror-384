import Kratos
from typing import Callable, overload

@overload
def GetNormMethod(arg0: Kratos.IntegerVariable, arg1: str) -> Callable[[int], float]:
    """GetNormMethod(*args, **kwargs)
    Overloaded function.

    1. GetNormMethod(arg0: Kratos.IntegerVariable, arg1: str) -> Callable[[int], float]

    2. GetNormMethod(arg0: Kratos.DoubleVariable, arg1: str) -> Callable[[float], float]

    3. GetNormMethod(arg0: Kratos.Array1DVariable3, arg1: str) -> Callable[[Kratos.Array3], float]

    4. GetNormMethod(arg0: Kratos.VectorVariable, arg1: str) -> Callable[[Kratos.Vector], float]

    5. GetNormMethod(arg0: Kratos.MatrixVariable, arg1: str) -> Callable[[Kratos.Matrix], float]
    """
@overload
def GetNormMethod(arg0: Kratos.DoubleVariable, arg1: str) -> Callable[[float], float]:
    """GetNormMethod(*args, **kwargs)
    Overloaded function.

    1. GetNormMethod(arg0: Kratos.IntegerVariable, arg1: str) -> Callable[[int], float]

    2. GetNormMethod(arg0: Kratos.DoubleVariable, arg1: str) -> Callable[[float], float]

    3. GetNormMethod(arg0: Kratos.Array1DVariable3, arg1: str) -> Callable[[Kratos.Array3], float]

    4. GetNormMethod(arg0: Kratos.VectorVariable, arg1: str) -> Callable[[Kratos.Vector], float]

    5. GetNormMethod(arg0: Kratos.MatrixVariable, arg1: str) -> Callable[[Kratos.Matrix], float]
    """
@overload
def GetNormMethod(arg0: Kratos.Array1DVariable3, arg1: str) -> Callable[[Kratos.Array3], float]:
    """GetNormMethod(*args, **kwargs)
    Overloaded function.

    1. GetNormMethod(arg0: Kratos.IntegerVariable, arg1: str) -> Callable[[int], float]

    2. GetNormMethod(arg0: Kratos.DoubleVariable, arg1: str) -> Callable[[float], float]

    3. GetNormMethod(arg0: Kratos.Array1DVariable3, arg1: str) -> Callable[[Kratos.Array3], float]

    4. GetNormMethod(arg0: Kratos.VectorVariable, arg1: str) -> Callable[[Kratos.Vector], float]

    5. GetNormMethod(arg0: Kratos.MatrixVariable, arg1: str) -> Callable[[Kratos.Matrix], float]
    """
@overload
def GetNormMethod(arg0: Kratos.VectorVariable, arg1: str) -> Callable[[Kratos.Vector], float]:
    """GetNormMethod(*args, **kwargs)
    Overloaded function.

    1. GetNormMethod(arg0: Kratos.IntegerVariable, arg1: str) -> Callable[[int], float]

    2. GetNormMethod(arg0: Kratos.DoubleVariable, arg1: str) -> Callable[[float], float]

    3. GetNormMethod(arg0: Kratos.Array1DVariable3, arg1: str) -> Callable[[Kratos.Array3], float]

    4. GetNormMethod(arg0: Kratos.VectorVariable, arg1: str) -> Callable[[Kratos.Vector], float]

    5. GetNormMethod(arg0: Kratos.MatrixVariable, arg1: str) -> Callable[[Kratos.Matrix], float]
    """
@overload
def GetNormMethod(arg0: Kratos.MatrixVariable, arg1: str) -> Callable[[Kratos.Matrix], float]:
    """GetNormMethod(*args, **kwargs)
    Overloaded function.

    1. GetNormMethod(arg0: Kratos.IntegerVariable, arg1: str) -> Callable[[int], float]

    2. GetNormMethod(arg0: Kratos.DoubleVariable, arg1: str) -> Callable[[float], float]

    3. GetNormMethod(arg0: Kratos.Array1DVariable3, arg1: str) -> Callable[[Kratos.Array3], float]

    4. GetNormMethod(arg0: Kratos.VectorVariable, arg1: str) -> Callable[[Kratos.Vector], float]

    5. GetNormMethod(arg0: Kratos.MatrixVariable, arg1: str) -> Callable[[Kratos.Matrix], float]
    """
@overload
def RaiseToPower(arg0: int, arg1: float) -> int:
    """RaiseToPower(*args, **kwargs)
    Overloaded function.

    1. RaiseToPower(arg0: int, arg1: float) -> int

    2. RaiseToPower(arg0: float, arg1: float) -> float

    3. RaiseToPower(arg0: Kratos.Array3, arg1: float) -> Kratos.Array3

    4. RaiseToPower(arg0: Kratos.Vector, arg1: float) -> Kratos.Vector

    5. RaiseToPower(arg0: Kratos.Matrix, arg1: float) -> Kratos.Matrix
    """
@overload
def RaiseToPower(arg0: float, arg1: float) -> float:
    """RaiseToPower(*args, **kwargs)
    Overloaded function.

    1. RaiseToPower(arg0: int, arg1: float) -> int

    2. RaiseToPower(arg0: float, arg1: float) -> float

    3. RaiseToPower(arg0: Kratos.Array3, arg1: float) -> Kratos.Array3

    4. RaiseToPower(arg0: Kratos.Vector, arg1: float) -> Kratos.Vector

    5. RaiseToPower(arg0: Kratos.Matrix, arg1: float) -> Kratos.Matrix
    """
@overload
def RaiseToPower(arg0: Kratos.Array3, arg1: float) -> Kratos.Array3:
    """RaiseToPower(*args, **kwargs)
    Overloaded function.

    1. RaiseToPower(arg0: int, arg1: float) -> int

    2. RaiseToPower(arg0: float, arg1: float) -> float

    3. RaiseToPower(arg0: Kratos.Array3, arg1: float) -> Kratos.Array3

    4. RaiseToPower(arg0: Kratos.Vector, arg1: float) -> Kratos.Vector

    5. RaiseToPower(arg0: Kratos.Matrix, arg1: float) -> Kratos.Matrix
    """
@overload
def RaiseToPower(arg0: Kratos.Vector, arg1: float) -> Kratos.Vector:
    """RaiseToPower(*args, **kwargs)
    Overloaded function.

    1. RaiseToPower(arg0: int, arg1: float) -> int

    2. RaiseToPower(arg0: float, arg1: float) -> float

    3. RaiseToPower(arg0: Kratos.Array3, arg1: float) -> Kratos.Array3

    4. RaiseToPower(arg0: Kratos.Vector, arg1: float) -> Kratos.Vector

    5. RaiseToPower(arg0: Kratos.Matrix, arg1: float) -> Kratos.Matrix
    """
@overload
def RaiseToPower(arg0: Kratos.Matrix, arg1: float) -> Kratos.Matrix:
    """RaiseToPower(*args, **kwargs)
    Overloaded function.

    1. RaiseToPower(arg0: int, arg1: float) -> int

    2. RaiseToPower(arg0: float, arg1: float) -> float

    3. RaiseToPower(arg0: Kratos.Array3, arg1: float) -> Kratos.Array3

    4. RaiseToPower(arg0: Kratos.Vector, arg1: float) -> Kratos.Vector

    5. RaiseToPower(arg0: Kratos.Matrix, arg1: float) -> Kratos.Matrix
    """
