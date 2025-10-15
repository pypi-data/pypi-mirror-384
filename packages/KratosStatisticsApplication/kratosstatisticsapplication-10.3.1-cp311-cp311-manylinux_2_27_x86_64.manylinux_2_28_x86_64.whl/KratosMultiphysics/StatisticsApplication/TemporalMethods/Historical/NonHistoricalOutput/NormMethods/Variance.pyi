import Kratos
import KratosStatisticsApplication.TemporalMethods

class Array(KratosStatisticsApplication.TemporalMethods.TemporalMethod):
    def __init__(self, arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3, arg3: int, arg4: Kratos.DoubleVariable, arg5: Kratos.DoubleVariable) -> None:
        """__init__(self: KratosStatisticsApplication.TemporalMethods.Historical.NonHistoricalOutput.NormMethods.Variance.Array, arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3, arg3: int, arg4: Kratos.DoubleVariable, arg5: Kratos.DoubleVariable) -> None"""

class Double(KratosStatisticsApplication.TemporalMethods.TemporalMethod):
    def __init__(self, arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.DoubleVariable, arg3: int, arg4: Kratos.DoubleVariable, arg5: Kratos.DoubleVariable) -> None:
        """__init__(self: KratosStatisticsApplication.TemporalMethods.Historical.NonHistoricalOutput.NormMethods.Variance.Double, arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.DoubleVariable, arg3: int, arg4: Kratos.DoubleVariable, arg5: Kratos.DoubleVariable) -> None"""

class Matrix(KratosStatisticsApplication.TemporalMethods.TemporalMethod):
    def __init__(self, arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.MatrixVariable, arg3: int, arg4: Kratos.DoubleVariable, arg5: Kratos.DoubleVariable) -> None:
        """__init__(self: KratosStatisticsApplication.TemporalMethods.Historical.NonHistoricalOutput.NormMethods.Variance.Matrix, arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.MatrixVariable, arg3: int, arg4: Kratos.DoubleVariable, arg5: Kratos.DoubleVariable) -> None"""

class Vector(KratosStatisticsApplication.TemporalMethods.TemporalMethod):
    def __init__(self, arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.VectorVariable, arg3: int, arg4: Kratos.DoubleVariable, arg5: Kratos.DoubleVariable) -> None:
        """__init__(self: KratosStatisticsApplication.TemporalMethods.Historical.NonHistoricalOutput.NormMethods.Variance.Vector, arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.VectorVariable, arg3: int, arg4: Kratos.DoubleVariable, arg5: Kratos.DoubleVariable) -> None"""
