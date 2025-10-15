import Kratos
from typing import overload

@overload
def Mean(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float:
    """Mean(*args, **kwargs)
    Overloaded function.

    1. Mean(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float

    2. Mean(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> Kratos.Array3
    """
@overload
def Mean(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> Kratos.Array3:
    """Mean(*args, **kwargs)
    Overloaded function.

    1. Mean(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float

    2. Mean(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> Kratos.Array3
    """
@overload
def RootMeanSquare(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float:
    """RootMeanSquare(*args, **kwargs)
    Overloaded function.

    1. RootMeanSquare(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float

    2. RootMeanSquare(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> Kratos.Array3
    """
@overload
def RootMeanSquare(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> Kratos.Array3:
    """RootMeanSquare(*args, **kwargs)
    Overloaded function.

    1. RootMeanSquare(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float

    2. RootMeanSquare(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> Kratos.Array3
    """
@overload
def Sum(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float:
    """Sum(*args, **kwargs)
    Overloaded function.

    1. Sum(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float

    2. Sum(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> Kratos.Array3
    """
@overload
def Sum(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> Kratos.Array3:
    """Sum(*args, **kwargs)
    Overloaded function.

    1. Sum(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float

    2. Sum(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> Kratos.Array3
    """
@overload
def Variance(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> tuple[float, float]:
    """Variance(*args, **kwargs)
    Overloaded function.

    1. Variance(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> tuple[float, float]

    2. Variance(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> tuple[Kratos.Array3, Kratos.Array3]
    """
@overload
def Variance(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> tuple[Kratos.Array3, Kratos.Array3]:
    """Variance(*args, **kwargs)
    Overloaded function.

    1. Variance(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> tuple[float, float]

    2. Variance(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> tuple[Kratos.Array3, Kratos.Array3]
    """
