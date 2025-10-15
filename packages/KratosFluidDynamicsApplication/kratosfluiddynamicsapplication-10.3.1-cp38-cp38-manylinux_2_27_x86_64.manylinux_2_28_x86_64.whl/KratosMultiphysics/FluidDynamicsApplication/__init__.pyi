import Kratos
from typing import ClassVar, overload

class AccelerationLimitationUtilities:
    def __init__(self, arg0: Kratos.ModelPart, arg1: float) -> None:
        """__init__(self: KratosFluidDynamicsApplication.AccelerationLimitationUtilities, arg0: Kratos.ModelPart, arg1: float) -> None"""
    def Execute(self) -> None:
        """Execute(self: KratosFluidDynamicsApplication.AccelerationLimitationUtilities) -> None"""
    def SetLimitAsMultipleOfGravitionalAcceleration(self, arg0: float) -> None:
        """SetLimitAsMultipleOfGravitionalAcceleration(self: KratosFluidDynamicsApplication.AccelerationLimitationUtilities, arg0: float) -> None"""

class ApplyCompressibleNavierStokesBoundaryConditionsProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosFluidDynamicsApplication.ApplyCompressibleNavierStokesBoundaryConditionsProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class BDF2TurbulentScheme(Kratos.Scheme):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.BDF2TurbulentScheme) -> None

        2. __init__(self: KratosFluidDynamicsApplication.BDF2TurbulentScheme, arg0: Kratos.Process) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Process) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.BDF2TurbulentScheme) -> None

        2. __init__(self: KratosFluidDynamicsApplication.BDF2TurbulentScheme, arg0: Kratos.Process) -> None
        """

class BaseSettingsType:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class Bingham2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosFluidDynamicsApplication.Bingham2DLaw) -> None"""

class Bingham3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosFluidDynamicsApplication.Bingham3DLaw) -> None"""

class BoussinesqForceProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosFluidDynamicsApplication.BoussinesqForceProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class CalculateLevelsetConsistentNodalGradientProcess(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.CalculateLevelsetConsistentNodalGradientProcess, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosFluidDynamicsApplication.CalculateLevelsetConsistentNodalGradientProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.CalculateLevelsetConsistentNodalGradientProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.CalculateLevelsetConsistentNodalGradientProcess, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosFluidDynamicsApplication.CalculateLevelsetConsistentNodalGradientProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.CalculateLevelsetConsistentNodalGradientProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.CalculateLevelsetConsistentNodalGradientProcess, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosFluidDynamicsApplication.CalculateLevelsetConsistentNodalGradientProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.CalculateLevelsetConsistentNodalGradientProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None
        """

class CompressibleElementRotationUtility(Kratos.CoordinateTransformationUtils):
    def __init__(self, arg0: int, arg1: Kratos.Flags) -> None:
        """__init__(self: KratosFluidDynamicsApplication.CompressibleElementRotationUtility, arg0: int, arg1: Kratos.Flags) -> None"""

class CompressibleNavierStokesExplicitSolvingStrategyBFECC(Kratos.ExplicitSolvingStrategyBFECC):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: bool, arg2: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyBFECC, arg0: Kratos.ModelPart, arg1: bool, arg2: int) -> None

        2. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyBFECC, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyBFECC, arg0: Kratos.ModelPart, arg1: Kratos.ExplicitBuilder, arg2: bool, arg3: int) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyBFECC, arg0: Kratos.ModelPart, arg1: bool, arg2: int) -> None

        2. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyBFECC, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyBFECC, arg0: Kratos.ModelPart, arg1: Kratos.ExplicitBuilder, arg2: bool, arg3: int) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ExplicitBuilder, arg2: bool, arg3: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyBFECC, arg0: Kratos.ModelPart, arg1: bool, arg2: int) -> None

        2. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyBFECC, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyBFECC, arg0: Kratos.ModelPart, arg1: Kratos.ExplicitBuilder, arg2: bool, arg3: int) -> None
        """

class CompressibleNavierStokesExplicitSolvingStrategyForwardEuler(Kratos.ExplicitSolvingStrategyRungeKutta1):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: bool, arg2: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyForwardEuler, arg0: Kratos.ModelPart, arg1: bool, arg2: int) -> None

        2. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyForwardEuler, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyForwardEuler, arg0: Kratos.ModelPart, arg1: Kratos.ExplicitBuilder, arg2: bool, arg3: int) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyForwardEuler, arg0: Kratos.ModelPart, arg1: bool, arg2: int) -> None

        2. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyForwardEuler, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyForwardEuler, arg0: Kratos.ModelPart, arg1: Kratos.ExplicitBuilder, arg2: bool, arg3: int) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ExplicitBuilder, arg2: bool, arg3: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyForwardEuler, arg0: Kratos.ModelPart, arg1: bool, arg2: int) -> None

        2. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyForwardEuler, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyForwardEuler, arg0: Kratos.ModelPart, arg1: Kratos.ExplicitBuilder, arg2: bool, arg3: int) -> None
        """

class CompressibleNavierStokesExplicitSolvingStrategyRungeKutta3TVD(Kratos.ExplicitSolvingStrategyRungeKutta3TVD):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: bool, arg2: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyRungeKutta3TVD, arg0: Kratos.ModelPart, arg1: bool, arg2: int) -> None

        2. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyRungeKutta3TVD, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyRungeKutta3TVD, arg0: Kratos.ModelPart, arg1: Kratos.ExplicitBuilder, arg2: bool, arg3: int) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyRungeKutta3TVD, arg0: Kratos.ModelPart, arg1: bool, arg2: int) -> None

        2. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyRungeKutta3TVD, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyRungeKutta3TVD, arg0: Kratos.ModelPart, arg1: Kratos.ExplicitBuilder, arg2: bool, arg3: int) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ExplicitBuilder, arg2: bool, arg3: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyRungeKutta3TVD, arg0: Kratos.ModelPart, arg1: bool, arg2: int) -> None

        2. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyRungeKutta3TVD, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyRungeKutta3TVD, arg0: Kratos.ModelPart, arg1: Kratos.ExplicitBuilder, arg2: bool, arg3: int) -> None
        """

class CompressibleNavierStokesExplicitSolvingStrategyRungeKutta4(Kratos.ExplicitSolvingStrategyRungeKutta4):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: bool, arg2: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyRungeKutta4, arg0: Kratos.ModelPart, arg1: bool, arg2: int) -> None

        2. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyRungeKutta4, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyRungeKutta4, arg0: Kratos.ModelPart, arg1: Kratos.ExplicitBuilder, arg2: bool, arg3: int) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyRungeKutta4, arg0: Kratos.ModelPart, arg1: bool, arg2: int) -> None

        2. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyRungeKutta4, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyRungeKutta4, arg0: Kratos.ModelPart, arg1: Kratos.ExplicitBuilder, arg2: bool, arg3: int) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ExplicitBuilder, arg2: bool, arg3: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyRungeKutta4, arg0: Kratos.ModelPart, arg1: bool, arg2: int) -> None

        2. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyRungeKutta4, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.CompressibleNavierStokesExplicitSolvingStrategyRungeKutta4, arg0: Kratos.ModelPart, arg1: Kratos.ExplicitBuilder, arg2: bool, arg3: int) -> None
        """

class ComputePressureCoefficientProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosFluidDynamicsApplication.ComputePressureCoefficientProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class ComputeYPlusProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosFluidDynamicsApplication.ComputeYPlusProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class DistanceModificationProcess(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: float, arg2: float, arg3: bool, arg4: bool, arg5: bool) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.DistanceModificationProcess, arg0: Kratos.ModelPart, arg1: float, arg2: float, arg3: bool, arg4: bool, arg5: bool) -> None

        2. __init__(self: KratosFluidDynamicsApplication.DistanceModificationProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.DistanceModificationProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.DistanceModificationProcess, arg0: Kratos.ModelPart, arg1: float, arg2: float, arg3: bool, arg4: bool, arg5: bool) -> None

        2. __init__(self: KratosFluidDynamicsApplication.DistanceModificationProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.DistanceModificationProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.DistanceModificationProcess, arg0: Kratos.ModelPart, arg1: float, arg2: float, arg3: bool, arg4: bool, arg5: bool) -> None

        2. __init__(self: KratosFluidDynamicsApplication.DistanceModificationProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.DistanceModificationProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None
        """

class DistanceSmoothingProcess2D(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.DistanceSmoothingProcess2D, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver) -> None

        2. __init__(self: KratosFluidDynamicsApplication.DistanceSmoothingProcess2D, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.DistanceSmoothingProcess2D, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.DistanceSmoothingProcess2D, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver) -> None

        2. __init__(self: KratosFluidDynamicsApplication.DistanceSmoothingProcess2D, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.DistanceSmoothingProcess2D, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.DistanceSmoothingProcess2D, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver) -> None

        2. __init__(self: KratosFluidDynamicsApplication.DistanceSmoothingProcess2D, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.DistanceSmoothingProcess2D, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None
        """

class DistanceSmoothingProcess3D(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.DistanceSmoothingProcess3D, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver) -> None

        2. __init__(self: KratosFluidDynamicsApplication.DistanceSmoothingProcess3D, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.DistanceSmoothingProcess3D, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.DistanceSmoothingProcess3D, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver) -> None

        2. __init__(self: KratosFluidDynamicsApplication.DistanceSmoothingProcess3D, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.DistanceSmoothingProcess3D, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.DistanceSmoothingProcess3D, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver) -> None

        2. __init__(self: KratosFluidDynamicsApplication.DistanceSmoothingProcess3D, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.DistanceSmoothingProcess3D, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None
        """

class DragResponseFunction2D(Kratos.AdjointResponseFunction):
    def __init__(self, arg0: Kratos.Parameters, arg1: Kratos.ModelPart) -> None:
        """__init__(self: KratosFluidDynamicsApplication.DragResponseFunction2D, arg0: Kratos.Parameters, arg1: Kratos.ModelPart) -> None"""

class DragResponseFunction3D(Kratos.AdjointResponseFunction):
    def __init__(self, arg0: Kratos.Parameters, arg1: Kratos.ModelPart) -> None:
        """__init__(self: KratosFluidDynamicsApplication.DragResponseFunction3D, arg0: Kratos.Parameters, arg1: Kratos.ModelPart) -> None"""

class DragUtilities:
    def __init__(self) -> None:
        """__init__(self: KratosFluidDynamicsApplication.DragUtilities) -> None"""
    def CalculateBodyFittedDrag(self, arg0: Kratos.ModelPart) -> Kratos.Array3:
        """CalculateBodyFittedDrag(self: KratosFluidDynamicsApplication.DragUtilities, arg0: Kratos.ModelPart) -> Kratos.Array3"""
    def CalculateEmbeddedDrag(self, arg0: Kratos.ModelPart) -> Kratos.Array3:
        """CalculateEmbeddedDrag(self: KratosFluidDynamicsApplication.DragUtilities, arg0: Kratos.ModelPart) -> Kratos.Array3"""

class DynamicSmagorinskyUtils:
    def __init__(self, arg0: Kratos.ModelPart, arg1: int) -> None:
        """__init__(self: KratosFluidDynamicsApplication.DynamicSmagorinskyUtils, arg0: Kratos.ModelPart, arg1: int) -> None"""
    def CalculateC(self) -> None:
        """CalculateC(self: KratosFluidDynamicsApplication.DynamicSmagorinskyUtils) -> None"""
    def CorrectFlagValues(self, arg0: Kratos.DoubleVariable) -> None:
        """CorrectFlagValues(self: KratosFluidDynamicsApplication.DynamicSmagorinskyUtils, arg0: Kratos.DoubleVariable) -> None"""
    def StoreCoarseMesh(self) -> None:
        """StoreCoarseMesh(self: KratosFluidDynamicsApplication.DynamicSmagorinskyUtils) -> None"""

class EmbeddedNodesInitializationProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: int) -> None:
        """__init__(self: KratosFluidDynamicsApplication.EmbeddedNodesInitializationProcess, arg0: Kratos.ModelPart, arg1: int) -> None"""

class EmbeddedPostprocessProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosFluidDynamicsApplication.EmbeddedPostprocessProcess, arg0: Kratos.ModelPart) -> None"""

class EmbeddedSkinVisualizationProcess(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: list[Kratos.DoubleVariable], arg3: list[Kratos.Array1DVariable3], arg4: list[Kratos.DoubleVariable], arg5: list[Kratos.Array1DVariable3], arg6, arg7, arg8: bool) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.EmbeddedSkinVisualizationProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: list[Kratos.DoubleVariable], arg3: list[Kratos.Array1DVariable3], arg4: list[Kratos.DoubleVariable], arg5: list[Kratos.Array1DVariable3], arg6: Kratos::EmbeddedSkinVisualizationProcess::LevelSetType, arg7: Kratos::EmbeddedSkinVisualizationProcess::ShapeFunctionsType, arg8: bool) -> None

        2. __init__(self: KratosFluidDynamicsApplication.EmbeddedSkinVisualizationProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.EmbeddedSkinVisualizationProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.EmbeddedSkinVisualizationProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: list[Kratos.DoubleVariable], arg3: list[Kratos.Array1DVariable3], arg4: list[Kratos.DoubleVariable], arg5: list[Kratos.Array1DVariable3], arg6: Kratos::EmbeddedSkinVisualizationProcess::LevelSetType, arg7: Kratos::EmbeddedSkinVisualizationProcess::ShapeFunctionsType, arg8: bool) -> None

        2. __init__(self: KratosFluidDynamicsApplication.EmbeddedSkinVisualizationProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.EmbeddedSkinVisualizationProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.EmbeddedSkinVisualizationProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: list[Kratos.DoubleVariable], arg3: list[Kratos.Array1DVariable3], arg4: list[Kratos.DoubleVariable], arg5: list[Kratos.Array1DVariable3], arg6: Kratos::EmbeddedSkinVisualizationProcess::LevelSetType, arg7: Kratos::EmbeddedSkinVisualizationProcess::ShapeFunctionsType, arg8: bool) -> None

        2. __init__(self: KratosFluidDynamicsApplication.EmbeddedSkinVisualizationProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None

        3. __init__(self: KratosFluidDynamicsApplication.EmbeddedSkinVisualizationProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None
        """

class EstimateDtUtility:
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: float, arg2: float, arg3: float) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.EstimateDtUtility, arg0: Kratos.ModelPart, arg1: float, arg2: float, arg3: float) -> None

        2. __init__(self: KratosFluidDynamicsApplication.EstimateDtUtility, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.EstimateDtUtility, arg0: Kratos.ModelPart, arg1: float, arg2: float, arg3: float) -> None

        2. __init__(self: KratosFluidDynamicsApplication.EstimateDtUtility, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """
    def EstimateDt(self) -> float:
        """EstimateDt(self: KratosFluidDynamicsApplication.EstimateDtUtility) -> float"""
    def SetCFL(self, arg0: float) -> None:
        """SetCFL(self: KratosFluidDynamicsApplication.EstimateDtUtility, arg0: float) -> None"""
    @overload
    def SetDtMax(self, arg0: float) -> None:
        """SetDtMax(*args, **kwargs)
        Overloaded function.

        1. SetDtMax(self: KratosFluidDynamicsApplication.EstimateDtUtility, arg0: float) -> None

        2. SetDtMax(self: KratosFluidDynamicsApplication.EstimateDtUtility, arg0: float) -> None
        """
    @overload
    def SetDtMax(self, arg0: float) -> None:
        """SetDtMax(*args, **kwargs)
        Overloaded function.

        1. SetDtMax(self: KratosFluidDynamicsApplication.EstimateDtUtility, arg0: float) -> None

        2. SetDtMax(self: KratosFluidDynamicsApplication.EstimateDtUtility, arg0: float) -> None
        """

class Euler2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosFluidDynamicsApplication.Euler2DLaw) -> None"""

class Euler3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosFluidDynamicsApplication.Euler3DLaw) -> None"""

class FluidAuxiliaryUtilities:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    @staticmethod
    def CalculateFlowRate(arg0: Kratos.ModelPart) -> float:
        """CalculateFlowRate(arg0: Kratos.ModelPart) -> float"""
    @overload
    @staticmethod
    def CalculateFlowRateNegativeSkin(arg0: Kratos.ModelPart) -> float:
        """CalculateFlowRateNegativeSkin(*args, **kwargs)
        Overloaded function.

        1. CalculateFlowRateNegativeSkin(arg0: Kratos.ModelPart) -> float

        2. CalculateFlowRateNegativeSkin(arg0: Kratos.ModelPart, arg1: Kratos.Flags) -> float
        """
    @overload
    @staticmethod
    def CalculateFlowRateNegativeSkin(arg0: Kratos.ModelPart, arg1: Kratos.Flags) -> float:
        """CalculateFlowRateNegativeSkin(*args, **kwargs)
        Overloaded function.

        1. CalculateFlowRateNegativeSkin(arg0: Kratos.ModelPart) -> float

        2. CalculateFlowRateNegativeSkin(arg0: Kratos.ModelPart, arg1: Kratos.Flags) -> float
        """
    @overload
    @staticmethod
    def CalculateFlowRatePositiveSkin(arg0: Kratos.ModelPart) -> float:
        """CalculateFlowRatePositiveSkin(*args, **kwargs)
        Overloaded function.

        1. CalculateFlowRatePositiveSkin(arg0: Kratos.ModelPart) -> float

        2. CalculateFlowRatePositiveSkin(arg0: Kratos.ModelPart, arg1: Kratos.Flags) -> float
        """
    @overload
    @staticmethod
    def CalculateFlowRatePositiveSkin(arg0: Kratos.ModelPart, arg1: Kratos.Flags) -> float:
        """CalculateFlowRatePositiveSkin(*args, **kwargs)
        Overloaded function.

        1. CalculateFlowRatePositiveSkin(arg0: Kratos.ModelPart) -> float

        2. CalculateFlowRatePositiveSkin(arg0: Kratos.ModelPart, arg1: Kratos.Flags) -> float
        """
    @staticmethod
    def CalculateFluidCutElementsNegativeVolume(arg0: Kratos.ModelPart) -> float:
        """CalculateFluidCutElementsNegativeVolume(arg0: Kratos.ModelPart) -> float"""
    @staticmethod
    def CalculateFluidCutElementsPositiveVolume(arg0: Kratos.ModelPart) -> float:
        """CalculateFluidCutElementsPositiveVolume(arg0: Kratos.ModelPart) -> float"""
    @staticmethod
    def CalculateFluidNegativeVolume(arg0: Kratos.ModelPart) -> float:
        """CalculateFluidNegativeVolume(arg0: Kratos.ModelPart) -> float"""
    @staticmethod
    def CalculateFluidPositiveVolume(arg0: Kratos.ModelPart) -> float:
        """CalculateFluidPositiveVolume(arg0: Kratos.ModelPart) -> float"""
    @staticmethod
    def CalculateFluidVolume(arg0: Kratos.ModelPart) -> float:
        """CalculateFluidVolume(arg0: Kratos.ModelPart) -> float"""
    @overload
    @staticmethod
    def FindMaximumEdgeLength(arg0: Kratos.ModelPart) -> float:
        """FindMaximumEdgeLength(*args, **kwargs)
        Overloaded function.

        1. FindMaximumEdgeLength(arg0: Kratos.ModelPart) -> float

        2. FindMaximumEdgeLength(arg0: Kratos.ModelPart, arg1: bool) -> float
        """
    @overload
    @staticmethod
    def FindMaximumEdgeLength(arg0: Kratos.ModelPart, arg1: bool) -> float:
        """FindMaximumEdgeLength(*args, **kwargs)
        Overloaded function.

        1. FindMaximumEdgeLength(arg0: Kratos.ModelPart) -> float

        2. FindMaximumEdgeLength(arg0: Kratos.ModelPart, arg1: bool) -> float
        """
    @staticmethod
    def MapVelocityFromSkinToVolumeRBF(arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: float) -> None:
        """MapVelocityFromSkinToVolumeRBF(arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: float) -> None"""
    @staticmethod
    def PostprocessP2P1ContinuousPressure(arg0: Kratos.ModelPart) -> None:
        """PostprocessP2P1ContinuousPressure(arg0: Kratos.ModelPart) -> None"""

class FluidCharacteristicNumbersUtilities:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    @staticmethod
    def CalculateLocalCFL(arg0: Kratos.ModelPart) -> None:
        """CalculateLocalCFL(arg0: Kratos.ModelPart) -> None"""

class FluidMeshUtilities:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    @staticmethod
    def AllElementsAreSimplex(arg0: Kratos.ModelPart) -> bool:
        """AllElementsAreSimplex(arg0: Kratos.ModelPart) -> bool"""
    @staticmethod
    def AssignNeighbourElementsToConditions(arg0: Kratos.ModelPart, arg1: bool) -> None:
        """AssignNeighbourElementsToConditions(arg0: Kratos.ModelPart, arg1: bool) -> None"""

class FluidTestUtilities:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    @overload
    @staticmethod
    def RandomFillHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float, arg3: float, arg4: int) -> None:
        """RandomFillHistoricalVariable(*args, **kwargs)
        Overloaded function.

        1. RandomFillHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float, arg3: float, arg4: int) -> None

        2. RandomFillHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: float, arg3: float, arg4: int) -> None

        3. RandomFillHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: str, arg3: float, arg4: float, arg5: int) -> None

        4. RandomFillHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: str, arg3: float, arg4: float, arg5: int) -> None
        """
    @overload
    @staticmethod
    def RandomFillHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: float, arg3: float, arg4: int) -> None:
        """RandomFillHistoricalVariable(*args, **kwargs)
        Overloaded function.

        1. RandomFillHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float, arg3: float, arg4: int) -> None

        2. RandomFillHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: float, arg3: float, arg4: int) -> None

        3. RandomFillHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: str, arg3: float, arg4: float, arg5: int) -> None

        4. RandomFillHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: str, arg3: float, arg4: float, arg5: int) -> None
        """
    @overload
    @staticmethod
    def RandomFillHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: str, arg3: float, arg4: float, arg5: int) -> None:
        """RandomFillHistoricalVariable(*args, **kwargs)
        Overloaded function.

        1. RandomFillHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float, arg3: float, arg4: int) -> None

        2. RandomFillHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: float, arg3: float, arg4: int) -> None

        3. RandomFillHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: str, arg3: float, arg4: float, arg5: int) -> None

        4. RandomFillHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: str, arg3: float, arg4: float, arg5: int) -> None
        """
    @overload
    @staticmethod
    def RandomFillHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: str, arg3: float, arg4: float, arg5: int) -> None:
        """RandomFillHistoricalVariable(*args, **kwargs)
        Overloaded function.

        1. RandomFillHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float, arg3: float, arg4: int) -> None

        2. RandomFillHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: float, arg3: float, arg4: int) -> None

        3. RandomFillHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: str, arg3: float, arg4: float, arg5: int) -> None

        4. RandomFillHistoricalVariable(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: str, arg3: float, arg4: float, arg5: int) -> None
        """
    @overload
    @staticmethod
    def RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None:
        """RandomFillNonHistoricalVariable(*args, **kwargs)
        Overloaded function.

        1. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        2. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        3. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        4. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        5. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        6. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        7. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        8. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        9. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        10. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        11. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        12. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None
        """
    @overload
    @staticmethod
    def RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None:
        """RandomFillNonHistoricalVariable(*args, **kwargs)
        Overloaded function.

        1. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        2. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        3. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        4. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        5. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        6. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        7. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        8. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        9. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        10. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        11. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        12. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None
        """
    @overload
    @staticmethod
    def RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None:
        """RandomFillNonHistoricalVariable(*args, **kwargs)
        Overloaded function.

        1. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        2. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        3. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        4. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        5. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        6. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        7. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        8. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        9. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        10. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        11. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        12. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None
        """
    @overload
    @staticmethod
    def RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None:
        """RandomFillNonHistoricalVariable(*args, **kwargs)
        Overloaded function.

        1. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        2. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        3. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        4. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        5. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        6. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        7. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        8. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        9. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        10. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        11. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        12. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None
        """
    @overload
    @staticmethod
    def RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None:
        """RandomFillNonHistoricalVariable(*args, **kwargs)
        Overloaded function.

        1. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        2. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        3. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        4. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        5. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        6. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        7. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        8. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        9. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        10. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        11. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        12. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None
        """
    @overload
    @staticmethod
    def RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None:
        """RandomFillNonHistoricalVariable(*args, **kwargs)
        Overloaded function.

        1. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        2. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        3. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        4. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        5. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        6. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        7. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        8. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        9. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        10. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        11. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        12. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None
        """
    @overload
    @staticmethod
    def RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None:
        """RandomFillNonHistoricalVariable(*args, **kwargs)
        Overloaded function.

        1. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        2. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        3. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        4. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        5. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        6. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        7. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        8. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        9. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        10. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        11. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        12. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None
        """
    @overload
    @staticmethod
    def RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None:
        """RandomFillNonHistoricalVariable(*args, **kwargs)
        Overloaded function.

        1. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        2. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        3. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        4. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        5. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        6. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        7. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        8. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        9. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        10. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        11. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        12. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None
        """
    @overload
    @staticmethod
    def RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None:
        """RandomFillNonHistoricalVariable(*args, **kwargs)
        Overloaded function.

        1. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        2. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        3. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        4. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        5. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        6. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        7. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        8. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        9. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        10. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        11. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        12. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None
        """
    @overload
    @staticmethod
    def RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None:
        """RandomFillNonHistoricalVariable(*args, **kwargs)
        Overloaded function.

        1. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        2. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        3. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        4. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        5. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        6. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        7. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        8. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        9. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        10. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        11. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        12. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None
        """
    @overload
    @staticmethod
    def RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None:
        """RandomFillNonHistoricalVariable(*args, **kwargs)
        Overloaded function.

        1. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        2. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        3. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        4. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        5. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        6. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        7. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        8. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        9. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        10. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        11. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        12. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None
        """
    @overload
    @staticmethod
    def RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None:
        """RandomFillNonHistoricalVariable(*args, **kwargs)
        Overloaded function.

        1. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        2. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        3. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        4. RandomFillNonHistoricalVariable(arg0: Kratos.NodesArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        5. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        6. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        7. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        8. RandomFillNonHistoricalVariable(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        9. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: int, arg3: float, arg4: float) -> None

        10. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: str, arg3: int, arg4: float, arg5: float) -> None

        11. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: int, arg3: float, arg4: float) -> None

        12. RandomFillNonHistoricalVariable(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: str, arg3: int, arg4: float, arg5: float) -> None
        """

