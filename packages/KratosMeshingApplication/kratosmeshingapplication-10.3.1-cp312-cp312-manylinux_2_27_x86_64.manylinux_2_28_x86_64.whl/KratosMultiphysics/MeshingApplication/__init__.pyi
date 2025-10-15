import Kratos
from . import MeshingUtilities as MeshingUtilities
from typing import overload

class BinBasedMeshTransfer2D:
    def __init__(self) -> None:
        """__init__(self: KratosMeshingApplication.BinBasedMeshTransfer2D) -> None"""
    def DirectScalarVarInterpolation(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable, arg4: Kratos.BinBasedFastPointLocator2D) -> None:
        """DirectScalarVarInterpolation(self: KratosMeshingApplication.BinBasedMeshTransfer2D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable, arg4: Kratos.BinBasedFastPointLocator2D) -> None"""
    def DirectVectorialVarInterpolation(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3, arg4: Kratos.BinBasedFastPointLocator2D) -> None:
        """DirectVectorialVarInterpolation(self: KratosMeshingApplication.BinBasedMeshTransfer2D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3, arg4: Kratos.BinBasedFastPointLocator2D) -> None"""
    def MappingFromMovingMesh_ScalarVar(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable, arg4: Kratos.BinBasedFastPointLocator2D) -> None:
        """MappingFromMovingMesh_ScalarVar(self: KratosMeshingApplication.BinBasedMeshTransfer2D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable, arg4: Kratos.BinBasedFastPointLocator2D) -> None"""
    def MappingFromMovingMesh_VariableMeshes_ScalarVar(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable, arg4: Kratos.BinBasedNodesInElementLocator2D) -> None:
        """MappingFromMovingMesh_VariableMeshes_ScalarVar(self: KratosMeshingApplication.BinBasedMeshTransfer2D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable, arg4: Kratos.BinBasedNodesInElementLocator2D) -> None"""
    def MappingFromMovingMesh_VariableMeshes_VectorialVar(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3, arg4: Kratos.BinBasedNodesInElementLocator2D) -> None:
        """MappingFromMovingMesh_VariableMeshes_VectorialVar(self: KratosMeshingApplication.BinBasedMeshTransfer2D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3, arg4: Kratos.BinBasedNodesInElementLocator2D) -> None"""
    def MappingFromMovingMesh_VectorialVar(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3, arg4: Kratos.BinBasedFastPointLocator2D) -> None:
        """MappingFromMovingMesh_VectorialVar(self: KratosMeshingApplication.BinBasedMeshTransfer2D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3, arg4: Kratos.BinBasedFastPointLocator2D) -> None"""

class BinBasedMeshTransfer3D:
    def __init__(self) -> None:
        """__init__(self: KratosMeshingApplication.BinBasedMeshTransfer3D) -> None"""
    def DirectScalarVarInterpolation(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable, arg4: Kratos.BinBasedFastPointLocator3D) -> None:
        """DirectScalarVarInterpolation(self: KratosMeshingApplication.BinBasedMeshTransfer3D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable, arg4: Kratos.BinBasedFastPointLocator3D) -> None"""
    def DirectVectorialVarInterpolation(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3, arg4: Kratos.BinBasedFastPointLocator3D) -> None:
        """DirectVectorialVarInterpolation(self: KratosMeshingApplication.BinBasedMeshTransfer3D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3, arg4: Kratos.BinBasedFastPointLocator3D) -> None"""
    def MappingFromMovingMesh_ScalarVar(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable, arg4: Kratos.BinBasedFastPointLocator3D) -> None:
        """MappingFromMovingMesh_ScalarVar(self: KratosMeshingApplication.BinBasedMeshTransfer3D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable, arg4: Kratos.BinBasedFastPointLocator3D) -> None"""
    def MappingFromMovingMesh_VariableMeshes_ScalarVar(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable, arg4: Kratos.BinBasedNodesInElementLocator3D) -> None:
        """MappingFromMovingMesh_VariableMeshes_ScalarVar(self: KratosMeshingApplication.BinBasedMeshTransfer3D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable, arg4: Kratos.BinBasedNodesInElementLocator3D) -> None"""
    def MappingFromMovingMesh_VariableMeshes_VectorialVar(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3, arg4: Kratos.BinBasedNodesInElementLocator3D) -> None:
        """MappingFromMovingMesh_VariableMeshes_VectorialVar(self: KratosMeshingApplication.BinBasedMeshTransfer3D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3, arg4: Kratos.BinBasedNodesInElementLocator3D) -> None"""
    def MappingFromMovingMesh_VectorialVar(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3, arg4: Kratos.BinBasedFastPointLocator3D) -> None:
        """MappingFromMovingMesh_VectorialVar(self: KratosMeshingApplication.BinBasedMeshTransfer3D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3, arg4: Kratos.BinBasedFastPointLocator3D) -> None"""

