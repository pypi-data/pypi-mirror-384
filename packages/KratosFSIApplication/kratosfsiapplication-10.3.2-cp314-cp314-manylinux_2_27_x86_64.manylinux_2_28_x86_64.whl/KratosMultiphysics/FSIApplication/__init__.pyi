import Kratos
from typing import overload

class AitkenConvergenceAccelerator(Kratos.ConvergenceAccelerator):
    @overload
    def __init__(self, arg0: float) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFSIApplication.AitkenConvergenceAccelerator, arg0: float) -> None

        2. __init__(self: KratosFSIApplication.AitkenConvergenceAccelerator, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFSIApplication.AitkenConvergenceAccelerator, arg0: float) -> None

        2. __init__(self: KratosFSIApplication.AitkenConvergenceAccelerator, arg0: Kratos.Parameters) -> None
        """

class ConstantRelaxationConvergenceAccelerator(Kratos.ConvergenceAccelerator):
    @overload
    def __init__(self, arg0: float) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFSIApplication.ConstantRelaxationConvergenceAccelerator, arg0: float) -> None

        2. __init__(self: KratosFSIApplication.ConstantRelaxationConvergenceAccelerator, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFSIApplication.ConstantRelaxationConvergenceAccelerator, arg0: float) -> None

        2. __init__(self: KratosFSIApplication.ConstantRelaxationConvergenceAccelerator, arg0: Kratos.Parameters) -> None
        """

class FSIUtils:
    def __init__(self) -> None:
        """__init__(self: KratosFSIApplication.FSIUtils) -> None"""
    def CheckPressureConvergence(self, arg0: Kratos.NodesArray, arg1: float, arg2: float) -> bool:
        """CheckPressureConvergence(self: KratosFSIApplication.FSIUtils, arg0: Kratos.NodesArray, arg1: float, arg2: float) -> bool"""
    def StructuralPressurePrediction(self, arg0: Kratos.DoubleVariable, arg1: Kratos.NodesArray, arg2: int, arg3: int) -> None:
        """StructuralPressurePrediction(self: KratosFSIApplication.FSIUtils, arg0: Kratos.DoubleVariable, arg1: Kratos.NodesArray, arg2: int, arg3: int) -> None"""

class IBQNMVQNConvergenceAccelerator(Kratos.ConvergenceAccelerator):
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(self: KratosFSIApplication.IBQNMVQNConvergenceAccelerator, arg0: Kratos.Parameters) -> None"""
    def UpdateSolutionLeft(self, arg0: Kratos.Vector, arg1: Kratos.Vector, arg2: Kratos.Vector) -> None:
        """UpdateSolutionLeft(self: KratosFSIApplication.IBQNMVQNConvergenceAccelerator, arg0: Kratos.Vector, arg1: Kratos.Vector, arg2: Kratos.Vector) -> None"""
    def UpdateSolutionRight(self, arg0: Kratos.Vector, arg1: Kratos.Vector, arg2: Kratos.Vector) -> None:
        """UpdateSolutionRight(self: KratosFSIApplication.IBQNMVQNConvergenceAccelerator, arg0: Kratos.Vector, arg1: Kratos.Vector, arg2: Kratos.Vector) -> None"""

class IBQNMVQNRandomizedSVDConvergenceAccelerator(IBQNMVQNConvergenceAccelerator):
    def __init__(self, arg0: Kratos.DenseQRDecompositionType, arg1: Kratos.DenseSingularValueDecomposition, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosFSIApplication.IBQNMVQNRandomizedSVDConvergenceAccelerator, arg0: Kratos.DenseQRDecompositionType, arg1: Kratos.DenseSingularValueDecomposition, arg2: Kratos.Parameters) -> None"""

class KratosFSIApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosFSIApplication.KratosFSIApplication) -> None"""

class MVQNFullJacobianConvergenceAccelerator(Kratos.ConvergenceAccelerator):
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(self: KratosFSIApplication.MVQNFullJacobianConvergenceAccelerator, arg0: Kratos.Parameters) -> None"""