class FractionalStepSettings(BaseSettingsType):
    def __init__(self, arg0: Kratos.ModelPart, arg1: int, arg2: int, arg3: bool, arg4: bool, arg5: bool) -> None:
        """__init__(self: KratosFluidDynamicsApplication.FractionalStepSettings, arg0: Kratos.ModelPart, arg1: int, arg2: int, arg3: bool, arg4: bool, arg5: bool) -> None"""
    def GetStrategy(self, arg0: StrategyLabel) -> Kratos.ImplicitSolvingStrategy:
        """GetStrategy(self: KratosFluidDynamicsApplication.FractionalStepSettings, arg0: KratosFluidDynamicsApplication.StrategyLabel) -> Kratos.ImplicitSolvingStrategy"""
    def SetEchoLevel(self, arg0: int) -> None:
        """SetEchoLevel(self: KratosFluidDynamicsApplication.FractionalStepSettings, arg0: int) -> None"""
    def SetStrategy(self, arg0: StrategyLabel, arg1: Kratos.LinearSolver, arg2: float, arg3: int) -> None:
        """SetStrategy(self: KratosFluidDynamicsApplication.FractionalStepSettings, arg0: KratosFluidDynamicsApplication.StrategyLabel, arg1: Kratos.LinearSolver, arg2: float, arg3: int) -> None"""
    @overload
    def SetTurbulenceModel(self, arg0: TurbulenceModelLabel, arg1: Kratos.LinearSolver, arg2: float, arg3: int) -> None:
        """SetTurbulenceModel(*args, **kwargs)
        Overloaded function.

        1. SetTurbulenceModel(self: KratosFluidDynamicsApplication.FractionalStepSettings, arg0: KratosFluidDynamicsApplication.TurbulenceModelLabel, arg1: Kratos.LinearSolver, arg2: float, arg3: int) -> None

        2. SetTurbulenceModel(self: KratosFluidDynamicsApplication.FractionalStepSettings, arg0: Kratos.Process) -> None
        """
    @overload
    def SetTurbulenceModel(self, arg0: Kratos.Process) -> None:
        """SetTurbulenceModel(*args, **kwargs)
        Overloaded function.

        1. SetTurbulenceModel(self: KratosFluidDynamicsApplication.FractionalStepSettings, arg0: KratosFluidDynamicsApplication.TurbulenceModelLabel, arg1: Kratos.LinearSolver, arg2: float, arg3: int) -> None

        2. SetTurbulenceModel(self: KratosFluidDynamicsApplication.FractionalStepSettings, arg0: Kratos.Process) -> None
        """

