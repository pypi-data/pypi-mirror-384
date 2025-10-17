import Kratos
import KratosLinearSolversApplication
from typing import overload

class DampingUtilities:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosShapeOptimizationApplication.DampingUtilities, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""
    def DampNodalVariable(self, arg0: Kratos.Array1DVariable3) -> None:
        """DampNodalVariable(self: KratosShapeOptimizationApplication.DampingUtilities, arg0: Kratos.Array1DVariable3) -> None"""

class DirectionDampingUtilities:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosShapeOptimizationApplication.DirectionDampingUtilities, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""
    def DampNodalVariable(self, arg0: Kratos.Array1DVariable3) -> None:
        """DampNodalVariable(self: KratosShapeOptimizationApplication.DirectionDampingUtilities, arg0: Kratos.Array1DVariable3) -> None"""

class FaceAngleResponseFunctionUtility:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosShapeOptimizationApplication.FaceAngleResponseFunctionUtility, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""
    def CalculateGradient(self) -> None:
        """CalculateGradient(self: KratosShapeOptimizationApplication.FaceAngleResponseFunctionUtility) -> None"""
    def CalculateValue(self) -> float:
        """CalculateValue(self: KratosShapeOptimizationApplication.FaceAngleResponseFunctionUtility) -> float"""
    def Initialize(self) -> None:
        """Initialize(self: KratosShapeOptimizationApplication.FaceAngleResponseFunctionUtility) -> None"""

