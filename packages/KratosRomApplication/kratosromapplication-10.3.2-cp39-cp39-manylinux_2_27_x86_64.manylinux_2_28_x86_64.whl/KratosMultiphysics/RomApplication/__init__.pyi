import Kratos
from typing import overload

class AnnPromGlobalROMBuilderAndSolver(Kratos.ResidualBasedBlockBuilderAndSolver):
    def __init__(self, arg0: Kratos.LinearSolver, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosRomApplication.AnnPromGlobalROMBuilderAndSolver, arg0: Kratos.LinearSolver, arg1: Kratos.Parameters) -> None"""
    def RunDecoder(self, arg0: Kratos.ModelPart, arg1: Kratos.Vector) -> Kratos.Vector:
        """RunDecoder(self: KratosRomApplication.AnnPromGlobalROMBuilderAndSolver, arg0: Kratos.ModelPart, arg1: Kratos.Vector) -> Kratos.Vector"""
    def SetDecoderParameters(self, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Matrix, arg3: Kratos.Matrix, arg4: Kratos.Matrix, arg5: Kratos.Vector) -> None:
        """SetDecoderParameters(self: KratosRomApplication.AnnPromGlobalROMBuilderAndSolver, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Matrix, arg3: Kratos.Matrix, arg4: Kratos.Matrix, arg5: Kratos.Vector) -> None"""
    def SetNNLayer(self, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Matrix) -> None:
        """SetNNLayer(self: KratosRomApplication.AnnPromGlobalROMBuilderAndSolver, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Matrix) -> None"""
    def SetNumberOfROMModes(self, arg0: int) -> None:
        """SetNumberOfROMModes(self: KratosRomApplication.AnnPromGlobalROMBuilderAndSolver, arg0: int) -> None"""

class AnnPromLeastSquaresPetrovGalerkinROMBuilderAndSolver(Kratos.ResidualBasedBlockBuilderAndSolver):
    def __init__(self, arg0: Kratos.LinearSolver, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosRomApplication.AnnPromLeastSquaresPetrovGalerkinROMBuilderAndSolver, arg0: Kratos.LinearSolver, arg1: Kratos.Parameters) -> None"""
    def RunDecoder(self, arg0: Kratos.ModelPart, arg1: Kratos.Vector) -> Kratos.Vector:
        """RunDecoder(self: KratosRomApplication.AnnPromLeastSquaresPetrovGalerkinROMBuilderAndSolver, arg0: Kratos.ModelPart, arg1: Kratos.Vector) -> Kratos.Vector"""
    def SetDecoderParameters(self, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Matrix, arg3: Kratos.Matrix, arg4: Kratos.Matrix, arg5: Kratos.Vector) -> None:
        """SetDecoderParameters(self: KratosRomApplication.AnnPromLeastSquaresPetrovGalerkinROMBuilderAndSolver, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Matrix, arg3: Kratos.Matrix, arg4: Kratos.Matrix, arg5: Kratos.Vector) -> None"""
    def SetNNLayer(self, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Matrix) -> None:
        """SetNNLayer(self: KratosRomApplication.AnnPromLeastSquaresPetrovGalerkinROMBuilderAndSolver, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Matrix) -> None"""
    def SetNumberOfROMModes(self, arg0: int) -> None:
        """SetNumberOfROMModes(self: KratosRomApplication.AnnPromLeastSquaresPetrovGalerkinROMBuilderAndSolver, arg0: int) -> None"""

class GlobalPetrovGalerkinROMBuilderAndSolver(GlobalROMBuilderAndSolver):
    def __init__(self, arg0: Kratos.LinearSolver, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosRomApplication.GlobalPetrovGalerkinROMBuilderAndSolver, arg0: Kratos.LinearSolver, arg1: Kratos.Parameters) -> None"""

class GlobalROMBuilderAndSolver(Kratos.ResidualBasedBlockBuilderAndSolver):
    def __init__(self, arg0: Kratos.LinearSolver, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosRomApplication.GlobalROMBuilderAndSolver, arg0: Kratos.LinearSolver, arg1: Kratos.Parameters) -> None"""