class FractionalStepSettingsPeriodic(BaseSettingsType):
    def __init__(self, arg0: Kratos.ModelPart, arg1: int, arg2: int, arg3: bool, arg4: bool, arg5: bool, arg6: Kratos.IntegerVariable) -> None:
        """__init__(self: KratosFluidDynamicsApplication.FractionalStepSettingsPeriodic, arg0: Kratos.ModelPart, arg1: int, arg2: int, arg3: bool, arg4: bool, arg5: bool, arg6: Kratos.IntegerVariable) -> None"""
    def GetStrategy(self, arg0: StrategyLabel) -> Kratos.ImplicitSolvingStrategy:
        """GetStrategy(self: KratosFluidDynamicsApplication.FractionalStepSettingsPeriodic, arg0: KratosFluidDynamicsApplication.StrategyLabel) -> Kratos.ImplicitSolvingStrategy"""
    def SetEchoLevel(self, arg0: int) -> None:
        """SetEchoLevel(self: KratosFluidDynamicsApplication.FractionalStepSettingsPeriodic, arg0: int) -> None"""
    def SetStrategy(self, arg0: StrategyLabel, arg1: Kratos.LinearSolver, arg2: float, arg3: int) -> None:
        """SetStrategy(self: KratosFluidDynamicsApplication.FractionalStepSettingsPeriodic, arg0: KratosFluidDynamicsApplication.StrategyLabel, arg1: Kratos.LinearSolver, arg2: float, arg3: int) -> None"""