class GeometryUtilities:
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosShapeOptimizationApplication.GeometryUtilities, arg0: Kratos.ModelPart) -> None"""
    @overload
    def CalculateLength(self, arg0: Kratos.ElementsArray) -> float:
        """CalculateLength(*args, **kwargs)
        Overloaded function.

        1. CalculateLength(self: KratosShapeOptimizationApplication.GeometryUtilities, arg0: Kratos.ElementsArray) -> float

        2. CalculateLength(self: KratosShapeOptimizationApplication.GeometryUtilities, arg0: Kratos.ConditionsArray) -> float
        """
    @overload
    def CalculateLength(self, arg0: Kratos.ConditionsArray) -> float:
        """CalculateLength(*args, **kwargs)
        Overloaded function.

        1. CalculateLength(self: KratosShapeOptimizationApplication.GeometryUtilities, arg0: Kratos.ElementsArray) -> float

        2. CalculateLength(self: KratosShapeOptimizationApplication.GeometryUtilities, arg0: Kratos.ConditionsArray) -> float
        """
    def CalculateNodalAreasFromConditions(self) -> None:
        """CalculateNodalAreasFromConditions(self: KratosShapeOptimizationApplication.GeometryUtilities) -> None"""
    def ComputeDistancesToBoundingModelPart(self, arg0: Kratos.ModelPart) -> tuple[list[float], list[float]]:
        """ComputeDistancesToBoundingModelPart(self: KratosShapeOptimizationApplication.GeometryUtilities, arg0: Kratos.ModelPart) -> tuple[list[float], list[float]]"""
    def ComputeUnitSurfaceNormals(self) -> None:
        """ComputeUnitSurfaceNormals(self: KratosShapeOptimizationApplication.GeometryUtilities) -> None"""
    def ComputeVolume(self) -> float:
        """ComputeVolume(self: KratosShapeOptimizationApplication.GeometryUtilities) -> float"""
    def ComputeVolumeShapeDerivatives(self, arg0: Kratos.Array1DVariable3) -> None:
        """ComputeVolumeShapeDerivatives(self: KratosShapeOptimizationApplication.GeometryUtilities, arg0: Kratos.Array1DVariable3) -> None"""
    def ExtractBoundaryNodes(self, arg0: str) -> None:
        """ExtractBoundaryNodes(self: KratosShapeOptimizationApplication.GeometryUtilities, arg0: str) -> None"""
    def ExtractEdgeNodes(self, arg0: str) -> None:
        """ExtractEdgeNodes(self: KratosShapeOptimizationApplication.GeometryUtilities, arg0: str) -> None"""
    def ProjectNodalVariableOnDirection(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """ProjectNodalVariableOnDirection(self: KratosShapeOptimizationApplication.GeometryUtilities, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None"""
    def ProjectNodalVariableOnTangentPlane(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """ProjectNodalVariableOnTangentPlane(self: KratosShapeOptimizationApplication.GeometryUtilities, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None"""
    def ProjectNodalVariableOnUnitSurfaceNormals(self, arg0: Kratos.Array1DVariable3) -> None:
        """ProjectNodalVariableOnUnitSurfaceNormals(self: KratosShapeOptimizationApplication.GeometryUtilities, arg0: Kratos.Array1DVariable3) -> None"""

class KratosShapeOptimizationApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosShapeOptimizationApplication.KratosShapeOptimizationApplication) -> None"""

class MapperVertexMorphing:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosShapeOptimizationApplication.MapperVertexMorphing, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None"""
    def Initialize(self) -> None:
        """Initialize(self: KratosShapeOptimizationApplication.MapperVertexMorphing) -> None"""
    @overload
    def InverseMap(self, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None:
        """InverseMap(*args, **kwargs)
        Overloaded function.

        1. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphing, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphing, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def InverseMap(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """InverseMap(*args, **kwargs)
        Overloaded function.

        1. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphing, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphing, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def Map(self, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None:
        """Map(*args, **kwargs)
        Overloaded function.

        1. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphing, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphing, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def Map(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """Map(*args, **kwargs)
        Overloaded function.

        1. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphing, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphing, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    def Update(self) -> None:
        """Update(self: KratosShapeOptimizationApplication.MapperVertexMorphing) -> None"""

class MapperVertexMorphingAdaptiveRadius:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosShapeOptimizationApplication.MapperVertexMorphingAdaptiveRadius, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None"""
    def Initialize(self) -> None:
        """Initialize(self: KratosShapeOptimizationApplication.MapperVertexMorphingAdaptiveRadius) -> None"""
    @overload
    def InverseMap(self, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None:
        """InverseMap(*args, **kwargs)
        Overloaded function.

        1. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingAdaptiveRadius, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingAdaptiveRadius, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def InverseMap(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """InverseMap(*args, **kwargs)
        Overloaded function.

        1. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingAdaptiveRadius, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingAdaptiveRadius, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def Map(self, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None:
        """Map(*args, **kwargs)
        Overloaded function.

        1. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingAdaptiveRadius, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingAdaptiveRadius, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def Map(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """Map(*args, **kwargs)
        Overloaded function.

        1. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingAdaptiveRadius, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingAdaptiveRadius, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    def Update(self) -> None:
        """Update(self: KratosShapeOptimizationApplication.MapperVertexMorphingAdaptiveRadius) -> None"""

class MapperVertexMorphingImprovedIntegration:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegration, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None"""
    def Initialize(self) -> None:
        """Initialize(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegration) -> None"""
    @overload
    def InverseMap(self, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None:
        """InverseMap(*args, **kwargs)
        Overloaded function.

        1. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegration, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegration, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def InverseMap(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """InverseMap(*args, **kwargs)
        Overloaded function.

        1. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegration, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegration, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def Map(self, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None:
        """Map(*args, **kwargs)
        Overloaded function.

        1. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegration, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegration, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def Map(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """Map(*args, **kwargs)
        Overloaded function.

        1. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegration, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegration, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    def Update(self) -> None:
        """Update(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegration) -> None"""

class MapperVertexMorphingImprovedIntegrationAdaptiveRadius:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegrationAdaptiveRadius, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None"""
    def Initialize(self) -> None:
        """Initialize(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegrationAdaptiveRadius) -> None"""
    @overload
    def InverseMap(self, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None:
        """InverseMap(*args, **kwargs)
        Overloaded function.

        1. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegrationAdaptiveRadius, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegrationAdaptiveRadius, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def InverseMap(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """InverseMap(*args, **kwargs)
        Overloaded function.

        1. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegrationAdaptiveRadius, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegrationAdaptiveRadius, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def Map(self, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None:
        """Map(*args, **kwargs)
        Overloaded function.

        1. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegrationAdaptiveRadius, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegrationAdaptiveRadius, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def Map(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """Map(*args, **kwargs)
        Overloaded function.

        1. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegrationAdaptiveRadius, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegrationAdaptiveRadius, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    def Update(self) -> None:
        """Update(self: KratosShapeOptimizationApplication.MapperVertexMorphingImprovedIntegrationAdaptiveRadius) -> None"""

class MapperVertexMorphingMatrixFree:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFree, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None"""
    def Initialize(self) -> None:
        """Initialize(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFree) -> None"""
    @overload
    def InverseMap(self, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None:
        """InverseMap(*args, **kwargs)
        Overloaded function.

        1. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFree, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFree, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def InverseMap(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """InverseMap(*args, **kwargs)
        Overloaded function.

        1. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFree, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFree, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def Map(self, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None:
        """Map(*args, **kwargs)
        Overloaded function.

        1. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFree, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFree, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def Map(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """Map(*args, **kwargs)
        Overloaded function.

        1. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFree, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFree, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    def Update(self) -> None:
        """Update(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFree) -> None"""

class MapperVertexMorphingMatrixFreeAdaptiveRadius:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFreeAdaptiveRadius, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None"""
    def Initialize(self) -> None:
        """Initialize(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFreeAdaptiveRadius) -> None"""
    @overload
    def InverseMap(self, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None:
        """InverseMap(*args, **kwargs)
        Overloaded function.

        1. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFreeAdaptiveRadius, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFreeAdaptiveRadius, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def InverseMap(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """InverseMap(*args, **kwargs)
        Overloaded function.

        1. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFreeAdaptiveRadius, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFreeAdaptiveRadius, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def Map(self, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None:
        """Map(*args, **kwargs)
        Overloaded function.

        1. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFreeAdaptiveRadius, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFreeAdaptiveRadius, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def Map(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """Map(*args, **kwargs)
        Overloaded function.

        1. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFreeAdaptiveRadius, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFreeAdaptiveRadius, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    def Update(self) -> None:
        """Update(self: KratosShapeOptimizationApplication.MapperVertexMorphingMatrixFreeAdaptiveRadius) -> None"""

class MapperVertexMorphingSymmetric:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetric, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None"""
    def Initialize(self) -> None:
        """Initialize(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetric) -> None"""
    @overload
    def InverseMap(self, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None:
        """InverseMap(*args, **kwargs)
        Overloaded function.

        1. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetric, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetric, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def InverseMap(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """InverseMap(*args, **kwargs)
        Overloaded function.

        1. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetric, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetric, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def Map(self, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None:
        """Map(*args, **kwargs)
        Overloaded function.

        1. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetric, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetric, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def Map(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """Map(*args, **kwargs)
        Overloaded function.

        1. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetric, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetric, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    def Update(self) -> None:
        """Update(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetric) -> None"""

class MapperVertexMorphingSymmetricAdaptiveRadius:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetricAdaptiveRadius, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None"""
    def Initialize(self) -> None:
        """Initialize(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetricAdaptiveRadius) -> None"""
    @overload
    def InverseMap(self, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None:
        """InverseMap(*args, **kwargs)
        Overloaded function.

        1. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetricAdaptiveRadius, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetricAdaptiveRadius, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def InverseMap(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """InverseMap(*args, **kwargs)
        Overloaded function.

        1. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetricAdaptiveRadius, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. InverseMap(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetricAdaptiveRadius, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def Map(self, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None:
        """Map(*args, **kwargs)
        Overloaded function.

        1. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetricAdaptiveRadius, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetricAdaptiveRadius, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def Map(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """Map(*args, **kwargs)
        Overloaded function.

        1. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetricAdaptiveRadius, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable) -> None

        2. Map(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetricAdaptiveRadius, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None
        """
    def Update(self) -> None:
        """Update(self: KratosShapeOptimizationApplication.MapperVertexMorphingSymmetricAdaptiveRadius) -> None"""

class MeshControllerUtilities:
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosShapeOptimizationApplication.MeshControllerUtilities, arg0: Kratos.ModelPart) -> None"""
    def AddFirstVariableToSecondVariable(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """AddFirstVariableToSecondVariable(self: KratosShapeOptimizationApplication.MeshControllerUtilities, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None"""
    def LogMeshChangeAccordingInputVariable(self, arg0: Kratos.Array1DVariable3) -> None:
        """LogMeshChangeAccordingInputVariable(self: KratosShapeOptimizationApplication.MeshControllerUtilities, arg0: Kratos.Array1DVariable3) -> None"""
    def RevertMeshUpdateAccordingInputVariable(self, arg0: Kratos.Array1DVariable3) -> None:
        """RevertMeshUpdateAccordingInputVariable(self: KratosShapeOptimizationApplication.MeshControllerUtilities, arg0: Kratos.Array1DVariable3) -> None"""
    def SetDeformationVariablesToZero(self) -> None:
        """SetDeformationVariablesToZero(self: KratosShapeOptimizationApplication.MeshControllerUtilities) -> None"""
    def SetMeshToReferenceMesh(self) -> None:
        """SetMeshToReferenceMesh(self: KratosShapeOptimizationApplication.MeshControllerUtilities) -> None"""
    def SetReferenceMeshToMesh(self) -> None:
        """SetReferenceMeshToMesh(self: KratosShapeOptimizationApplication.MeshControllerUtilities) -> None"""
    def SubtractCoordinatesFromVariable(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None:
        """SubtractCoordinatesFromVariable(self: KratosShapeOptimizationApplication.MeshControllerUtilities, arg0: Kratos.Array1DVariable3, arg1: Kratos.Array1DVariable3) -> None"""
    def UpdateMeshAccordingInputVariable(self, arg0: Kratos.Array1DVariable3) -> None:
        """UpdateMeshAccordingInputVariable(self: KratosShapeOptimizationApplication.MeshControllerUtilities, arg0: Kratos.Array1DVariable3) -> None"""
    def WriteCoordinatesToVariable(self, arg0: Kratos.Array1DVariable3) -> None:
        """WriteCoordinatesToVariable(self: KratosShapeOptimizationApplication.MeshControllerUtilities, arg0: Kratos.Array1DVariable3) -> None"""

class OptimizationUtilities:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    @staticmethod
    def AddFirstVariableToSecondVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None:
        """AddFirstVariableToSecondVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3) -> None"""
    @staticmethod
    def AssembleBufferMatrix(arg0: Kratos.Matrix, arg1: list[float]) -> None:
        """AssembleBufferMatrix(arg0: Kratos.Matrix, arg1: list[float]) -> None"""
    @staticmethod
    def AssembleMatrix(arg0: Kratos.ModelPart, arg1: Kratos.Matrix, arg2: list) -> None:
        """AssembleMatrix(arg0: Kratos.ModelPart, arg1: Kratos.Matrix, arg2: list) -> None"""
    @overload
    @staticmethod
    def AssembleVector(arg0: Kratos.ModelPart, arg1: Kratos.Vector, arg2: Kratos.DoubleVariable) -> None:
        """AssembleVector(*args, **kwargs)
        Overloaded function.

        1. AssembleVector(arg0: Kratos.ModelPart, arg1: Kratos.Vector, arg2: Kratos.DoubleVariable) -> None

        2. AssembleVector(arg0: Kratos.ModelPart, arg1: Kratos.Vector, arg2: Kratos.Array1DVariable3) -> None
        """
    @overload
    @staticmethod
    def AssembleVector(arg0: Kratos.ModelPart, arg1: Kratos.Vector, arg2: Kratos.Array1DVariable3) -> None:
        """AssembleVector(*args, **kwargs)
        Overloaded function.

        1. AssembleVector(arg0: Kratos.ModelPart, arg1: Kratos.Vector, arg2: Kratos.DoubleVariable) -> None

        2. AssembleVector(arg0: Kratos.ModelPart, arg1: Kratos.Vector, arg2: Kratos.Array1DVariable3) -> None
        """
    @overload
    @staticmethod
    def AssignVectorToVariable(arg0: Kratos.ModelPart, arg1: Kratos.Vector, arg2: Kratos.DoubleVariable) -> None:
        """AssignVectorToVariable(*args, **kwargs)
        Overloaded function.

        1. AssignVectorToVariable(arg0: Kratos.ModelPart, arg1: Kratos.Vector, arg2: Kratos.DoubleVariable) -> None

        2. AssignVectorToVariable(arg0: Kratos.ModelPart, arg1: Kratos.Vector, arg2: Kratos.Array1DVariable3) -> None
        """
    @overload
    @staticmethod
    def AssignVectorToVariable(arg0: Kratos.ModelPart, arg1: Kratos.Vector, arg2: Kratos.Array1DVariable3) -> None:
        """AssignVectorToVariable(*args, **kwargs)
        Overloaded function.

        1. AssignVectorToVariable(arg0: Kratos.ModelPart, arg1: Kratos.Vector, arg2: Kratos.DoubleVariable) -> None

        2. AssignVectorToVariable(arg0: Kratos.ModelPart, arg1: Kratos.Vector, arg2: Kratos.Array1DVariable3) -> None
        """
    @staticmethod
    def CalculateProjectedSearchDirectionAndCorrection(arg0: Kratos.Vector, arg1: Kratos.Matrix, arg2: Kratos.Vector, arg3: KratosLinearSolversApplication.DenseLinearSolver, arg4: Kratos.Vector, arg5: Kratos.Vector) -> None:
        """CalculateProjectedSearchDirectionAndCorrection(arg0: Kratos.Vector, arg1: Kratos.Matrix, arg2: Kratos.Vector, arg3: KratosLinearSolversApplication.DenseLinearSolver, arg4: Kratos.Vector, arg5: Kratos.Vector) -> None"""
    @staticmethod
    def CalculateRelaxedProjectedSearchDirectionAndCorrection(arg0: Kratos.Vector, arg1: Kratos.Matrix, arg2: Kratos.Matrix, arg3: Kratos.Vector, arg4: KratosLinearSolversApplication.DenseLinearSolver, arg5: Kratos.Vector, arg6: Kratos.Vector) -> None:
        """CalculateRelaxedProjectedSearchDirectionAndCorrection(arg0: Kratos.Vector, arg1: Kratos.Matrix, arg2: Kratos.Matrix, arg3: Kratos.Vector, arg4: KratosLinearSolversApplication.DenseLinearSolver, arg5: Kratos.Vector, arg6: Kratos.Vector) -> None"""
    @staticmethod
    def ComputeControlPointUpdate(arg0: Kratos.ModelPart, arg1: float, arg2: bool) -> None:
        """ComputeControlPointUpdate(arg0: Kratos.ModelPart, arg1: float, arg2: bool) -> None"""
    @overload
    @staticmethod
    def ComputeL2NormOfNodalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float:
        """ComputeL2NormOfNodalVariable(*args, **kwargs)
        Overloaded function.

        1. ComputeL2NormOfNodalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float

        2. ComputeL2NormOfNodalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> float
        """
    @overload
    @staticmethod
    def ComputeL2NormOfNodalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> float:
        """ComputeL2NormOfNodalVariable(*args, **kwargs)
        Overloaded function.

        1. ComputeL2NormOfNodalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float

        2. ComputeL2NormOfNodalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> float
        """
    @overload
    @staticmethod
    def ComputeMaxNormOfNodalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float:
        """ComputeMaxNormOfNodalVariable(*args, **kwargs)
        Overloaded function.

        1. ComputeMaxNormOfNodalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float

        2. ComputeMaxNormOfNodalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> float
        """
    @overload
    @staticmethod
    def ComputeMaxNormOfNodalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> float:
        """ComputeMaxNormOfNodalVariable(*args, **kwargs)
        Overloaded function.

        1. ComputeMaxNormOfNodalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float

        2. ComputeMaxNormOfNodalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> float
        """
    @staticmethod
    def ComputeProjectedSearchDirection(arg0: Kratos.ModelPart) -> None:
        """ComputeProjectedSearchDirection(arg0: Kratos.ModelPart) -> None"""
    @staticmethod
    def ComputeSearchDirectionSteepestDescent(arg0: Kratos.ModelPart) -> None:
        """ComputeSearchDirectionSteepestDescent(arg0: Kratos.ModelPart) -> None"""
    @staticmethod
    def CorrectProjectedSearchDirection(arg0: Kratos.ModelPart, arg1: float, arg2: float, arg3: float, arg4: bool) -> float:
        """CorrectProjectedSearchDirection(arg0: Kratos.ModelPart, arg1: float, arg2: float, arg3: float, arg4: bool) -> float"""

class SearchBasedFunctions:
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosShapeOptimizationApplication.SearchBasedFunctions, arg0: Kratos.ModelPart) -> None"""
    def FlagNodesInRadius(self, arg0: Kratos.NodesArray, arg1: Kratos.Flags, arg2: float) -> None:
        """FlagNodesInRadius(self: KratosShapeOptimizationApplication.SearchBasedFunctions, arg0: Kratos.NodesArray, arg1: Kratos.Flags, arg2: float) -> None"""

class UniversalFileIO:
    def __init__(self, arg0: Kratos.ModelPart, arg1: str, arg2: str, arg3: Kratos.Parameters) -> None:
        """__init__(self: KratosShapeOptimizationApplication.UniversalFileIO, arg0: Kratos.ModelPart, arg1: str, arg2: str, arg3: Kratos.Parameters) -> None"""
    def InitializeLogging(self) -> None:
        """InitializeLogging(self: KratosShapeOptimizationApplication.UniversalFileIO) -> None"""
    def LogNodalResults(self, arg0: int) -> None:
        """LogNodalResults(self: KratosShapeOptimizationApplication.UniversalFileIO, arg0: int) -> None"""