class ComputeHessianSolMetricProcess(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

        3. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

        3. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

        3. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None
        """

class ComputeHessianSolMetricProcess2D(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

        3. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

        3. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

        3. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None
        """

class ComputeHessianSolMetricProcess3D(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

        3. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

        3. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

        3. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None
        """

class ComputeHessianSolMetricProcessComp2D(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

        3. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

        3. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

        3. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None
        """

class ComputeHessianSolMetricProcessComp3D(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

        3. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

        3. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

        3. __init__(self: KratosMeshingApplication.ComputeHessianSolMetricProcess, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None
        """

class ComputeLevelSetSolMetricProcess2D(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.ComputeLevelSetSolMetricProcess2D, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None

        2. __init__(self: KratosMeshingApplication.ComputeLevelSetSolMetricProcess2D, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.ComputeLevelSetSolMetricProcess2D, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None

        2. __init__(self: KratosMeshingApplication.ComputeLevelSetSolMetricProcess2D, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Parameters) -> None
        """

class ComputeLevelSetSolMetricProcess3D(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.ComputeLevelSetSolMetricProcess3D, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None

        2. __init__(self: KratosMeshingApplication.ComputeLevelSetSolMetricProcess3D, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.ComputeLevelSetSolMetricProcess3D, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None

        2. __init__(self: KratosMeshingApplication.ComputeLevelSetSolMetricProcess3D, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Parameters) -> None
        """

class Cutting_Isosurface_Application:
    def __init__(self) -> None:
        """__init__(self: KratosMeshingApplication.Cutting_Isosurface_Application) -> None"""
    def AddModelPartElements(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: int) -> None:
        """AddModelPartElements(self: KratosMeshingApplication.Cutting_Isosurface_Application, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: int) -> None"""
    def AddSkinConditions(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: int) -> None:
        """AddSkinConditions(self: KratosMeshingApplication.Cutting_Isosurface_Application, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: int) -> None"""
    def DeleteCutData(self, arg0: Kratos.ModelPart) -> None:
        """DeleteCutData(self: KratosMeshingApplication.Cutting_Isosurface_Application, arg0: Kratos.ModelPart) -> None"""
    def GenerateScalarVarCut(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: float, arg4: int, arg5: float) -> None:
        """GenerateScalarVarCut(self: KratosMeshingApplication.Cutting_Isosurface_Application, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: float, arg4: int, arg5: float) -> None"""
    def GenerateVectorialVarCut(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: float, arg4: int, arg5: float) -> None:
        """GenerateVectorialVarCut(self: KratosMeshingApplication.Cutting_Isosurface_Application, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: float, arg4: int, arg5: float) -> None"""
    def UpdateCutData(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """UpdateCutData(self: KratosMeshingApplication.Cutting_Isosurface_Application, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""

class GradualVariableInterpolationUtility:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def InitializeInterpolationAndConstraints(self, arg0: Kratos.ModelPart, arg1: list[str], arg2: float, arg3: int, arg4: bool) -> None:
        """InitializeInterpolationAndConstraints(self: Kratos.ModelPart, arg0: Kratos.ModelPart, arg1: list[str], arg2: float, arg3: int, arg4: bool) -> None"""
    def UpdateSolutionStepVariables(self, arg0: list[str], arg1: float, arg2: float, arg3: bool) -> None:
        """UpdateSolutionStepVariables(self: Kratos.ModelPart, arg0: list[str], arg1: float, arg2: float, arg3: bool) -> None"""

class InternalVariablesInterpolationProcess(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.InternalVariablesInterpolationProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None

        2. __init__(self: KratosMeshingApplication.InternalVariablesInterpolationProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.InternalVariablesInterpolationProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None

        2. __init__(self: KratosMeshingApplication.InternalVariablesInterpolationProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None
        """

class KratosMeshingApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosMeshingApplication.KratosMeshingApplication) -> None"""

class LinearToQuadraticTetrahedraMeshConverter:
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosMeshingApplication.LinearToQuadraticTetrahedraMeshConverter, arg0: Kratos.ModelPart) -> None"""
    def LocalConvertLinearToQuadraticTetrahedraMesh(self, arg0: bool, arg1: bool) -> None:
        """LocalConvertLinearToQuadraticTetrahedraMesh(self: KratosMeshingApplication.LinearToQuadraticTetrahedraMeshConverter, arg0: bool, arg1: bool) -> None"""

class LocalRefinePrismMesh:
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosMeshingApplication.LocalRefinePrismMesh, arg0: Kratos.ModelPart) -> None"""
    def LocalRefineMesh(self, arg0: bool, arg1: bool) -> None:
        """LocalRefineMesh(self: KratosMeshingApplication.LocalRefinePrismMesh, arg0: bool, arg1: bool) -> None"""

class LocalRefineTetrahedraMesh:
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosMeshingApplication.LocalRefineTetrahedraMesh, arg0: Kratos.ModelPart) -> None"""
    def LocalRefineMesh(self, arg0: bool, arg1: bool) -> None:
        """LocalRefineMesh(self: KratosMeshingApplication.LocalRefineTetrahedraMesh, arg0: bool, arg1: bool) -> None"""

class LocalRefineTetrahedraMeshOnlyOnBoundaries:
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosMeshingApplication.LocalRefineTetrahedraMeshOnlyOnBoundaries, arg0: Kratos.ModelPart) -> None"""
    def LocalRefineMesh(self, arg0: bool, arg1: bool) -> None:
        """LocalRefineMesh(self: KratosMeshingApplication.LocalRefineTetrahedraMeshOnlyOnBoundaries, arg0: bool, arg1: bool) -> None"""

class LocalRefineTetrahedraMeshParallelToBoundaries:
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosMeshingApplication.LocalRefineTetrahedraMeshParallelToBoundaries, arg0: Kratos.ModelPart) -> None"""
    def LocalRefineMesh(self, arg0: bool, arg1: bool) -> None:
        """LocalRefineMesh(self: KratosMeshingApplication.LocalRefineTetrahedraMeshParallelToBoundaries, arg0: bool, arg1: bool) -> None"""

class LocalRefineTriangleMesh:
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosMeshingApplication.LocalRefineTriangleMesh, arg0: Kratos.ModelPart) -> None"""
    def LocalRefineMesh(self, arg0: bool, arg1: bool) -> None:
        """LocalRefineMesh(self: KratosMeshingApplication.LocalRefineTriangleMesh, arg0: bool, arg1: bool) -> None"""

class LocalRefineTriangleMeshConditions:
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosMeshingApplication.LocalRefineTriangleMeshConditions, arg0: Kratos.ModelPart) -> None"""
    def LocalRefineMesh(self, arg0: bool, arg1: bool) -> None:
        """LocalRefineMesh(self: KratosMeshingApplication.LocalRefineTriangleMeshConditions, arg0: bool, arg1: bool) -> None"""

class MeshTransfer2D:
    def __init__(self) -> None:
        """__init__(self: KratosMeshingApplication.MeshTransfer2D) -> None"""
    def DirectModelPartInterpolation(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """DirectModelPartInterpolation(self: KratosMeshingApplication.MeshTransfer2D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
    def DirectScalarVarInterpolation(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable) -> None:
        """DirectScalarVarInterpolation(self: KratosMeshingApplication.MeshTransfer2D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable) -> None"""
    def DirectVectorialVarInterpolation(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None:
        """DirectVectorialVarInterpolation(self: KratosMeshingApplication.MeshTransfer2D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None"""

class MeshTransfer3D:
    def __init__(self) -> None:
        """__init__(self: KratosMeshingApplication.MeshTransfer3D) -> None"""
    def DirectModelPartInterpolation(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """DirectModelPartInterpolation(self: KratosMeshingApplication.MeshTransfer3D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
    def DirectScalarVarInterpolation(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable) -> None:
        """DirectScalarVarInterpolation(self: KratosMeshingApplication.MeshTransfer3D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.DoubleVariable, arg3: Kratos.DoubleVariable) -> None"""
    def DirectVectorialVarInterpolation(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None:
        """DirectVectorialVarInterpolation(self: KratosMeshingApplication.MeshTransfer3D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None"""

class MetricErrorProcess2D(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.MetricErrorProcess2D, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosMeshingApplication.MetricErrorProcess2D, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.MetricErrorProcess2D, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosMeshingApplication.MetricErrorProcess2D, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """

class MetricErrorProcess3D(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.MetricErrorProcess3D, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosMeshingApplication.MetricErrorProcess3D, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.MetricErrorProcess3D, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosMeshingApplication.MetricErrorProcess3D, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """

class MetricFastInit2D(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosMeshingApplication.MetricFastInit2D, arg0: Kratos.ModelPart) -> None"""

class MetricFastInit3D(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosMeshingApplication.MetricFastInit3D, arg0: Kratos.ModelPart) -> None"""

class MmgIO2D(Kratos.IO):
    @overload
    def __init__(self, arg0: str) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.MmgIO2D, arg0: str) -> None

        2. __init__(self: KratosMeshingApplication.MmgIO2D, arg0: str, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosMeshingApplication.MmgIO2D, arg0: str, arg1: Kratos.Parameters, arg2: Kratos.Flags) -> None
        """
    @overload
    def __init__(self, arg0: str, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.MmgIO2D, arg0: str) -> None

        2. __init__(self: KratosMeshingApplication.MmgIO2D, arg0: str, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosMeshingApplication.MmgIO2D, arg0: str, arg1: Kratos.Parameters, arg2: Kratos.Flags) -> None
        """
    @overload
    def __init__(self, arg0: str, arg1: Kratos.Parameters, arg2: Kratos.Flags) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.MmgIO2D, arg0: str) -> None

        2. __init__(self: KratosMeshingApplication.MmgIO2D, arg0: str, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosMeshingApplication.MmgIO2D, arg0: str, arg1: Kratos.Parameters, arg2: Kratos.Flags) -> None
        """
    def GetMmgVersion(self) -> str:
        """GetMmgVersion(self: KratosMeshingApplication.MmgIO2D) -> str"""

class MmgIO3D(Kratos.IO):
    @overload
    def __init__(self, arg0: str) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.MmgIO3D, arg0: str) -> None

        2. __init__(self: KratosMeshingApplication.MmgIO3D, arg0: str, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosMeshingApplication.MmgIO3D, arg0: str, arg1: Kratos.Parameters, arg2: Kratos.Flags) -> None
        """
    @overload
    def __init__(self, arg0: str, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.MmgIO3D, arg0: str) -> None

        2. __init__(self: KratosMeshingApplication.MmgIO3D, arg0: str, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosMeshingApplication.MmgIO3D, arg0: str, arg1: Kratos.Parameters, arg2: Kratos.Flags) -> None
        """
    @overload
    def __init__(self, arg0: str, arg1: Kratos.Parameters, arg2: Kratos.Flags) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.MmgIO3D, arg0: str) -> None

        2. __init__(self: KratosMeshingApplication.MmgIO3D, arg0: str, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosMeshingApplication.MmgIO3D, arg0: str, arg1: Kratos.Parameters, arg2: Kratos.Flags) -> None
        """
    def GetMmgVersion(self) -> str:
        """GetMmgVersion(self: KratosMeshingApplication.MmgIO3D) -> str"""

class MmgIOS(Kratos.IO):
    @overload
    def __init__(self, arg0: str) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.MmgIOS, arg0: str) -> None

        2. __init__(self: KratosMeshingApplication.MmgIOS, arg0: str, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosMeshingApplication.MmgIOS, arg0: str, arg1: Kratos.Parameters, arg2: Kratos.Flags) -> None
        """
    @overload
    def __init__(self, arg0: str, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.MmgIOS, arg0: str) -> None

        2. __init__(self: KratosMeshingApplication.MmgIOS, arg0: str, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosMeshingApplication.MmgIOS, arg0: str, arg1: Kratos.Parameters, arg2: Kratos.Flags) -> None
        """
    @overload
    def __init__(self, arg0: str, arg1: Kratos.Parameters, arg2: Kratos.Flags) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.MmgIOS, arg0: str) -> None

        2. __init__(self: KratosMeshingApplication.MmgIOS, arg0: str, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosMeshingApplication.MmgIOS, arg0: str, arg1: Kratos.Parameters, arg2: Kratos.Flags) -> None
        """
    def GetMmgVersion(self) -> str:
        """GetMmgVersion(self: KratosMeshingApplication.MmgIOS) -> str"""

class MmgProcess2D(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.MmgProcess2D, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosMeshingApplication.MmgProcess2D, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.MmgProcess2D, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosMeshingApplication.MmgProcess2D, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """
    def CleanSuperfluousNodes(self) -> None:
        """CleanSuperfluousNodes(self: KratosMeshingApplication.MmgProcess2D) -> None"""
    def GetMmgVersion(self) -> str:
        """GetMmgVersion(self: KratosMeshingApplication.MmgProcess2D) -> str"""
    def OutputMdpa(self) -> None:
        """OutputMdpa(self: KratosMeshingApplication.MmgProcess2D) -> None"""

class MmgProcess3D(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.MmgProcess3D, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosMeshingApplication.MmgProcess3D, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.MmgProcess3D, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosMeshingApplication.MmgProcess3D, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """
    def CleanSuperfluousNodes(self) -> None:
        """CleanSuperfluousNodes(self: KratosMeshingApplication.MmgProcess3D) -> None"""
    def GetMmgVersion(self) -> str:
        """GetMmgVersion(self: KratosMeshingApplication.MmgProcess3D) -> str"""
    def OutputMdpa(self) -> None:
        """OutputMdpa(self: KratosMeshingApplication.MmgProcess3D) -> None"""

class MmgProcess3DSurfaces(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.MmgProcess3DSurfaces, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosMeshingApplication.MmgProcess3DSurfaces, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.MmgProcess3DSurfaces, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosMeshingApplication.MmgProcess3DSurfaces, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """
    def CleanSuperfluousNodes(self) -> None:
        """CleanSuperfluousNodes(self: KratosMeshingApplication.MmgProcess3DSurfaces) -> None"""
    def GetMmgVersion(self) -> str:
        """GetMmgVersion(self: KratosMeshingApplication.MmgProcess3DSurfaces) -> str"""
    def OutputMdpa(self) -> None:
        """OutputMdpa(self: KratosMeshingApplication.MmgProcess3DSurfaces) -> None"""

class MultiscaleRefiningProcess(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart) -> None

        2. __init__(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart, arg3: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart, arg3: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart) -> None

        2. __init__(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart, arg3: Kratos.Parameters) -> None
        """
    def ExecuteCoarsening(self) -> None:
        """ExecuteCoarsening(self: KratosMeshingApplication.MultiscaleRefiningProcess) -> None"""
    def ExecuteRefinement(self) -> None:
        """ExecuteRefinement(self: KratosMeshingApplication.MultiscaleRefiningProcess) -> None"""
    def FixRefinedInterface(self, arg0: Kratos.DoubleVariable, arg1: bool) -> None:
        """FixRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.DoubleVariable, arg1: bool) -> None"""
    def GetCoarseModelPart(self) -> Kratos.ModelPart:
        """GetCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess) -> Kratos.ModelPart"""
    def GetRefinedModelPart(self) -> Kratos.ModelPart:
        """GetRefinedModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess) -> Kratos.ModelPart"""
    def GetVisualizationModelPart(self) -> Kratos.ModelPart:
        """GetVisualizationModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess) -> Kratos.ModelPart"""
    def InitializeRefinedModelPart(self, arg0: Kratos.ModelPart) -> None:
        """InitializeRefinedModelPart(self: Kratos.ModelPart, arg0: Kratos.ModelPart) -> None"""
    def InitializeVisualizationModelPart(self, arg0: Kratos.ModelPart) -> None:
        """InitializeVisualizationModelPart(self: Kratos.ModelPart, arg0: Kratos.ModelPart) -> None"""
    @overload
    def TransferLastStepToCoarseModelPart(self, arg0: Kratos.DoubleVariable) -> None:
        """TransferLastStepToCoarseModelPart(*args, **kwargs)
        Overloaded function.

        1. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.DoubleVariable) -> None

        2. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable3) -> None

        3. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable4) -> None

        4. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable6) -> None

        5. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable9) -> None
        """
    @overload
    def TransferLastStepToCoarseModelPart(self, arg0: Kratos.Array1DVariable3) -> None:
        """TransferLastStepToCoarseModelPart(*args, **kwargs)
        Overloaded function.

        1. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.DoubleVariable) -> None

        2. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable3) -> None

        3. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable4) -> None

        4. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable6) -> None

        5. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable9) -> None
        """
    @overload
    def TransferLastStepToCoarseModelPart(self, arg0: Kratos.Array1DVariable4) -> None:
        """TransferLastStepToCoarseModelPart(*args, **kwargs)
        Overloaded function.

        1. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.DoubleVariable) -> None

        2. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable3) -> None

        3. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable4) -> None

        4. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable6) -> None

        5. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable9) -> None
        """
    @overload
    def TransferLastStepToCoarseModelPart(self, arg0: Kratos.Array1DVariable6) -> None:
        """TransferLastStepToCoarseModelPart(*args, **kwargs)
        Overloaded function.

        1. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.DoubleVariable) -> None

        2. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable3) -> None

        3. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable4) -> None

        4. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable6) -> None

        5. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable9) -> None
        """
    @overload
    def TransferLastStepToCoarseModelPart(self, arg0: Kratos.Array1DVariable9) -> None:
        """TransferLastStepToCoarseModelPart(*args, **kwargs)
        Overloaded function.

        1. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.DoubleVariable) -> None

        2. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable3) -> None

        3. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable4) -> None

        4. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable6) -> None

        5. TransferLastStepToCoarseModelPart(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable9) -> None
        """
    @overload
    def TransferSubstepToRefinedInterface(self, arg0: Kratos.DoubleVariable, arg1: float) -> None:
        """TransferSubstepToRefinedInterface(*args, **kwargs)
        Overloaded function.

        1. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.DoubleVariable, arg1: float) -> None

        2. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable3, arg1: float) -> None

        3. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable4, arg1: float) -> None

        4. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable6, arg1: float) -> None

        5. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable9, arg1: float) -> None
        """
    @overload
    def TransferSubstepToRefinedInterface(self, arg0: Kratos.Array1DVariable3, arg1: float) -> None:
        """TransferSubstepToRefinedInterface(*args, **kwargs)
        Overloaded function.

        1. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.DoubleVariable, arg1: float) -> None

        2. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable3, arg1: float) -> None

        3. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable4, arg1: float) -> None

        4. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable6, arg1: float) -> None

        5. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable9, arg1: float) -> None
        """
    @overload
    def TransferSubstepToRefinedInterface(self, arg0: Kratos.Array1DVariable4, arg1: float) -> None:
        """TransferSubstepToRefinedInterface(*args, **kwargs)
        Overloaded function.

        1. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.DoubleVariable, arg1: float) -> None

        2. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable3, arg1: float) -> None

        3. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable4, arg1: float) -> None

        4. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable6, arg1: float) -> None

        5. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable9, arg1: float) -> None
        """
    @overload
    def TransferSubstepToRefinedInterface(self, arg0: Kratos.Array1DVariable6, arg1: float) -> None:
        """TransferSubstepToRefinedInterface(*args, **kwargs)
        Overloaded function.

        1. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.DoubleVariable, arg1: float) -> None

        2. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable3, arg1: float) -> None

        3. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable4, arg1: float) -> None

        4. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable6, arg1: float) -> None

        5. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable9, arg1: float) -> None
        """
    @overload
    def TransferSubstepToRefinedInterface(self, arg0: Kratos.Array1DVariable9, arg1: float) -> None:
        """TransferSubstepToRefinedInterface(*args, **kwargs)
        Overloaded function.

        1. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.DoubleVariable, arg1: float) -> None

        2. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable3, arg1: float) -> None

        3. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable4, arg1: float) -> None

        4. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable6, arg1: float) -> None

        5. TransferSubstepToRefinedInterface(self: KratosMeshingApplication.MultiscaleRefiningProcess, arg0: Kratos.Array1DVariable9, arg1: float) -> None
        """

class NodalValuesInterpolationProcess2D(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.NodalValuesInterpolationProcess2D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None

        2. __init__(self: KratosMeshingApplication.NodalValuesInterpolationProcess2D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.NodalValuesInterpolationProcess2D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None

        2. __init__(self: KratosMeshingApplication.NodalValuesInterpolationProcess2D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None
        """
    def Execute(self) -> None:
        """Execute(self: KratosMeshingApplication.NodalValuesInterpolationProcess2D) -> None"""

class NodalValuesInterpolationProcess3D(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.NodalValuesInterpolationProcess3D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None

        2. __init__(self: KratosMeshingApplication.NodalValuesInterpolationProcess3D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMeshingApplication.NodalValuesInterpolationProcess3D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None

        2. __init__(self: KratosMeshingApplication.NodalValuesInterpolationProcess3D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None
        """
    def Execute(self) -> None:
        """Execute(self: KratosMeshingApplication.NodalValuesInterpolationProcess3D) -> None"""

class TriGenDropletModeler:
    def __init__(self) -> None:
        """__init__(self: KratosMeshingApplication.TriGenDropletModeler) -> None"""
    @overload
    def ReGenerateMeshDroplet(self, arg0: str, arg1: str, arg2: Kratos.ModelPart, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None:
        """ReGenerateMeshDroplet(*args, **kwargs)
        Overloaded function.

        1. ReGenerateMeshDroplet(self: KratosMeshingApplication.TriGenDropletModeler, arg0: str, arg1: str, arg2: Kratos.ModelPart, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None

        2. ReGenerateMeshDroplet(self: KratosMeshingApplication.TriGenDropletModeler, arg0: Kratos.ModelPart, arg1: Kratos.Element, arg2: Kratos.Condition, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None
        """
    @overload
    def ReGenerateMeshDroplet(self, arg0: Kratos.ModelPart, arg1: Kratos.Element, arg2: Kratos.Condition, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None:
        """ReGenerateMeshDroplet(*args, **kwargs)
        Overloaded function.

        1. ReGenerateMeshDroplet(self: KratosMeshingApplication.TriGenDropletModeler, arg0: str, arg1: str, arg2: Kratos.ModelPart, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None

        2. ReGenerateMeshDroplet(self: KratosMeshingApplication.TriGenDropletModeler, arg0: Kratos.ModelPart, arg1: Kratos.Element, arg2: Kratos.Condition, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None
        """

class TriGenGLASSModeler:
    def __init__(self) -> None:
        """__init__(self: KratosMeshingApplication.TriGenGLASSModeler) -> None"""
    @overload
    def ReGenerateMeshGlass(self, arg0: str, arg1: str, arg2: Kratos.ModelPart, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None:
        """ReGenerateMeshGlass(*args, **kwargs)
        Overloaded function.

        1. ReGenerateMeshGlass(self: KratosMeshingApplication.TriGenGLASSModeler, arg0: str, arg1: str, arg2: Kratos.ModelPart, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None

        2. ReGenerateMeshGlass(self: KratosMeshingApplication.TriGenGLASSModeler, arg0: Kratos.ModelPart, arg1: Kratos.Element, arg2: Kratos.Condition, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None
        """
    @overload
    def ReGenerateMeshGlass(self, arg0: Kratos.ModelPart, arg1: Kratos.Element, arg2: Kratos.Condition, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None:
        """ReGenerateMeshGlass(*args, **kwargs)
        Overloaded function.

        1. ReGenerateMeshGlass(self: KratosMeshingApplication.TriGenGLASSModeler, arg0: str, arg1: str, arg2: Kratos.ModelPart, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None

        2. ReGenerateMeshGlass(self: KratosMeshingApplication.TriGenGLASSModeler, arg0: Kratos.ModelPart, arg1: Kratos.Element, arg2: Kratos.Condition, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None
        """

class TriGenPFEMModeler:
    def __init__(self) -> None:
        """__init__(self: KratosMeshingApplication.TriGenPFEMModeler) -> None"""
    @overload
    def ReGenerateMesh(self, arg0: str, arg1: str, arg2: Kratos.ModelPart, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None:
        """ReGenerateMesh(*args, **kwargs)
        Overloaded function.

        1. ReGenerateMesh(self: KratosMeshingApplication.TriGenPFEMModeler, arg0: str, arg1: str, arg2: Kratos.ModelPart, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None

        2. ReGenerateMesh(self: KratosMeshingApplication.TriGenPFEMModeler, arg0: Kratos.ModelPart, arg1: Kratos.Element, arg2: Kratos.Condition, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None
        """
    @overload
    def ReGenerateMesh(self, arg0: Kratos.ModelPart, arg1: Kratos.Element, arg2: Kratos.Condition, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None:
        """ReGenerateMesh(*args, **kwargs)
        Overloaded function.

        1. ReGenerateMesh(self: KratosMeshingApplication.TriGenPFEMModeler, arg0: str, arg1: str, arg2: Kratos.ModelPart, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None

        2. ReGenerateMesh(self: KratosMeshingApplication.TriGenPFEMModeler, arg0: Kratos.ModelPart, arg1: Kratos.Element, arg2: Kratos.Condition, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None
        """

class TriGenPFEMModelerVMS:
    def __init__(self) -> None:
        """__init__(self: KratosMeshingApplication.TriGenPFEMModelerVMS) -> None"""
    def ReGenerateMesh(self, arg0: Kratos.ModelPart, arg1: Kratos.Element, arg2: Kratos.Condition, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None:
        """ReGenerateMesh(self: KratosMeshingApplication.TriGenPFEMModelerVMS, arg0: Kratos.ModelPart, arg1: Kratos.Element, arg2: Kratos.Condition, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None"""

class TriGenPFEMSegment:
    def __init__(self) -> None:
        """__init__(self: KratosMeshingApplication.TriGenPFEMSegment) -> None"""
    def ReGenerateMesh(self, arg0: str, arg1: str, arg2: Kratos.ModelPart, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None:
        """ReGenerateMesh(self: KratosMeshingApplication.TriGenPFEMSegment, arg0: str, arg1: str, arg2: Kratos.ModelPart, arg3: Kratos.NodeEraseProcess, arg4: bool, arg5: bool, arg6: float, arg7: float) -> None"""