class FractionalStepStrategy(Kratos.ImplicitSolvingStrategy):
    def __init__(self, *args, **kwargs) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.FractionalStepStrategy, arg0: Kratos.ModelPart, arg1: Kratos::SolverSettings<Kratos::UblasSpace<double, boost::numeric::ublas::compressed_matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, 0ul, boost::numeric::ublas::unbounded_array<unsigned long, std::allocator<unsigned long> >, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::UblasSpace<double, boost::numeric::ublas::matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::LinearSolver<Kratos::UblasSpace<double, boost::numeric::ublas::compressed_matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, 0ul, boost::numeric::ublas::unbounded_array<unsigned long, std::allocator<unsigned long> >, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::UblasSpace<double, boost::numeric::ublas::matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::Reorderer<Kratos::UblasSpace<double, boost::numeric::ublas::compressed_matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, 0ul, boost::numeric::ublas::unbounded_array<unsigned long, std::allocator<unsigned long> >, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::UblasSpace<double, boost::numeric::ublas::matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > > > > >, arg2: bool) -> None

        2. __init__(self: KratosFluidDynamicsApplication.FractionalStepStrategy, arg0: Kratos.ModelPart, arg1: Kratos::SolverSettings<Kratos::UblasSpace<double, boost::numeric::ublas::compressed_matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, 0ul, boost::numeric::ublas::unbounded_array<unsigned long, std::allocator<unsigned long> >, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::UblasSpace<double, boost::numeric::ublas::matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::LinearSolver<Kratos::UblasSpace<double, boost::numeric::ublas::compressed_matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, 0ul, boost::numeric::ublas::unbounded_array<unsigned long, std::allocator<unsigned long> >, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::UblasSpace<double, boost::numeric::ublas::matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::Reorderer<Kratos::UblasSpace<double, boost::numeric::ublas::compressed_matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, 0ul, boost::numeric::ublas::unbounded_array<unsigned long, std::allocator<unsigned long> >, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::UblasSpace<double, boost::numeric::ublas::matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > > > > >, arg2: bool, arg3: bool) -> None

        3. __init__(self: KratosFluidDynamicsApplication.FractionalStepStrategy, arg0: Kratos.ModelPart, arg1: Kratos::SolverSettings<Kratos::UblasSpace<double, boost::numeric::ublas::compressed_matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, 0ul, boost::numeric::ublas::unbounded_array<unsigned long, std::allocator<unsigned long> >, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::UblasSpace<double, boost::numeric::ublas::matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::LinearSolver<Kratos::UblasSpace<double, boost::numeric::ublas::compressed_matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, 0ul, boost::numeric::ublas::unbounded_array<unsigned long, std::allocator<unsigned long> >, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::UblasSpace<double, boost::numeric::ublas::matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::Reorderer<Kratos::UblasSpace<double, boost::numeric::ublas::compressed_matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, 0ul, boost::numeric::ublas::unbounded_array<unsigned long, std::allocator<unsigned long> >, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::UblasSpace<double, boost::numeric::ublas::matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > > > > >, arg2: bool, arg3: Kratos.IntegerVariable) -> None

        4. __init__(self: KratosFluidDynamicsApplication.FractionalStepStrategy, arg0: Kratos.ModelPart, arg1: Kratos::SolverSettings<Kratos::UblasSpace<double, boost::numeric::ublas::compressed_matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, 0ul, boost::numeric::ublas::unbounded_array<unsigned long, std::allocator<unsigned long> >, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::UblasSpace<double, boost::numeric::ublas::matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::LinearSolver<Kratos::UblasSpace<double, boost::numeric::ublas::compressed_matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, 0ul, boost::numeric::ublas::unbounded_array<unsigned long, std::allocator<unsigned long> >, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::UblasSpace<double, boost::numeric::ublas::matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::Reorderer<Kratos::UblasSpace<double, boost::numeric::ublas::compressed_matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, 0ul, boost::numeric::ublas::unbounded_array<unsigned long, std::allocator<unsigned long> >, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::UblasSpace<double, boost::numeric::ublas::matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > > > > >, arg2: bool, arg3: bool, arg4: Kratos.IntegerVariable) -> None
        """
    def AddIterationStep(self, arg0: Kratos.Process) -> None:
        """AddIterationStep(self: KratosFluidDynamicsApplication.FractionalStepStrategy, arg0: Kratos.Process) -> None"""
    def CalculateReactions(self) -> None:
        """CalculateReactions(self: KratosFluidDynamicsApplication.FractionalStepStrategy) -> None"""
    def ClearExtraIterationSteps(self) -> None:
        """ClearExtraIterationSteps(self: KratosFluidDynamicsApplication.FractionalStepStrategy) -> None"""

class HerschelBulkley3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosFluidDynamicsApplication.HerschelBulkley3DLaw) -> None"""

class IntegrationPointStatisticsProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosFluidDynamicsApplication.IntegrationPointStatisticsProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class IntegrationPointToNodeTransformationUtility2D:
    def __init__(self) -> None:
        """__init__(self: KratosFluidDynamicsApplication.IntegrationPointToNodeTransformationUtility2D) -> None"""
    def TransformFromIntegrationPointsToNodes(self, arg0: Kratos.DoubleVariable, arg1: Kratos.ModelPart) -> None:
        """TransformFromIntegrationPointsToNodes(self: KratosFluidDynamicsApplication.IntegrationPointToNodeTransformationUtility2D, arg0: Kratos.DoubleVariable, arg1: Kratos.ModelPart) -> None"""

class IntegrationPointToNodeTransformationUtility3D:
    def __init__(self) -> None:
        """__init__(self: KratosFluidDynamicsApplication.IntegrationPointToNodeTransformationUtility3D) -> None"""
    def TransformFromIntegrationPointsToNodes(self, arg0: Kratos.DoubleVariable, arg1: Kratos.ModelPart) -> None:
        """TransformFromIntegrationPointsToNodes(self: KratosFluidDynamicsApplication.IntegrationPointToNodeTransformationUtility3D, arg0: Kratos.DoubleVariable, arg1: Kratos.ModelPart) -> None"""

class KratosFluidDynamicsApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosFluidDynamicsApplication.KratosFluidDynamicsApplication) -> None"""

class MassConservationCheckProcess(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: bool, arg2: int, arg3: bool, arg4: str) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.MassConservationCheckProcess, arg0: Kratos.ModelPart, arg1: bool, arg2: int, arg3: bool, arg4: str) -> None

        2. __init__(self: KratosFluidDynamicsApplication.MassConservationCheckProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.MassConservationCheckProcess, arg0: Kratos.ModelPart, arg1: bool, arg2: int, arg3: bool, arg4: str) -> None

        2. __init__(self: KratosFluidDynamicsApplication.MassConservationCheckProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """
    def ComputeFlowOverBoundary(self, arg0: Kratos.Flags) -> float:
        """ComputeFlowOverBoundary(self: KratosFluidDynamicsApplication.MassConservationCheckProcess, arg0: Kratos.Flags) -> float"""
    def ComputeInterfaceArea(self) -> float:
        """ComputeInterfaceArea(self: KratosFluidDynamicsApplication.MassConservationCheckProcess) -> float"""
    def ComputeNegativeVolume(self) -> float:
        """ComputeNegativeVolume(self: KratosFluidDynamicsApplication.MassConservationCheckProcess) -> float"""
    def ComputePositiveVolume(self) -> float:
        """ComputePositiveVolume(self: KratosFluidDynamicsApplication.MassConservationCheckProcess) -> float"""
    def ExecuteInTimeStep(self) -> str:
        """ExecuteInTimeStep(self: KratosFluidDynamicsApplication.MassConservationCheckProcess) -> str"""
    def Initialize(self) -> str:
        """Initialize(self: KratosFluidDynamicsApplication.MassConservationCheckProcess) -> str"""

class Newtonian2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosFluidDynamicsApplication.Newtonian2DLaw) -> None"""

class Newtonian3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosFluidDynamicsApplication.Newtonian3DLaw) -> None"""

class NewtonianTemperatureDependent2DLaw(Newtonian2DLaw):
    def __init__(self) -> None:
        """__init__(self: KratosFluidDynamicsApplication.NewtonianTemperatureDependent2DLaw) -> None"""

class NewtonianTemperatureDependent3DLaw(Newtonian3DLaw):
    def __init__(self) -> None:
        """__init__(self: KratosFluidDynamicsApplication.NewtonianTemperatureDependent3DLaw) -> None"""

class NewtonianTwoFluid2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosFluidDynamicsApplication.NewtonianTwoFluid2DLaw) -> None"""

class NewtonianTwoFluid3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosFluidDynamicsApplication.NewtonianTwoFluid3DLaw) -> None"""

class PeriodicConditionUtilities:
    def __init__(self, arg0: Kratos.ModelPart, arg1: int) -> None:
        """__init__(self: KratosFluidDynamicsApplication.PeriodicConditionUtilities, arg0: Kratos.ModelPart, arg1: int) -> None"""
    def AddPeriodicVariable(self, arg0: Kratos.Properties, arg1: Kratos.DoubleVariable) -> None:
        """AddPeriodicVariable(self: KratosFluidDynamicsApplication.PeriodicConditionUtilities, arg0: Kratos.Properties, arg1: Kratos.DoubleVariable) -> None"""
    def DefinePeriodicBoundary(self, arg0: Kratos.Properties, arg1: str, arg2: float, arg3: float, arg4: float) -> None:
        """DefinePeriodicBoundary(self: KratosFluidDynamicsApplication.PeriodicConditionUtilities, arg0: Kratos.Properties, arg1: str, arg2: float, arg3: float, arg4: float) -> None"""
    def SetUpSearchStructure(self, arg0: Kratos.DoubleVariable, arg1: float) -> None:
        """SetUpSearchStructure(self: KratosFluidDynamicsApplication.PeriodicConditionUtilities, arg0: Kratos.DoubleVariable, arg1: float) -> None"""

