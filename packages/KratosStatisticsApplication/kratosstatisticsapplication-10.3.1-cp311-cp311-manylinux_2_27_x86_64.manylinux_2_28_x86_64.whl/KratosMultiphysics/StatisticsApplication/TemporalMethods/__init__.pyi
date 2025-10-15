import Kratos
from . import Historical as Historical, NonHistorical as NonHistorical

class TemporalMethod:
    def __init__(self, arg0: Kratos.ModelPart, arg1: int) -> None:
        """__init__(self: KratosStatisticsApplication.TemporalMethods.TemporalMethod, arg0: Kratos.ModelPart, arg1: int) -> None"""
    def CalculateStatistics(self) -> None:
        """CalculateStatistics(self: KratosStatisticsApplication.TemporalMethods.TemporalMethod) -> None"""
    def GetEchoLevel(self) -> int:
        """GetEchoLevel(self: KratosStatisticsApplication.TemporalMethods.TemporalMethod) -> int"""
    def GetModelPart(self) -> Kratos.ModelPart:
        """GetModelPart(self: KratosStatisticsApplication.TemporalMethods.TemporalMethod) -> Kratos.ModelPart"""
    def GetTotalTime(self) -> float:
        """GetTotalTime(self: KratosStatisticsApplication.TemporalMethods.TemporalMethod) -> float"""
    def InitializeStatisticsMethod(self, arg0: float) -> None:
        """InitializeStatisticsMethod(self: KratosStatisticsApplication.TemporalMethods.TemporalMethod, arg0: float) -> None"""