class HRomVisualizationMeshModeler(Kratos.Modeler):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosRomApplication.HRomVisualizationMeshModeler, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class KratosRomApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosRomApplication.KratosRomApplication) -> None"""

class LeastSquaresPetrovGalerkinROMBuilderAndSolver(GlobalROMBuilderAndSolver):
    def __init__(self, arg0: Kratos.LinearSolver, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosRomApplication.LeastSquaresPetrovGalerkinROMBuilderAndSolver, arg0: Kratos.LinearSolver, arg1: Kratos.Parameters) -> None"""
    def BuildAndApplyDirichletConditions(self, arg0: Kratos.Scheme, arg1: Kratos.ModelPart, arg2: Kratos.CompressedMatrix, arg3: Kratos.Vector, arg4: Kratos.Vector) -> None:
        """BuildAndApplyDirichletConditions(self: KratosRomApplication.LeastSquaresPetrovGalerkinROMBuilderAndSolver, arg0: Kratos.Scheme, arg1: Kratos.ModelPart, arg2: Kratos.CompressedMatrix, arg3: Kratos.Vector, arg4: Kratos.Vector) -> None"""
    def GetRightROMBasis(self, arg0: Kratos.ModelPart, arg1: Kratos.Matrix) -> None:
        """GetRightROMBasis(self: KratosRomApplication.LeastSquaresPetrovGalerkinROMBuilderAndSolver, arg0: Kratos.ModelPart, arg1: Kratos.Matrix) -> None"""

class PetrovGalerkinROMBuilderAndSolver(ROMBuilderAndSolver):
    def __init__(self, arg0: Kratos.LinearSolver, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosRomApplication.PetrovGalerkinROMBuilderAndSolver, arg0: Kratos.LinearSolver, arg1: Kratos.Parameters) -> None"""

class ROMBuilderAndSolver(Kratos.BuilderAndSolver):
    def __init__(self, arg0: Kratos.LinearSolver, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosRomApplication.ROMBuilderAndSolver, arg0: Kratos.LinearSolver, arg1: Kratos.Parameters) -> None"""