class ResidualBasedBlockBuilderAndSolverPeriodic(Kratos.ResidualBasedBlockBuilderAndSolver):
    def __init__(self, arg0: Kratos.LinearSolver, arg1: Kratos.IntegerVariable) -> None:
        """__init__(self: KratosFluidDynamicsApplication.ResidualBasedBlockBuilderAndSolverPeriodic, arg0: Kratos.LinearSolver, arg1: Kratos.IntegerVariable) -> None"""

class ResidualBasedPredictorCorrectorVelocityBossakSchemeTurbulent(Kratos.Scheme):
    @overload
    def __init__(self, arg0: float, arg1: float, arg2: int, arg3: Kratos.Process) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.ResidualBasedPredictorCorrectorVelocityBossakSchemeTurbulent, arg0: float, arg1: float, arg2: int, arg3: Kratos.Process) -> None

        2. __init__(self: KratosFluidDynamicsApplication.ResidualBasedPredictorCorrectorVelocityBossakSchemeTurbulent, arg0: float, arg1: float, arg2: int, arg3: float, arg4: Kratos.Process) -> None

        3. __init__(self: KratosFluidDynamicsApplication.ResidualBasedPredictorCorrectorVelocityBossakSchemeTurbulent, arg0: float, arg1: float, arg2: int) -> None

        4. __init__(self: KratosFluidDynamicsApplication.ResidualBasedPredictorCorrectorVelocityBossakSchemeTurbulent, arg0: float, arg1: int, arg2: Kratos.IntegerVariable) -> None
        """
    @overload
    def __init__(self, arg0: float, arg1: float, arg2: int, arg3: float, arg4: Kratos.Process) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.ResidualBasedPredictorCorrectorVelocityBossakSchemeTurbulent, arg0: float, arg1: float, arg2: int, arg3: Kratos.Process) -> None

        2. __init__(self: KratosFluidDynamicsApplication.ResidualBasedPredictorCorrectorVelocityBossakSchemeTurbulent, arg0: float, arg1: float, arg2: int, arg3: float, arg4: Kratos.Process) -> None

        3. __init__(self: KratosFluidDynamicsApplication.ResidualBasedPredictorCorrectorVelocityBossakSchemeTurbulent, arg0: float, arg1: float, arg2: int) -> None

        4. __init__(self: KratosFluidDynamicsApplication.ResidualBasedPredictorCorrectorVelocityBossakSchemeTurbulent, arg0: float, arg1: int, arg2: Kratos.IntegerVariable) -> None
        """
    @overload
    def __init__(self, arg0: float, arg1: float, arg2: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.ResidualBasedPredictorCorrectorVelocityBossakSchemeTurbulent, arg0: float, arg1: float, arg2: int, arg3: Kratos.Process) -> None

        2. __init__(self: KratosFluidDynamicsApplication.ResidualBasedPredictorCorrectorVelocityBossakSchemeTurbulent, arg0: float, arg1: float, arg2: int, arg3: float, arg4: Kratos.Process) -> None

        3. __init__(self: KratosFluidDynamicsApplication.ResidualBasedPredictorCorrectorVelocityBossakSchemeTurbulent, arg0: float, arg1: float, arg2: int) -> None

        4. __init__(self: KratosFluidDynamicsApplication.ResidualBasedPredictorCorrectorVelocityBossakSchemeTurbulent, arg0: float, arg1: int, arg2: Kratos.IntegerVariable) -> None
        """
    @overload
    def __init__(self, arg0: float, arg1: int, arg2: Kratos.IntegerVariable) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.ResidualBasedPredictorCorrectorVelocityBossakSchemeTurbulent, arg0: float, arg1: float, arg2: int, arg3: Kratos.Process) -> None

        2. __init__(self: KratosFluidDynamicsApplication.ResidualBasedPredictorCorrectorVelocityBossakSchemeTurbulent, arg0: float, arg1: float, arg2: int, arg3: float, arg4: Kratos.Process) -> None

        3. __init__(self: KratosFluidDynamicsApplication.ResidualBasedPredictorCorrectorVelocityBossakSchemeTurbulent, arg0: float, arg1: float, arg2: int) -> None

        4. __init__(self: KratosFluidDynamicsApplication.ResidualBasedPredictorCorrectorVelocityBossakSchemeTurbulent, arg0: float, arg1: int, arg2: Kratos.IntegerVariable) -> None
        """

class ResidualBasedSimpleSteadyScheme(Kratos.Scheme):
    @overload
    def __init__(self, arg0: float, arg1: float, arg2: int, arg3: Kratos.Process) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.ResidualBasedSimpleSteadyScheme, arg0: float, arg1: float, arg2: int, arg3: Kratos.Process) -> None

        2. __init__(self: KratosFluidDynamicsApplication.ResidualBasedSimpleSteadyScheme, arg0: float, arg1: float, arg2: int) -> None
        """
    @overload
    def __init__(self, arg0: float, arg1: float, arg2: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.ResidualBasedSimpleSteadyScheme, arg0: float, arg1: float, arg2: int, arg3: Kratos.Process) -> None

        2. __init__(self: KratosFluidDynamicsApplication.ResidualBasedSimpleSteadyScheme, arg0: float, arg1: float, arg2: int) -> None
        """
    def GetPressureRelaxationFactor(self) -> float:
        """GetPressureRelaxationFactor(self: KratosFluidDynamicsApplication.ResidualBasedSimpleSteadyScheme) -> float"""
    def GetVelocityRelaxationFactor(self) -> float:
        """GetVelocityRelaxationFactor(self: KratosFluidDynamicsApplication.ResidualBasedSimpleSteadyScheme) -> float"""
    def SetPressureRelaxationFactor(self, arg0: float) -> None:
        """SetPressureRelaxationFactor(self: KratosFluidDynamicsApplication.ResidualBasedSimpleSteadyScheme, arg0: float) -> None"""
    def SetVelocityRelaxationFactor(self, arg0: float) -> None:
        """SetVelocityRelaxationFactor(self: KratosFluidDynamicsApplication.ResidualBasedSimpleSteadyScheme, arg0: float) -> None"""

