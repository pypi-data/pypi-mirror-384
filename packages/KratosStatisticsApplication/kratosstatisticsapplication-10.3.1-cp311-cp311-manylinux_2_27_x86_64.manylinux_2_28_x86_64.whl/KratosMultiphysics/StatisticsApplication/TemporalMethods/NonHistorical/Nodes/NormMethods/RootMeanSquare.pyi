import Kratos
import KratosStatisticsApplication.TemporalMethods

class Array(KratosStatisticsApplication.TemporalMethods.TemporalMethod):
    def __init__(self, arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3, arg3: int, arg4: Kratos.DoubleVariable) -> None:
        """__init__(self: KratosStatisticsApplication.TemporalMethods.NonHistorical.Nodes.NormMethods.RootMeanSquare.Array, arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.Array1DVariable3, arg3: int, arg4: Kratos.DoubleVariable) -> None"""

class Double(KratosStatisticsApplication.TemporalMethods.TemporalMethod):
    def __init__(self, arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.DoubleVariable, arg3: int, arg4: Kratos.DoubleVariable) -> None:
        """__init__(self: KratosStatisticsApplication.TemporalMethods.NonHistorical.Nodes.NormMethods.RootMeanSquare.Double, arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.DoubleVariable, arg3: int, arg4: Kratos.DoubleVariable) -> None"""

class Matrix(KratosStatisticsApplication.TemporalMethods.TemporalMethod):
    def __init__(self, arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.MatrixVariable, arg3: int, arg4: Kratos.DoubleVariable) -> None:
        """__init__(self: KratosStatisticsApplication.TemporalMethods.NonHistorical.Nodes.NormMethods.RootMeanSquare.Matrix, arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.MatrixVariable, arg3: int, arg4: Kratos.DoubleVariable) -> None"""

class Vector(KratosStatisticsApplication.TemporalMethods.TemporalMethod):
    def __init__(self, arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.VectorVariable, arg3: int, arg4: Kratos.DoubleVariable) -> None:
        """__init__(self: KratosStatisticsApplication.TemporalMethods.NonHistorical.Nodes.NormMethods.RootMeanSquare.Vector, arg0: Kratos.ModelPart, arg1: str, arg2: Kratos.VectorVariable, arg3: int, arg4: Kratos.DoubleVariable) -> None"""
