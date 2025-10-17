import Kratos
from typing import overload

@overload
def Distribution(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]:
    """Distribution(*args, **kwargs)
    Overloaded function.

    1. Distribution(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4e0f0>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    2. Distribution(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c47a70>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    3. Distribution(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4e9b0>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    4. Distribution(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4e330>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]
    """
@overload
def Distribution(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]:
    """Distribution(*args, **kwargs)
    Overloaded function.

    1. Distribution(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4e0f0>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    2. Distribution(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c47a70>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    3. Distribution(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4e9b0>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    4. Distribution(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4e330>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]
    """
@overload
def Distribution(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]:
    """Distribution(*args, **kwargs)
    Overloaded function.

    1. Distribution(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4e0f0>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    2. Distribution(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c47a70>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    3. Distribution(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4e9b0>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    4. Distribution(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4e330>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]
    """
@overload
def Distribution(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]:
    """Distribution(*args, **kwargs)
    Overloaded function.

    1. Distribution(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4e0f0>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    2. Distribution(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c47a70>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    3. Distribution(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4e9b0>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    4. Distribution(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4e330>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]
    """
@overload
def Max(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Max(*args, **kwargs)
    Overloaded function.

    1. Max(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4daf0>) -> tuple[float, int]

    2. Max(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4d6f0>) -> tuple[float, int]

    3. Max(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4de30>) -> tuple[float, int]

    4. Max(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4d5b0>) -> tuple[float, int]
    """
@overload
def Max(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Max(*args, **kwargs)
    Overloaded function.

    1. Max(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4daf0>) -> tuple[float, int]

    2. Max(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4d6f0>) -> tuple[float, int]

    3. Max(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4de30>) -> tuple[float, int]

    4. Max(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4d5b0>) -> tuple[float, int]
    """
@overload
def Max(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Max(*args, **kwargs)
    Overloaded function.

    1. Max(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4daf0>) -> tuple[float, int]

    2. Max(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4d6f0>) -> tuple[float, int]

    3. Max(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4de30>) -> tuple[float, int]

    4. Max(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4d5b0>) -> tuple[float, int]
    """
@overload
def Max(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Max(*args, **kwargs)
    Overloaded function.

    1. Max(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4daf0>) -> tuple[float, int]

    2. Max(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4d6f0>) -> tuple[float, int]

    3. Max(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4de30>) -> tuple[float, int]

    4. Max(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4d5b0>) -> tuple[float, int]
    """
@overload
def Mean(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Mean(*args, **kwargs)
    Overloaded function.

    1. Mean(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4f7b0>) -> float

    2. Mean(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c403b0>) -> float

    3. Mean(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4ff30>) -> float

    4. Mean(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4f5f0>) -> float
    """
@overload
def Mean(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Mean(*args, **kwargs)
    Overloaded function.

    1. Mean(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4f7b0>) -> float

    2. Mean(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c403b0>) -> float

    3. Mean(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4ff30>) -> float

    4. Mean(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4f5f0>) -> float
    """
@overload
def Mean(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Mean(*args, **kwargs)
    Overloaded function.

    1. Mean(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4f7b0>) -> float

    2. Mean(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c403b0>) -> float

    3. Mean(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4ff30>) -> float

    4. Mean(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4f5f0>) -> float
    """
@overload
def Mean(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Mean(*args, **kwargs)
    Overloaded function.

    1. Mean(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4f7b0>) -> float

    2. Mean(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c403b0>) -> float

    3. Mean(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4ff30>) -> float

    4. Mean(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d4f5f0>) -> float
    """
@overload
def Median(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Median(*args, **kwargs)
    Overloaded function.

    1. Median(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35cb4530>) -> float

    2. Median(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35cb49b0>) -> float

    3. Median(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35cb4770>) -> float

    4. Median(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35cb4a30>) -> float
    """
@overload
def Median(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Median(*args, **kwargs)
    Overloaded function.

    1. Median(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35cb4530>) -> float

    2. Median(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35cb49b0>) -> float

    3. Median(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35cb4770>) -> float

    4. Median(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35cb4a30>) -> float
    """
@overload
def Median(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Median(*args, **kwargs)
    Overloaded function.

    1. Median(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35cb4530>) -> float

    2. Median(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35cb49b0>) -> float

    3. Median(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35cb4770>) -> float

    4. Median(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35cb4a30>) -> float
    """
@overload
def Median(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Median(*args, **kwargs)
    Overloaded function.

    1. Median(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35cb4530>) -> float

    2. Median(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35cb49b0>) -> float

    3. Median(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35cb4770>) -> float

    4. Median(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35cb4a30>) -> float
    """
@overload
def Min(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Min(*args, **kwargs)
    Overloaded function.

    1. Min(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4be70>) -> tuple[float, int]

    2. Min(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4b430>) -> tuple[float, int]

    3. Min(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4b930>) -> tuple[float, int]

    4. Min(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4bdf0>) -> tuple[float, int]
    """
@overload
def Min(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Min(*args, **kwargs)
    Overloaded function.

    1. Min(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4be70>) -> tuple[float, int]

    2. Min(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4b430>) -> tuple[float, int]

    3. Min(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4b930>) -> tuple[float, int]

    4. Min(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4bdf0>) -> tuple[float, int]
    """
@overload
def Min(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Min(*args, **kwargs)
    Overloaded function.

    1. Min(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4be70>) -> tuple[float, int]

    2. Min(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4b430>) -> tuple[float, int]

    3. Min(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4b930>) -> tuple[float, int]

    4. Min(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4bdf0>) -> tuple[float, int]
    """
@overload
def Min(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Min(*args, **kwargs)
    Overloaded function.

    1. Min(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4be70>) -> tuple[float, int]

    2. Min(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4b430>) -> tuple[float, int]

    3. Min(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4b930>) -> tuple[float, int]

    4. Min(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35c4bdf0>) -> tuple[float, int]
    """
@overload
def RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """RootMeanSquare(*args, **kwargs)
    Overloaded function.

    1. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d571b0>) -> float

    2. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe364e7f70>) -> float

    3. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d571f0>) -> float

    4. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d57af0>) -> float
    """
@overload
def RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """RootMeanSquare(*args, **kwargs)
    Overloaded function.

    1. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d571b0>) -> float

    2. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe364e7f70>) -> float

    3. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d571f0>) -> float

    4. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d57af0>) -> float
    """
@overload
def RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """RootMeanSquare(*args, **kwargs)
    Overloaded function.

    1. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d571b0>) -> float

    2. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe364e7f70>) -> float

    3. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d571f0>) -> float

    4. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d57af0>) -> float
    """
@overload
def RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """RootMeanSquare(*args, **kwargs)
    Overloaded function.

    1. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d571b0>) -> float

    2. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe364e7f70>) -> float

    3. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d571f0>) -> float

    4. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d57af0>) -> float
    """
@overload
def Sum(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Sum(*args, **kwargs)
    Overloaded function.

    1. Sum(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe37d205b0>) -> float

    2. Sum(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe360ac430>) -> float

    3. Sum(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d5cdb0>) -> float

    4. Sum(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe360a28f0>) -> float
    """
@overload
def Sum(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Sum(*args, **kwargs)
    Overloaded function.

    1. Sum(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe37d205b0>) -> float

    2. Sum(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe360ac430>) -> float

    3. Sum(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d5cdb0>) -> float

    4. Sum(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe360a28f0>) -> float
    """
@overload
def Sum(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Sum(*args, **kwargs)
    Overloaded function.

    1. Sum(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe37d205b0>) -> float

    2. Sum(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe360ac430>) -> float

    3. Sum(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d5cdb0>) -> float

    4. Sum(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe360a28f0>) -> float
    """
@overload
def Sum(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Sum(*args, **kwargs)
    Overloaded function.

    1. Sum(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe37d205b0>) -> float

    2. Sum(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe360ac430>) -> float

    3. Sum(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35d5cdb0>) -> float

    4. Sum(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe360a28f0>) -> float
    """
@overload
def Variance(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float]:
    """Variance(*args, **kwargs)
    Overloaded function.

    1. Variance(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe375aa5b0>) -> tuple[float, float]

    2. Variance(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe38150d70>) -> tuple[float, float]

    3. Variance(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35dbf4b0>) -> tuple[float, float]

    4. Variance(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35dbf6b0>) -> tuple[float, float]
    """
@overload
def Variance(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float]:
    """Variance(*args, **kwargs)
    Overloaded function.

    1. Variance(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe375aa5b0>) -> tuple[float, float]

    2. Variance(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe38150d70>) -> tuple[float, float]

    3. Variance(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35dbf4b0>) -> tuple[float, float]

    4. Variance(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35dbf6b0>) -> tuple[float, float]
    """
@overload
def Variance(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float]:
    """Variance(*args, **kwargs)
    Overloaded function.

    1. Variance(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe375aa5b0>) -> tuple[float, float]

    2. Variance(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe38150d70>) -> tuple[float, float]

    3. Variance(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35dbf4b0>) -> tuple[float, float]

    4. Variance(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35dbf6b0>) -> tuple[float, float]
    """
@overload
def Variance(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float]:
    """Variance(*args, **kwargs)
    Overloaded function.

    1. Variance(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe375aa5b0>) -> tuple[float, float]

    2. Variance(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe38150d70>) -> tuple[float, float]

    3. Variance(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35dbf4b0>) -> tuple[float, float]

    4. Variance(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7efe35dbf6b0>) -> tuple[float, float]
    """
