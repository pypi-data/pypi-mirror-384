import Kratos
from typing import overload

@overload
def Distribution(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]:
    """Distribution(*args, **kwargs)
    Overloaded function.

    1. Distribution(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee339ff0>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    2. Distribution(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee338330>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    3. Distribution(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee33ad30>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    4. Distribution(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee351930>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]
    """
@overload
def Distribution(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]:
    """Distribution(*args, **kwargs)
    Overloaded function.

    1. Distribution(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee339ff0>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    2. Distribution(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee338330>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    3. Distribution(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee33ad30>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    4. Distribution(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee351930>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]
    """
@overload
def Distribution(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]:
    """Distribution(*args, **kwargs)
    Overloaded function.

    1. Distribution(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee339ff0>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    2. Distribution(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee338330>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    3. Distribution(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee33ad30>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    4. Distribution(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee351930>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]
    """
@overload
def Distribution(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]:
    """Distribution(*args, **kwargs)
    Overloaded function.

    1. Distribution(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee339ff0>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    2. Distribution(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee338330>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    3. Distribution(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee33ad30>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    4. Distribution(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee351930>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]
    """
@overload
def Max(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Max(*args, **kwargs)
    Overloaded function.

    1. Max(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee3529f0>) -> tuple[float, int]

    2. Max(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee352a30>) -> tuple[float, int]

    3. Max(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee351470>) -> tuple[float, int]

    4. Max(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee352df0>) -> tuple[float, int]
    """
@overload
def Max(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Max(*args, **kwargs)
    Overloaded function.

    1. Max(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee3529f0>) -> tuple[float, int]

    2. Max(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee352a30>) -> tuple[float, int]

    3. Max(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee351470>) -> tuple[float, int]

    4. Max(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee352df0>) -> tuple[float, int]
    """
@overload
def Max(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Max(*args, **kwargs)
    Overloaded function.

    1. Max(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee3529f0>) -> tuple[float, int]

    2. Max(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee352a30>) -> tuple[float, int]

    3. Max(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee351470>) -> tuple[float, int]

    4. Max(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee352df0>) -> tuple[float, int]
    """
@overload
def Max(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Max(*args, **kwargs)
    Overloaded function.

    1. Max(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee3529f0>) -> tuple[float, int]

    2. Max(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee352a30>) -> tuple[float, int]

    3. Max(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee351470>) -> tuple[float, int]

    4. Max(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee352df0>) -> tuple[float, int]
    """
@overload
def Mean(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Mean(*args, **kwargs)
    Overloaded function.

    1. Mean(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf21db0>) -> float

    2. Mean(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf215b0>) -> float

    3. Mean(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf23f30>) -> float

    4. Mean(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf206f0>) -> float
    """
@overload
def Mean(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Mean(*args, **kwargs)
    Overloaded function.

    1. Mean(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf21db0>) -> float

    2. Mean(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf215b0>) -> float

    3. Mean(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf23f30>) -> float

    4. Mean(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf206f0>) -> float
    """
@overload
def Mean(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Mean(*args, **kwargs)
    Overloaded function.

    1. Mean(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf21db0>) -> float

    2. Mean(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf215b0>) -> float

    3. Mean(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf23f30>) -> float

    4. Mean(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf206f0>) -> float
    """
@overload
def Mean(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Mean(*args, **kwargs)
    Overloaded function.

    1. Mean(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf21db0>) -> float

    2. Mean(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf215b0>) -> float

    3. Mean(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf23f30>) -> float

    4. Mean(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf206f0>) -> float
    """
@overload
def Median(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Median(*args, **kwargs)
    Overloaded function.

    1. Median(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee353cf0>) -> float

    2. Median(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee353630>) -> float

    3. Median(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee351af0>) -> float

    4. Median(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf21030>) -> float
    """
@overload
def Median(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Median(*args, **kwargs)
    Overloaded function.

    1. Median(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee353cf0>) -> float

    2. Median(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee353630>) -> float

    3. Median(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee351af0>) -> float

    4. Median(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf21030>) -> float
    """
@overload
def Median(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Median(*args, **kwargs)
    Overloaded function.

    1. Median(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee353cf0>) -> float

    2. Median(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee353630>) -> float

    3. Median(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee351af0>) -> float

    4. Median(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf21030>) -> float
    """
@overload
def Median(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Median(*args, **kwargs)
    Overloaded function.

    1. Median(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee353cf0>) -> float

    2. Median(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee353630>) -> float

    3. Median(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee351af0>) -> float

    4. Median(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf21030>) -> float
    """
@overload
def Min(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Min(*args, **kwargs)
    Overloaded function.

    1. Min(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee350eb0>) -> tuple[float, int]

    2. Min(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee351ef0>) -> tuple[float, int]

    3. Min(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf202b0>) -> tuple[float, int]

    4. Min(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf29670>) -> tuple[float, int]
    """
@overload
def Min(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Min(*args, **kwargs)
    Overloaded function.

    1. Min(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee350eb0>) -> tuple[float, int]

    2. Min(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee351ef0>) -> tuple[float, int]

    3. Min(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf202b0>) -> tuple[float, int]

    4. Min(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf29670>) -> tuple[float, int]
    """
@overload
def Min(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Min(*args, **kwargs)
    Overloaded function.

    1. Min(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee350eb0>) -> tuple[float, int]

    2. Min(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee351ef0>) -> tuple[float, int]

    3. Min(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf202b0>) -> tuple[float, int]

    4. Min(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf29670>) -> tuple[float, int]
    """
@overload
def Min(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Min(*args, **kwargs)
    Overloaded function.

    1. Min(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee350eb0>) -> tuple[float, int]

    2. Min(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee351ef0>) -> tuple[float, int]

    3. Min(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf202b0>) -> tuple[float, int]

    4. Min(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf29670>) -> tuple[float, int]
    """
@overload
def RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """RootMeanSquare(*args, **kwargs)
    Overloaded function.

    1. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9f2dcd6f0>) -> float

    2. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf210f0>) -> float

    3. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf22f30>) -> float

    4. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf295b0>) -> float
    """
@overload
def RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """RootMeanSquare(*args, **kwargs)
    Overloaded function.

    1. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9f2dcd6f0>) -> float

    2. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf210f0>) -> float

    3. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf22f30>) -> float

    4. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf295b0>) -> float
    """
@overload
def RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """RootMeanSquare(*args, **kwargs)
    Overloaded function.

    1. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9f2dcd6f0>) -> float

    2. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf210f0>) -> float

    3. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf22f30>) -> float

    4. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf295b0>) -> float
    """
@overload
def RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """RootMeanSquare(*args, **kwargs)
    Overloaded function.

    1. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9f2dcd6f0>) -> float

    2. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf210f0>) -> float

    3. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf22f30>) -> float

    4. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf295b0>) -> float
    """
@overload
def Sum(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Sum(*args, **kwargs)
    Overloaded function.

    1. Sum(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf20430>) -> float

    2. Sum(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf20030>) -> float

    3. Sum(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf21570>) -> float

    4. Sum(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee33e3f0>) -> float
    """
@overload
def Sum(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Sum(*args, **kwargs)
    Overloaded function.

    1. Sum(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf20430>) -> float

    2. Sum(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf20030>) -> float

    3. Sum(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf21570>) -> float

    4. Sum(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee33e3f0>) -> float
    """
@overload
def Sum(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Sum(*args, **kwargs)
    Overloaded function.

    1. Sum(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf20430>) -> float

    2. Sum(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf20030>) -> float

    3. Sum(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf21570>) -> float

    4. Sum(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee33e3f0>) -> float
    """
@overload
def Sum(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Sum(*args, **kwargs)
    Overloaded function.

    1. Sum(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf20430>) -> float

    2. Sum(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf20030>) -> float

    3. Sum(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf21570>) -> float

    4. Sum(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9ee33e3f0>) -> float
    """
@overload
def Variance(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float]:
    """Variance(*args, **kwargs)
    Overloaded function.

    1. Variance(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf2b570>) -> tuple[float, float]

    2. Variance(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf20e70>) -> tuple[float, float]

    3. Variance(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf2a630>) -> tuple[float, float]

    4. Variance(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf235b0>) -> tuple[float, float]
    """
@overload
def Variance(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float]:
    """Variance(*args, **kwargs)
    Overloaded function.

    1. Variance(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf2b570>) -> tuple[float, float]

    2. Variance(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf20e70>) -> tuple[float, float]

    3. Variance(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf2a630>) -> tuple[float, float]

    4. Variance(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf235b0>) -> tuple[float, float]
    """
@overload
def Variance(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float]:
    """Variance(*args, **kwargs)
    Overloaded function.

    1. Variance(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf2b570>) -> tuple[float, float]

    2. Variance(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf20e70>) -> tuple[float, float]

    3. Variance(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf2a630>) -> tuple[float, float]

    4. Variance(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf235b0>) -> tuple[float, float]
    """
@overload
def Variance(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float]:
    """Variance(*args, **kwargs)
    Overloaded function.

    1. Variance(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf2b570>) -> tuple[float, float]

    2. Variance(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf20e70>) -> tuple[float, float]

    3. Variance(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf2a630>) -> tuple[float, float]

    4. Variance(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7ff9edf235b0>) -> tuple[float, float]
    """