class ShockCapturingEntropyViscosityProcess(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.ShockCapturingEntropyViscosityProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosFluidDynamicsApplication.ShockCapturingEntropyViscosityProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.ShockCapturingEntropyViscosityProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosFluidDynamicsApplication.ShockCapturingEntropyViscosityProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """

class ShockCapturingPhysicsBasedProcess(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.ShockCapturingPhysicsBasedProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosFluidDynamicsApplication.ShockCapturingPhysicsBasedProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosFluidDynamicsApplication.ShockCapturingPhysicsBasedProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosFluidDynamicsApplication.ShockCapturingPhysicsBasedProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """

class SimpleSteadyAdjointScheme(Kratos.Scheme):
    def __init__(self, arg0: Kratos.AdjointResponseFunction, arg1: int, arg2: int) -> None:
        """__init__(self: KratosFluidDynamicsApplication.SimpleSteadyAdjointScheme, arg0: Kratos.AdjointResponseFunction, arg1: int, arg2: int) -> None"""

class SimpleSteadySensitivityBuilderScheme(Kratos.SensitivityBuilderScheme):
    def __init__(self, arg0: int, arg1: int) -> None:
        """__init__(self: KratosFluidDynamicsApplication.SimpleSteadySensitivityBuilderScheme, arg0: int, arg1: int) -> None"""

class SpalartAllmarasTurbulenceModel(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: int, arg3: float, arg4: int, arg5: bool, arg6: int) -> None:
        """__init__(self: KratosFluidDynamicsApplication.SpalartAllmarasTurbulenceModel, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: int, arg3: float, arg4: int, arg5: bool, arg6: int) -> None"""
    def ActivateDES(self, arg0: float) -> None:
        """ActivateDES(self: KratosFluidDynamicsApplication.SpalartAllmarasTurbulenceModel, arg0: float) -> None"""
    def AdaptForFractionalStep(self) -> None:
        """AdaptForFractionalStep(self: KratosFluidDynamicsApplication.SpalartAllmarasTurbulenceModel) -> None"""

class StokesInitializationProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: int, arg3: Kratos.IntegerVariable) -> None:
        """__init__(self: KratosFluidDynamicsApplication.StokesInitializationProcess, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: int, arg3: Kratos.IntegerVariable) -> None"""
    def SetConditions(self, arg0: Kratos.ModelPart, arg1: Kratos.ConditionsArray) -> None:
        """SetConditions(self: KratosFluidDynamicsApplication.StokesInitializationProcess, arg0: Kratos.ModelPart, arg1: Kratos.ConditionsArray) -> None"""

class StrategyLabel:
    __members__: ClassVar[dict] = ...  # read-only
    Pressure: ClassVar[StrategyLabel] = ...
    Velocity: ClassVar[StrategyLabel] = ...
    __entries: ClassVar[dict] = ...
    def __init__(self, value: int) -> None:
        """__init__(self: KratosFluidDynamicsApplication.StrategyLabel, value: int) -> None"""
    def __eq__(self, other: object) -> bool:
        """__eq__(self: object, other: object) -> bool"""
    def __hash__(self) -> int:
        """__hash__(self: object) -> int"""
    def __index__(self) -> int:
        """__index__(self: KratosFluidDynamicsApplication.StrategyLabel) -> int"""
    def __int__(self) -> int:
        """__int__(self: KratosFluidDynamicsApplication.StrategyLabel) -> int"""
    def __ne__(self, other: object) -> bool:
        """__ne__(self: object, other: object) -> bool"""
    @property
    def name(self) -> str: ...
    @property
    def value(self) -> int: ...

class TurbulenceModelLabel:
    __members__: ClassVar[dict] = ...  # read-only
    SpalartAllmaras: ClassVar[TurbulenceModelLabel] = ...
    __entries: ClassVar[dict] = ...
    def __init__(self, value: int) -> None:
        """__init__(self: KratosFluidDynamicsApplication.TurbulenceModelLabel, value: int) -> None"""
    def __eq__(self, other: object) -> bool:
        """__eq__(self: object, other: object) -> bool"""
    def __hash__(self) -> int:
        """__hash__(self: object) -> int"""
    def __index__(self) -> int:
        """__index__(self: KratosFluidDynamicsApplication.TurbulenceModelLabel) -> int"""
    def __int__(self) -> int:
        """__int__(self: KratosFluidDynamicsApplication.TurbulenceModelLabel) -> int"""
    def __ne__(self, other: object) -> bool:
        """__ne__(self: object, other: object) -> bool"""
    @property
    def name(self) -> str: ...
    @property
    def value(self) -> int: ...

class TwoFluidNavierStokesFractionalConvectionProcess2D(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.LinearSolver, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosFluidDynamicsApplication.TwoFluidNavierStokesFractionalConvectionProcess2D, arg0: Kratos.Model, arg1: Kratos.LinearSolver, arg2: Kratos.Parameters) -> None"""

class TwoFluidNavierStokesFractionalConvectionProcess3D(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.LinearSolver, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosFluidDynamicsApplication.TwoFluidNavierStokesFractionalConvectionProcess3D, arg0: Kratos.Model, arg1: Kratos.LinearSolver, arg2: Kratos.Parameters) -> None"""

class TwoFluidsInletProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters, arg2: Kratos.Process) -> None:
        """__init__(self: KratosFluidDynamicsApplication.TwoFluidsInletProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters, arg2: Kratos.Process) -> None"""
    def SmoothDistanceField(self) -> None:
        """SmoothDistanceField(self: KratosFluidDynamicsApplication.TwoFluidsInletProcess) -> None"""

class VelocityBossakAdjointScheme(Kratos.Scheme):
    def __init__(self, arg0: Kratos.Parameters, arg1: Kratos.AdjointResponseFunction, arg2: int, arg3: int) -> None:
        """__init__(self: KratosFluidDynamicsApplication.VelocityBossakAdjointScheme, arg0: Kratos.Parameters, arg1: Kratos.AdjointResponseFunction, arg2: int, arg3: int) -> None"""

class VelocityBossakSensitivityBuilderScheme(Kratos.SensitivityBuilderScheme):
    def __init__(self, arg0: float, arg1: int, arg2: int) -> None:
        """__init__(self: KratosFluidDynamicsApplication.VelocityBossakSensitivityBuilderScheme, arg0: float, arg1: int, arg2: int) -> None"""

class VelocityPressureNormSquareResponseFunction(Kratos.AdjointResponseFunction):
    def __init__(self, arg0: Kratos.Parameters, arg1: Kratos.Model) -> None:
        """__init__(self: KratosFluidDynamicsApplication.VelocityPressureNormSquareResponseFunction, arg0: Kratos.Parameters, arg1: Kratos.Model) -> None"""

class WindkesselModel(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosFluidDynamicsApplication.WindkesselModel, arg0: Kratos.ModelPart) -> None"""
