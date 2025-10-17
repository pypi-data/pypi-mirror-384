import Kratos
from typing import overload

@overload
def Distribution(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]:
    """Distribution(*args, **kwargs)
    Overloaded function.

    1. Distribution(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba3f30>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    2. Distribution(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba3fb0>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    3. Distribution(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bd5e70>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    4. Distribution(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba10b0>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]
    """
@overload
def Distribution(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]:
    """Distribution(*args, **kwargs)
    Overloaded function.

    1. Distribution(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba3f30>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    2. Distribution(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba3fb0>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    3. Distribution(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bd5e70>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    4. Distribution(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba10b0>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]
    """
@overload
def Distribution(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]:
    """Distribution(*args, **kwargs)
    Overloaded function.

    1. Distribution(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba3f30>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    2. Distribution(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba3fb0>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    3. Distribution(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bd5e70>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    4. Distribution(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba10b0>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]
    """
@overload
def Distribution(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]:
    """Distribution(*args, **kwargs)
    Overloaded function.

    1. Distribution(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba3f30>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    2. Distribution(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba3fb0>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    3. Distribution(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bd5e70>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]

    4. Distribution(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba10b0>) -> tuple[float, float, list[float], list[int], list[float], list[float], list[float]]
    """
@overload
def Max(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Max(*args, **kwargs)
    Overloaded function.

    1. Max(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227d0cf0>) -> tuple[float, int]

    2. Max(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba31f0>) -> tuple[float, int]

    3. Max(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe822bd7eb0>) -> tuple[float, int]

    4. Max(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227aa530>) -> tuple[float, int]
    """
@overload
def Max(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Max(*args, **kwargs)
    Overloaded function.

    1. Max(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227d0cf0>) -> tuple[float, int]

    2. Max(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba31f0>) -> tuple[float, int]

    3. Max(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe822bd7eb0>) -> tuple[float, int]

    4. Max(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227aa530>) -> tuple[float, int]
    """
@overload
def Max(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Max(*args, **kwargs)
    Overloaded function.

    1. Max(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227d0cf0>) -> tuple[float, int]

    2. Max(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba31f0>) -> tuple[float, int]

    3. Max(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe822bd7eb0>) -> tuple[float, int]

    4. Max(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227aa530>) -> tuple[float, int]
    """
@overload
def Max(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Max(*args, **kwargs)
    Overloaded function.

    1. Max(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227d0cf0>) -> tuple[float, int]

    2. Max(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba31f0>) -> tuple[float, int]

    3. Max(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe822bd7eb0>) -> tuple[float, int]

    4. Max(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227aa530>) -> tuple[float, int]
    """
@overload
def Mean(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Mean(*args, **kwargs)
    Overloaded function.

    1. Mean(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe822787070>) -> float

    2. Mean(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bcc9f0>) -> float

    3. Mean(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227d1e30>) -> float

    4. Mean(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227dcff0>) -> float
    """
@overload
def Mean(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Mean(*args, **kwargs)
    Overloaded function.

    1. Mean(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe822787070>) -> float

    2. Mean(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bcc9f0>) -> float

    3. Mean(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227d1e30>) -> float

    4. Mean(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227dcff0>) -> float
    """
@overload
def Mean(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Mean(*args, **kwargs)
    Overloaded function.

    1. Mean(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe822787070>) -> float

    2. Mean(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bcc9f0>) -> float

    3. Mean(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227d1e30>) -> float

    4. Mean(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227dcff0>) -> float
    """
@overload
def Mean(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Mean(*args, **kwargs)
    Overloaded function.

    1. Mean(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe822787070>) -> float

    2. Mean(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bcc9f0>) -> float

    3. Mean(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227d1e30>) -> float

    4. Mean(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227dcff0>) -> float
    """
@overload
def Median(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Median(*args, **kwargs)
    Overloaded function.

    1. Median(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba2e30>) -> float

    2. Median(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba38f0>) -> float

    3. Median(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8237d48b0>) -> float

    4. Median(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227001f0>) -> float
    """
@overload
def Median(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Median(*args, **kwargs)
    Overloaded function.

    1. Median(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba2e30>) -> float

    2. Median(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba38f0>) -> float

    3. Median(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8237d48b0>) -> float

    4. Median(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227001f0>) -> float
    """
@overload
def Median(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Median(*args, **kwargs)
    Overloaded function.

    1. Median(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba2e30>) -> float

    2. Median(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba38f0>) -> float

    3. Median(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8237d48b0>) -> float

    4. Median(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227001f0>) -> float
    """
@overload
def Median(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Median(*args, **kwargs)
    Overloaded function.

    1. Median(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba2e30>) -> float

    2. Median(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba38f0>) -> float

    3. Median(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8237d48b0>) -> float

    4. Median(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227001f0>) -> float
    """
@overload
def Min(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Min(*args, **kwargs)
    Overloaded function.

    1. Min(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227f9270>) -> tuple[float, int]

    2. Min(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bcaab0>) -> tuple[float, int]

    3. Min(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bd7af0>) -> tuple[float, int]

    4. Min(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe822787830>) -> tuple[float, int]
    """
@overload
def Min(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Min(*args, **kwargs)
    Overloaded function.

    1. Min(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227f9270>) -> tuple[float, int]

    2. Min(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bcaab0>) -> tuple[float, int]

    3. Min(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bd7af0>) -> tuple[float, int]

    4. Min(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe822787830>) -> tuple[float, int]
    """
@overload
def Min(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Min(*args, **kwargs)
    Overloaded function.

    1. Min(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227f9270>) -> tuple[float, int]

    2. Min(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bcaab0>) -> tuple[float, int]

    3. Min(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bd7af0>) -> tuple[float, int]

    4. Min(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe822787830>) -> tuple[float, int]
    """
@overload
def Min(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, int]:
    """Min(*args, **kwargs)
    Overloaded function.

    1. Min(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227f9270>) -> tuple[float, int]

    2. Min(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bcaab0>) -> tuple[float, int]

    3. Min(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bd7af0>) -> tuple[float, int]

    4. Min(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe822787830>) -> tuple[float, int]
    """
@overload
def RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """RootMeanSquare(*args, **kwargs)
    Overloaded function.

    1. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820b2cfb0>) -> float

    2. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba1f30>) -> float

    3. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba2070>) -> float

    4. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bc95b0>) -> float
    """
@overload
def RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """RootMeanSquare(*args, **kwargs)
    Overloaded function.

    1. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820b2cfb0>) -> float

    2. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba1f30>) -> float

    3. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba2070>) -> float

    4. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bc95b0>) -> float
    """
@overload
def RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """RootMeanSquare(*args, **kwargs)
    Overloaded function.

    1. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820b2cfb0>) -> float

    2. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba1f30>) -> float

    3. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba2070>) -> float

    4. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bc95b0>) -> float
    """
@overload
def RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """RootMeanSquare(*args, **kwargs)
    Overloaded function.

    1. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820b2cfb0>) -> float

    2. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba1f30>) -> float

    3. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba2070>) -> float

    4. RootMeanSquare(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bc95b0>) -> float
    """
@overload
def Sum(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Sum(*args, **kwargs)
    Overloaded function.

    1. Sum(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba0470>) -> float

    2. Sum(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227decf0>) -> float

    3. Sum(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba05f0>) -> float

    4. Sum(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227dc970>) -> float
    """