class RomAuxiliaryUtilities:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    @staticmethod
    def GetConditionIdsInModelPart(arg0: Kratos.ModelPart) -> list[int]:
        """GetConditionIdsInModelPart(arg0: Kratos.ModelPart) -> list[int]"""
    @staticmethod
    def GetConditionIdsNotInHRomModelPart(arg0: Kratos.ModelPart, arg1: dict[str, dict[int, float]]) -> list[int]:
        """GetConditionIdsNotInHRomModelPart(arg0: Kratos.ModelPart, arg1: dict[str, dict[int, float]]) -> list[int]"""
    @staticmethod
    def GetElementIdsInModelPart(arg0: Kratos.ModelPart) -> list[int]:
        """GetElementIdsInModelPart(arg0: Kratos.ModelPart) -> list[int]"""
    @staticmethod
    def GetElementIdsNotInHRomModelPart(arg0: Kratos.ModelPart, arg1: dict[str, dict[int, float]]) -> list[int]:
        """GetElementIdsNotInHRomModelPart(arg0: Kratos.ModelPart, arg1: dict[str, dict[int, float]]) -> list[int]"""
    @overload
    @staticmethod
    def GetHRomConditionParentsIds(arg0: Kratos.ModelPart, arg1: list[int]) -> list[int]:
        """GetHRomConditionParentsIds(*args, **kwargs)
        Overloaded function.

        1. GetHRomConditionParentsIds(arg0: Kratos.ModelPart, arg1: list[int]) -> list[int]

        2. GetHRomConditionParentsIds(arg0: Kratos.ModelPart, arg1: dict[str, dict[int, float]]) -> list[int]
        """
    @overload
    @staticmethod
    def GetHRomConditionParentsIds(arg0: Kratos.ModelPart, arg1: dict[str, dict[int, float]]) -> list[int]:
        """GetHRomConditionParentsIds(*args, **kwargs)
        Overloaded function.

        1. GetHRomConditionParentsIds(arg0: Kratos.ModelPart, arg1: list[int]) -> list[int]

        2. GetHRomConditionParentsIds(arg0: Kratos.ModelPart, arg1: dict[str, dict[int, float]]) -> list[int]
        """
    @staticmethod
    def GetHRomMinimumConditionsIds(arg0: Kratos.ModelPart, arg1: dict[int, float]) -> list[int]:
        """GetHRomMinimumConditionsIds(arg0: Kratos.ModelPart, arg1: dict[int, float]) -> list[int]"""
    @staticmethod
    def GetNodalNeighbouringConditionIds(arg0: Kratos.ModelPart, arg1: list[int], arg2: bool) -> list[int]:
        """GetNodalNeighbouringConditionIds(arg0: Kratos.ModelPart, arg1: list[int], arg2: bool) -> list[int]"""
    @overload
    @staticmethod
    def GetNodalNeighbouringElementIds(arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> list[int]:
        """GetNodalNeighbouringElementIds(*args, **kwargs)
        Overloaded function.

        1. GetNodalNeighbouringElementIds(arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> list[int]

        2. GetNodalNeighbouringElementIds(arg0: Kratos.ModelPart, arg1: list[int], arg2: bool) -> list[int]
        """
    @overload
    @staticmethod
    def GetNodalNeighbouringElementIds(arg0: Kratos.ModelPart, arg1: list[int], arg2: bool) -> list[int]:
        """GetNodalNeighbouringElementIds(*args, **kwargs)
        Overloaded function.

        1. GetNodalNeighbouringElementIds(arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> list[int]

        2. GetNodalNeighbouringElementIds(arg0: Kratos.ModelPart, arg1: list[int], arg2: bool) -> list[int]
        """
    @staticmethod
    def GetNodalNeighbouringElementIdsNotInHRom(arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: dict[str, dict[int, float]]) -> list[int]:
        """GetNodalNeighbouringElementIdsNotInHRom(arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: dict[str, dict[int, float]]) -> list[int]"""
    @staticmethod
    def ProjectRomSolutionIncrementToNodes(arg0: list[str], arg1: Kratos.ModelPart) -> None:
        """ProjectRomSolutionIncrementToNodes(arg0: list[str], arg1: Kratos.ModelPart) -> None"""
    @staticmethod
    def SetHRomComputingModelPart(arg0: Kratos.Parameters, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart) -> None:
        """SetHRomComputingModelPart(arg0: Kratos.Parameters, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart) -> None"""
    @staticmethod
    def SetHRomComputingModelPartWithLists(arg0: list[int], arg1: list[int], arg2: Kratos.ModelPart, arg3: Kratos.ModelPart) -> None:
        """SetHRomComputingModelPartWithLists(arg0: list[int], arg1: list[int], arg2: Kratos.ModelPart, arg3: Kratos.ModelPart) -> None"""
    @staticmethod
    def SetHRomComputingModelPartWithNeighbours(arg0: Kratos.Parameters, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart) -> None:
        """SetHRomComputingModelPartWithNeighbours(arg0: Kratos.Parameters, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart) -> None"""
    @staticmethod
    def SetHRomVolumetricVisualizationModelPart(arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """SetHRomVolumetricVisualizationModelPart(arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""

class RomResidualsUtility:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters, arg2: Kratos.Scheme) -> None:
        """__init__(self: KratosRomApplication.RomResidualsUtility, arg0: Kratos.ModelPart, arg1: Kratos.Parameters, arg2: Kratos.Scheme) -> None"""
    def GetProjectedResidualsOntoJPhi(self, arg0: Kratos.Matrix) -> Kratos.Matrix:
        """GetProjectedResidualsOntoJPhi(self: KratosRomApplication.RomResidualsUtility, arg0: Kratos.Matrix) -> Kratos.Matrix"""
    def GetProjectedResidualsOntoPhi(self) -> Kratos.Matrix:
        """GetProjectedResidualsOntoPhi(self: KratosRomApplication.RomResidualsUtility) -> Kratos.Matrix"""
    def GetProjectedResidualsOntoPsi(self) -> Kratos.Matrix:
        """GetProjectedResidualsOntoPsi(self: KratosRomApplication.RomResidualsUtility) -> Kratos.Matrix"""