class MVQNRandomizedSVDConvergenceAccelerator(MVQNFullJacobianConvergenceAccelerator):
    def __init__(self, arg0: Kratos.DenseQRDecompositionType, arg1: Kratos.DenseSingularValueDecomposition, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosFSIApplication.MVQNRandomizedSVDConvergenceAccelerator, arg0: Kratos.DenseQRDecompositionType, arg1: Kratos.DenseSingularValueDecomposition, arg2: Kratos.Parameters) -> None"""

class MVQNRecursiveJacobianConvergenceAccelerator(Kratos.ConvergenceAccelerator):
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFSIApplication.MVQNRecursiveJacobianConvergenceAccelerator, arg0: Kratos.Parameters) -> None

        2. __init__(self: KratosFSIApplication.MVQNRecursiveJacobianConvergenceAccelerator, arg0: float, arg1: int, arg2: float) -> None
        """
    @overload
    def __init__(self, arg0: float, arg1: int, arg2: float) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFSIApplication.MVQNRecursiveJacobianConvergenceAccelerator, arg0: Kratos.Parameters) -> None

        2. __init__(self: KratosFSIApplication.MVQNRecursiveJacobianConvergenceAccelerator, arg0: float, arg1: int, arg2: float) -> None
        """

class PartitionedFSIUtilitiesArray2D:
    def __init__(self) -> None:
        """__init__(self: KratosFSIApplication.PartitionedFSIUtilitiesArray2D) -> None"""
    @overload
    def CalculateTractionFromPressureValues(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: bool) -> None:
        """CalculateTractionFromPressureValues(*args, **kwargs)
        Overloaded function.

        1. CalculateTractionFromPressureValues(self: KratosFSIApplication.PartitionedFSIUtilitiesArray2D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: bool) -> None

        2. CalculateTractionFromPressureValues(self: KratosFSIApplication.PartitionedFSIUtilitiesArray2D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: bool) -> None
        """
    @overload
    def CalculateTractionFromPressureValues(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: bool) -> None:
        """CalculateTractionFromPressureValues(*args, **kwargs)
        Overloaded function.

        1. CalculateTractionFromPressureValues(self: KratosFSIApplication.PartitionedFSIUtilitiesArray2D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: bool) -> None

        2. CalculateTractionFromPressureValues(self: KratosFSIApplication.PartitionedFSIUtilitiesArray2D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: bool) -> None
        """
    def CheckCurrentCoordinatesFluid(self, arg0: Kratos.ModelPart, arg1: float) -> None:
        """CheckCurrentCoordinatesFluid(self: KratosFSIApplication.PartitionedFSIUtilitiesArray2D, arg0: Kratos.ModelPart, arg1: float) -> None"""
    def CheckCurrentCoordinatesStructure(self, arg0: Kratos.ModelPart, arg1: float) -> None:
        """CheckCurrentCoordinatesStructure(self: KratosFSIApplication.PartitionedFSIUtilitiesArray2D, arg0: Kratos.ModelPart, arg1: float) -> None"""
    def ComputeAndPrintFluidInterfaceNorms(self, arg0: Kratos.ModelPart) -> None:
        """ComputeAndPrintFluidInterfaceNorms(self: KratosFSIApplication.PartitionedFSIUtilitiesArray2D, arg0: Kratos.ModelPart) -> None"""
    def ComputeAndPrintStructureInterfaceNorms(self, arg0: Kratos.ModelPart) -> None:
        """ComputeAndPrintStructureInterfaceNorms(self: KratosFSIApplication.PartitionedFSIUtilitiesArray2D, arg0: Kratos.ModelPart) -> None"""
    def ComputeInterfaceResidualNorm(self, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3, arg4: str) -> float:
        """ComputeInterfaceResidualNorm(self: KratosFSIApplication.PartitionedFSIUtilitiesArray2D, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3, arg4: str) -> float"""
    def ComputeInterfaceResidualVector(self, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3, arg4: Kratos.Vector, arg5: str, arg6: Kratos.DoubleVariable) -> None:
        """ComputeInterfaceResidualVector(self: KratosFSIApplication.PartitionedFSIUtilitiesArray2D, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3, arg4: Kratos.Vector, arg5: str, arg6: Kratos.DoubleVariable) -> None"""
    def CreateCouplingSkin(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """CreateCouplingSkin(self: KratosFSIApplication.PartitionedFSIUtilitiesArray2D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
    def EmbeddedPressureToPositiveFacePressureInterpolator(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """EmbeddedPressureToPositiveFacePressureInterpolator(self: KratosFSIApplication.PartitionedFSIUtilitiesArray2D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
    def GetInterfaceArea(self, arg0: Kratos.ModelPart) -> float:
        """GetInterfaceArea(self: KratosFSIApplication.PartitionedFSIUtilitiesArray2D, arg0: Kratos.ModelPart) -> float"""
    def GetInterfaceResidualSize(self, arg0: Kratos.ModelPart) -> int:
        """GetInterfaceResidualSize(self: KratosFSIApplication.PartitionedFSIUtilitiesArray2D, arg0: Kratos.ModelPart) -> int"""
    def InitializeInterfaceVector(self, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Vector) -> None:
        """InitializeInterfaceVector(self: KratosFSIApplication.PartitionedFSIUtilitiesArray2D, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Vector) -> None"""
    def SetUpInterfaceVector(self, arg0: Kratos.ModelPart) -> Kratos.Vector:
        """SetUpInterfaceVector(self: KratosFSIApplication.PartitionedFSIUtilitiesArray2D, arg0: Kratos.ModelPart) -> Kratos.Vector"""
    def UpdateInterfaceValues(self, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Vector) -> None:
        """UpdateInterfaceValues(self: KratosFSIApplication.PartitionedFSIUtilitiesArray2D, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Vector) -> None"""

class PartitionedFSIUtilitiesArray3D:
    def __init__(self) -> None:
        """__init__(self: KratosFSIApplication.PartitionedFSIUtilitiesArray3D) -> None"""
    @overload
    def CalculateTractionFromPressureValues(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: bool) -> None:
        """CalculateTractionFromPressureValues(*args, **kwargs)
        Overloaded function.

        1. CalculateTractionFromPressureValues(self: KratosFSIApplication.PartitionedFSIUtilitiesArray3D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: bool) -> None

        2. CalculateTractionFromPressureValues(self: KratosFSIApplication.PartitionedFSIUtilitiesArray3D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: bool) -> None
        """
    @overload
    def CalculateTractionFromPressureValues(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: bool) -> None:
        """CalculateTractionFromPressureValues(*args, **kwargs)
        Overloaded function.

        1. CalculateTractionFromPressureValues(self: KratosFSIApplication.PartitionedFSIUtilitiesArray3D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: bool) -> None

        2. CalculateTractionFromPressureValues(self: KratosFSIApplication.PartitionedFSIUtilitiesArray3D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: bool) -> None
        """
    def CheckCurrentCoordinatesFluid(self, arg0: Kratos.ModelPart, arg1: float) -> None:
        """CheckCurrentCoordinatesFluid(self: KratosFSIApplication.PartitionedFSIUtilitiesArray3D, arg0: Kratos.ModelPart, arg1: float) -> None"""
    def CheckCurrentCoordinatesStructure(self, arg0: Kratos.ModelPart, arg1: float) -> None:
        """CheckCurrentCoordinatesStructure(self: KratosFSIApplication.PartitionedFSIUtilitiesArray3D, arg0: Kratos.ModelPart, arg1: float) -> None"""
    def ComputeAndPrintFluidInterfaceNorms(self, arg0: Kratos.ModelPart) -> None:
        """ComputeAndPrintFluidInterfaceNorms(self: KratosFSIApplication.PartitionedFSIUtilitiesArray3D, arg0: Kratos.ModelPart) -> None"""
    def ComputeAndPrintStructureInterfaceNorms(self, arg0: Kratos.ModelPart) -> None:
        """ComputeAndPrintStructureInterfaceNorms(self: KratosFSIApplication.PartitionedFSIUtilitiesArray3D, arg0: Kratos.ModelPart) -> None"""
    def ComputeInterfaceResidualNorm(self, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3, arg4: str) -> float:
        """ComputeInterfaceResidualNorm(self: KratosFSIApplication.PartitionedFSIUtilitiesArray3D, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3, arg4: str) -> float"""
    def ComputeInterfaceResidualVector(self, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3, arg4: Kratos.Vector, arg5: str, arg6: Kratos.DoubleVariable) -> None:
        """ComputeInterfaceResidualVector(self: KratosFSIApplication.PartitionedFSIUtilitiesArray3D, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3, arg4: Kratos.Vector, arg5: str, arg6: Kratos.DoubleVariable) -> None"""
    def CreateCouplingSkin(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """CreateCouplingSkin(self: KratosFSIApplication.PartitionedFSIUtilitiesArray3D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
    def EmbeddedPressureToPositiveFacePressureInterpolator(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """EmbeddedPressureToPositiveFacePressureInterpolator(self: KratosFSIApplication.PartitionedFSIUtilitiesArray3D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
    def GetInterfaceArea(self, arg0: Kratos.ModelPart) -> float:
        """GetInterfaceArea(self: KratosFSIApplication.PartitionedFSIUtilitiesArray3D, arg0: Kratos.ModelPart) -> float"""
    def GetInterfaceResidualSize(self, arg0: Kratos.ModelPart) -> int:
        """GetInterfaceResidualSize(self: KratosFSIApplication.PartitionedFSIUtilitiesArray3D, arg0: Kratos.ModelPart) -> int"""
    def InitializeInterfaceVector(self, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Vector) -> None:
        """InitializeInterfaceVector(self: KratosFSIApplication.PartitionedFSIUtilitiesArray3D, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Vector) -> None"""
    def SetUpInterfaceVector(self, arg0: Kratos.ModelPart) -> Kratos.Vector:
        """SetUpInterfaceVector(self: KratosFSIApplication.PartitionedFSIUtilitiesArray3D, arg0: Kratos.ModelPart) -> Kratos.Vector"""
    def UpdateInterfaceValues(self, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Vector) -> None:
        """UpdateInterfaceValues(self: KratosFSIApplication.PartitionedFSIUtilitiesArray3D, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Vector) -> None"""

class PartitionedFSIUtilitiesDouble2D:
    def __init__(self) -> None:
        """__init__(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble2D) -> None"""
    @overload
    def CalculateTractionFromPressureValues(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: bool) -> None:
        """CalculateTractionFromPressureValues(*args, **kwargs)
        Overloaded function.

        1. CalculateTractionFromPressureValues(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble2D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: bool) -> None

        2. CalculateTractionFromPressureValues(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble2D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: bool) -> None
        """
    @overload
    def CalculateTractionFromPressureValues(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: bool) -> None:
        """CalculateTractionFromPressureValues(*args, **kwargs)
        Overloaded function.

        1. CalculateTractionFromPressureValues(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble2D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: bool) -> None

        2. CalculateTractionFromPressureValues(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble2D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: bool) -> None
        """
    def CheckCurrentCoordinatesFluid(self, arg0: Kratos.ModelPart, arg1: float) -> None:
        """CheckCurrentCoordinatesFluid(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble2D, arg0: Kratos.ModelPart, arg1: float) -> None"""
    def CheckCurrentCoordinatesStructure(self, arg0: Kratos.ModelPart, arg1: float) -> None:
        """CheckCurrentCoordinatesStructure(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble2D, arg0: Kratos.ModelPart, arg1: float) -> None"""
    def ComputeAndPrintFluidInterfaceNorms(self, arg0: Kratos.ModelPart) -> None:
        """ComputeAndPrintFluidInterfaceNorms(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble2D, arg0: Kratos.ModelPart) -> None"""
    def ComputeAndPrintStructureInterfaceNorms(self, arg0: Kratos.ModelPart) -> None:
        """ComputeAndPrintStructureInterfaceNorms(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble2D, arg0: Kratos.ModelPart) -> None"""
    def ComputeInterfaceResidualNorm(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable, arg4: str) -> float:
        """ComputeInterfaceResidualNorm(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble2D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable, arg4: str) -> float"""
    def ComputeInterfaceResidualVector(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable, arg4: Kratos.Vector, arg5: str, arg6: Kratos.DoubleVariable) -> None:
        """ComputeInterfaceResidualVector(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble2D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable, arg4: Kratos.Vector, arg5: str, arg6: Kratos.DoubleVariable) -> None"""
    def CreateCouplingSkin(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """CreateCouplingSkin(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble2D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
    def EmbeddedPressureToPositiveFacePressureInterpolator(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """EmbeddedPressureToPositiveFacePressureInterpolator(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble2D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
    def GetInterfaceArea(self, arg0: Kratos.ModelPart) -> float:
        """GetInterfaceArea(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble2D, arg0: Kratos.ModelPart) -> float"""
    def GetInterfaceResidualSize(self, arg0: Kratos.ModelPart) -> int:
        """GetInterfaceResidualSize(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble2D, arg0: Kratos.ModelPart) -> int"""
    def InitializeInterfaceVector(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Vector) -> None:
        """InitializeInterfaceVector(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble2D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Vector) -> None"""
    def SetUpInterfaceVector(self, arg0: Kratos.ModelPart) -> Kratos.Vector:
        """SetUpInterfaceVector(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble2D, arg0: Kratos.ModelPart) -> Kratos.Vector"""
    def UpdateInterfaceValues(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Vector) -> None:
        """UpdateInterfaceValues(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble2D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Vector) -> None"""

class PartitionedFSIUtilitiesDouble3D:
    def __init__(self) -> None:
        """__init__(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble3D) -> None"""
    @overload
    def CalculateTractionFromPressureValues(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: bool) -> None:
        """CalculateTractionFromPressureValues(*args, **kwargs)
        Overloaded function.

        1. CalculateTractionFromPressureValues(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble3D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: bool) -> None

        2. CalculateTractionFromPressureValues(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble3D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: bool) -> None
        """
    @overload
    def CalculateTractionFromPressureValues(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: bool) -> None:
        """CalculateTractionFromPressureValues(*args, **kwargs)
        Overloaded function.

        1. CalculateTractionFromPressureValues(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble3D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: bool) -> None

        2. CalculateTractionFromPressureValues(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble3D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: bool) -> None
        """
    def CheckCurrentCoordinatesFluid(self, arg0: Kratos.ModelPart, arg1: float) -> None:
        """CheckCurrentCoordinatesFluid(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble3D, arg0: Kratos.ModelPart, arg1: float) -> None"""
    def CheckCurrentCoordinatesStructure(self, arg0: Kratos.ModelPart, arg1: float) -> None:
        """CheckCurrentCoordinatesStructure(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble3D, arg0: Kratos.ModelPart, arg1: float) -> None"""
    def ComputeAndPrintFluidInterfaceNorms(self, arg0: Kratos.ModelPart) -> None:
        """ComputeAndPrintFluidInterfaceNorms(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble3D, arg0: Kratos.ModelPart) -> None"""
    def ComputeAndPrintStructureInterfaceNorms(self, arg0: Kratos.ModelPart) -> None:
        """ComputeAndPrintStructureInterfaceNorms(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble3D, arg0: Kratos.ModelPart) -> None"""
    def ComputeInterfaceResidualNorm(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable, arg4: str) -> float:
        """ComputeInterfaceResidualNorm(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble3D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable, arg4: str) -> float"""
    def ComputeInterfaceResidualVector(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable, arg4: Kratos.Vector, arg5: str, arg6: Kratos.DoubleVariable) -> None:
        """ComputeInterfaceResidualVector(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble3D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable, arg4: Kratos.Vector, arg5: str, arg6: Kratos.DoubleVariable) -> None"""
    def CreateCouplingSkin(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """CreateCouplingSkin(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble3D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
    def EmbeddedPressureToPositiveFacePressureInterpolator(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """EmbeddedPressureToPositiveFacePressureInterpolator(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble3D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
    def GetInterfaceArea(self, arg0: Kratos.ModelPart) -> float:
        """GetInterfaceArea(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble3D, arg0: Kratos.ModelPart) -> float"""
    def GetInterfaceResidualSize(self, arg0: Kratos.ModelPart) -> int:
        """GetInterfaceResidualSize(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble3D, arg0: Kratos.ModelPart) -> int"""
    def InitializeInterfaceVector(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Vector) -> None:
        """InitializeInterfaceVector(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble3D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Vector) -> None"""
    def SetUpInterfaceVector(self, arg0: Kratos.ModelPart) -> Kratos.Vector:
        """SetUpInterfaceVector(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble3D, arg0: Kratos.ModelPart) -> Kratos.Vector"""
    def UpdateInterfaceValues(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Vector) -> None:
        """UpdateInterfaceValues(self: KratosFSIApplication.PartitionedFSIUtilitiesDouble3D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Vector) -> None"""

class SharedPointsMapper:
    def __init__(self, arg0: Kratos.NodesArray, arg1: Kratos.NodesArray, arg2: float) -> None:
        """__init__(self: KratosFSIApplication.SharedPointsMapper, arg0: Kratos.NodesArray, arg1: Kratos.NodesArray, arg2: float) -> None"""
    def InverseScalarMap(self, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None:
        """InverseScalarMap(self: KratosFSIApplication.SharedPointsMapper, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None"""
    def InverseVectorMap(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """InverseVectorMap(self: KratosFSIApplication.SharedPointsMapper, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None"""
    def ScalarMap(self, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None:
        """ScalarMap(self: KratosFSIApplication.SharedPointsMapper, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None"""
    def VectorMap(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """VectorMap(self: KratosFSIApplication.SharedPointsMapper, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None"""