@overload
def Sum(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Sum(*args, **kwargs)
    Overloaded function.

    1. Sum(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba0470>) -> float

    2. Sum(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227decf0>) -> float

    3. Sum(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba05f0>) -> float

    4. Sum(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227dc970>) -> float
    """
@overload
def Sum(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Sum(*args, **kwargs)
    Overloaded function.

    1. Sum(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba0470>) -> float

    2. Sum(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227decf0>) -> float

    3. Sum(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba05f0>) -> float

    4. Sum(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227dc970>) -> float
    """
@overload
def Sum(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> float:
    """Sum(*args, **kwargs)
    Overloaded function.

    1. Sum(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba0470>) -> float

    2. Sum(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227decf0>) -> float

    3. Sum(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820ba05f0>) -> float

    4. Sum(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227dc970>) -> float
    """
@overload
def Variance(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float]:
    """Variance(*args, **kwargs)
    Overloaded function.

    1. Variance(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bcd0b0>) -> tuple[float, float]

    2. Variance(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe822712cb0>) -> tuple[float, float]

    3. Variance(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bd5ab0>) -> tuple[float, float]

    4. Variance(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227dceb0>) -> tuple[float, float]
    """
@overload
def Variance(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float]:
    """Variance(*args, **kwargs)
    Overloaded function.

    1. Variance(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bcd0b0>) -> tuple[float, float]

    2. Variance(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe822712cb0>) -> tuple[float, float]

    3. Variance(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bd5ab0>) -> tuple[float, float]

    4. Variance(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227dceb0>) -> tuple[float, float]
    """
@overload
def Variance(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float]:
    """Variance(*args, **kwargs)
    Overloaded function.

    1. Variance(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bcd0b0>) -> tuple[float, float]

    2. Variance(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe822712cb0>) -> tuple[float, float]

    3. Variance(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bd5ab0>) -> tuple[float, float]

    4. Variance(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227dceb0>) -> tuple[float, float]
    """
@overload
def Variance(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = ...) -> tuple[float, float]:
    """Variance(*args, **kwargs)
    Overloaded function.

    1. Variance(model_part: Kratos.ModelPart, variable: Kratos.DoubleVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bcd0b0>) -> tuple[float, float]

    2. Variance(model_part: Kratos.ModelPart, variable: Kratos.Array1DVariable3, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe822712cb0>) -> tuple[float, float]

    3. Variance(model_part: Kratos.ModelPart, variable: Kratos.VectorVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe820bd5ab0>) -> tuple[float, float]

    4. Variance(model_part: Kratos.ModelPart, variable: Kratos.MatrixVariable, norm_type: str, parameters: Kratos.Parameters = <Kratos.Parameters object at 0x7fe8227dceb0>) -> tuple[float, float]
    """
