import Kratos
from typing import overload

class BFECCConvection2D:
    @overload
    def __init__(self, arg0: Kratos.BinBasedFastPointLocator2D) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosConvectionDiffusionApplication.BFECCConvection2D, arg0: Kratos.BinBasedFastPointLocator2D) -> None

        2. __init__(self: KratosConvectionDiffusionApplication.BFECCConvection2D, arg0: Kratos.BinBasedFastPointLocator2D, arg1: bool) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.BinBasedFastPointLocator2D, arg1: bool) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosConvectionDiffusionApplication.BFECCConvection2D, arg0: Kratos.BinBasedFastPointLocator2D) -> None

        2. __init__(self: KratosConvectionDiffusionApplication.BFECCConvection2D, arg0: Kratos.BinBasedFastPointLocator2D, arg1: bool) -> None
        """
    def BFECCconvect(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: float) -> None:
        """BFECCconvect(self: KratosConvectionDiffusionApplication.BFECCConvection2D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: float) -> None"""
    def CopyScalarVarToPreviousTimeStep(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None:
        """CopyScalarVarToPreviousTimeStep(self: KratosConvectionDiffusionApplication.BFECCConvection2D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None"""
    def ResetBoundaryConditions(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None:
        """ResetBoundaryConditions(self: KratosConvectionDiffusionApplication.BFECCConvection2D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None"""

class BFECCConvection3D:
    @overload
    def __init__(self, arg0: Kratos.BinBasedFastPointLocator3D) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosConvectionDiffusionApplication.BFECCConvection3D, arg0: Kratos.BinBasedFastPointLocator3D) -> None

        2. __init__(self: KratosConvectionDiffusionApplication.BFECCConvection3D, arg0: Kratos.BinBasedFastPointLocator3D, arg1: bool) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.BinBasedFastPointLocator3D, arg1: bool) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosConvectionDiffusionApplication.BFECCConvection3D, arg0: Kratos.BinBasedFastPointLocator3D) -> None

        2. __init__(self: KratosConvectionDiffusionApplication.BFECCConvection3D, arg0: Kratos.BinBasedFastPointLocator3D, arg1: bool) -> None
        """
    def BFECCconvect(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: float) -> None:
        """BFECCconvect(self: KratosConvectionDiffusionApplication.BFECCConvection3D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: float) -> None"""
    def CopyScalarVarToPreviousTimeStep(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None:
        """CopyScalarVarToPreviousTimeStep(self: KratosConvectionDiffusionApplication.BFECCConvection3D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None"""
    def ResetBoundaryConditions(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None:
        """ResetBoundaryConditions(self: KratosConvectionDiffusionApplication.BFECCConvection3D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None"""

class BFECCLimiterConvection2D:
    def __init__(self, arg0: Kratos.BinBasedFastPointLocator2D) -> None:
        """__init__(self: KratosConvectionDiffusionApplication.BFECCLimiterConvection2D, arg0: Kratos.BinBasedFastPointLocator2D) -> None"""
    def BFECCconvect(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: float) -> None:
        """BFECCconvect(self: KratosConvectionDiffusionApplication.BFECCLimiterConvection2D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: float) -> None"""

class BFECCLimiterConvection3D:
    def __init__(self, arg0: Kratos.BinBasedFastPointLocator3D) -> None:
        """__init__(self: KratosConvectionDiffusionApplication.BFECCLimiterConvection3D, arg0: Kratos.BinBasedFastPointLocator3D) -> None"""
    def BFECCconvect(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: float) -> None:
        """BFECCconvect(self: KratosConvectionDiffusionApplication.BFECCLimiterConvection3D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: float) -> None"""

class EmbeddedMLSConstraintProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosConvectionDiffusionApplication.EmbeddedMLSConstraintProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class ExplicitSolvingStrategyRungeKutta4ConvectionDiffusion(Kratos.ExplicitSolvingStrategyRungeKutta4):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: bool, arg2: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosConvectionDiffusionApplication.ExplicitSolvingStrategyRungeKutta4ConvectionDiffusion, arg0: Kratos.ModelPart, arg1: bool, arg2: int) -> None

        2. __init__(self: KratosConvectionDiffusionApplication.ExplicitSolvingStrategyRungeKutta4ConvectionDiffusion, arg0: Kratos.ModelPart, arg1: Kratos.ExplicitBuilder, arg2: bool, arg3: int) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ExplicitBuilder, arg2: bool, arg3: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosConvectionDiffusionApplication.ExplicitSolvingStrategyRungeKutta4ConvectionDiffusion, arg0: Kratos.ModelPart, arg1: bool, arg2: int) -> None

        2. __init__(self: KratosConvectionDiffusionApplication.ExplicitSolvingStrategyRungeKutta4ConvectionDiffusion, arg0: Kratos.ModelPart, arg1: Kratos.ExplicitBuilder, arg2: bool, arg3: int) -> None
        """

class FaceHeatUtilities:
    def __init__(self) -> None:
        """__init__(self: KratosConvectionDiffusionApplication.FaceHeatUtilities) -> None"""
    def ApplyFaceHeat(self, arg0: Kratos.ConditionsArray, arg1: float) -> None:
        """ApplyFaceHeat(self: KratosConvectionDiffusionApplication.FaceHeatUtilities, arg0: Kratos.ConditionsArray, arg1: float) -> None"""
    def ConditionModelPart(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: int) -> None:
        """ConditionModelPart(self: KratosConvectionDiffusionApplication.FaceHeatUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: int) -> None"""
    def GenerateModelPart(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: int) -> None:
        """GenerateModelPart(self: KratosConvectionDiffusionApplication.FaceHeatUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: int) -> None"""

class KratosConvectionDiffusionApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosConvectionDiffusionApplication.KratosConvectionDiffusionApplication) -> None"""

class LocalTemperatureAverageResponseFunction(Kratos.AdjointResponseFunction):
    def __init__(self, arg0: Kratos.Parameters, arg1: Kratos.ModelPart) -> None:
        """__init__(self: KratosConvectionDiffusionApplication.LocalTemperatureAverageResponseFunction, arg0: Kratos.Parameters, arg1: Kratos.ModelPart) -> None"""

class MoveParticleUtilityScalarTransport2D:
    def __init__(self, arg0: Kratos.ModelPart, arg1: int) -> None:
        """__init__(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport2D, arg0: Kratos.ModelPart, arg1: int) -> None"""
    def CalculateDeltaVariables(self) -> None:
        """CalculateDeltaVariables(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport2D) -> None"""
    def CalculateVelOverElemSize(self) -> None:
        """CalculateVelOverElemSize(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport2D) -> None"""
    def CopyScalarVarToPreviousTimeStep(self, arg0: Kratos.DoubleVariable, arg1: Kratos.NodesArray) -> None:
        """CopyScalarVarToPreviousTimeStep(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport2D, arg0: Kratos.DoubleVariable, arg1: Kratos.NodesArray) -> None"""
    def CorrectParticlesWithoutMovingUsingDeltaVariables(self) -> None:
        """CorrectParticlesWithoutMovingUsingDeltaVariables(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport2D) -> None"""
    def ExecuteParticlesPritingTool(self, arg0: Kratos.ModelPart, arg1: int) -> None:
        """ExecuteParticlesPritingTool(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport2D, arg0: Kratos.ModelPart, arg1: int) -> None"""
    @overload
    def MountBin(self) -> None:
        """MountBin(*args, **kwargs)
        Overloaded function.

        1. MountBin(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport2D) -> None

        2. MountBin(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport2D, arg0: float) -> None
        """
    @overload
    def MountBin(self, arg0: float) -> None:
        """MountBin(*args, **kwargs)
        Overloaded function.

        1. MountBin(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport2D) -> None

        2. MountBin(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport2D, arg0: float) -> None
        """
    def MoveParticles(self) -> None:
        """MoveParticles(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport2D) -> None"""
    def PostReseed(self, arg0: int) -> None:
        """PostReseed(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport2D, arg0: int) -> None"""
    def PreReseed(self, arg0: int) -> None:
        """PreReseed(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport2D, arg0: int) -> None"""
    def ResetBoundaryConditions(self) -> None:
        """ResetBoundaryConditions(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport2D) -> None"""
    def TransferLagrangianToEulerian(self) -> None:
        """TransferLagrangianToEulerian(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport2D) -> None"""

class MoveParticleUtilityScalarTransport3D:
    def __init__(self, arg0: Kratos.ModelPart, arg1: int) -> None:
        """__init__(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport3D, arg0: Kratos.ModelPart, arg1: int) -> None"""
    def CalculateDeltaVariables(self) -> None:
        """CalculateDeltaVariables(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport3D) -> None"""
    def CalculateVelOverElemSize(self) -> None:
        """CalculateVelOverElemSize(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport3D) -> None"""
    def CopyScalarVarToPreviousTimeStep(self, arg0: Kratos.DoubleVariable, arg1: Kratos.NodesArray) -> None:
        """CopyScalarVarToPreviousTimeStep(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport3D, arg0: Kratos.DoubleVariable, arg1: Kratos.NodesArray) -> None"""
    def CorrectParticlesWithoutMovingUsingDeltaVariables(self) -> None:
        """CorrectParticlesWithoutMovingUsingDeltaVariables(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport3D) -> None"""
    def ExecuteParticlesPritingTool(self, arg0: Kratos.ModelPart, arg1: int) -> None:
        """ExecuteParticlesPritingTool(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport3D, arg0: Kratos.ModelPart, arg1: int) -> None"""
    @overload
    def MountBin(self) -> None:
        """MountBin(*args, **kwargs)
        Overloaded function.

        1. MountBin(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport3D) -> None

        2. MountBin(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport3D, arg0: float) -> None
        """
    @overload
    def MountBin(self, arg0: float) -> None:
        """MountBin(*args, **kwargs)
        Overloaded function.

        1. MountBin(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport3D) -> None

        2. MountBin(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport3D, arg0: float) -> None
        """
    def MoveParticles(self) -> None:
        """MoveParticles(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport3D) -> None"""
    def PostReseed(self, arg0: int) -> None:
        """PostReseed(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport3D, arg0: int) -> None"""
    def PreReseed(self, arg0: int) -> None:
        """PreReseed(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport3D, arg0: int) -> None"""
    def ResetBoundaryConditions(self) -> None:
        """ResetBoundaryConditions(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport3D) -> None"""
    def TransferLagrangianToEulerian(self) -> None:
        """TransferLagrangianToEulerian(self: KratosConvectionDiffusionApplication.MoveParticleUtilityScalarTransport3D) -> None"""

class PureConvectionCrankNUtilities2D:
    def __init__(self) -> None:
        """__init__(self: KratosConvectionDiffusionApplication.PureConvectionCrankNUtilities2D) -> None"""
    def CalculateProjection(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: Kratos.Array1DVariable3, arg5: Kratos.DoubleVariable) -> None:
        """CalculateProjection(self: KratosConvectionDiffusionApplication.PureConvectionCrankNUtilities2D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: Kratos.Array1DVariable3, arg5: Kratos.DoubleVariable) -> None"""
    def ClearSystem(self) -> None:
        """ClearSystem(self: KratosConvectionDiffusionApplication.PureConvectionCrankNUtilities2D) -> None"""
    def ConstructSystem(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None:
        """ConstructSystem(self: KratosConvectionDiffusionApplication.PureConvectionCrankNUtilities2D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None"""
    def ConvectScalarVar(self, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: Kratos.Array1DVariable3, arg5: Kratos.DoubleVariable, arg6: int) -> None:
        """ConvectScalarVar(self: KratosConvectionDiffusionApplication.PureConvectionCrankNUtilities2D, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: Kratos.Array1DVariable3, arg5: Kratos.DoubleVariable, arg6: int) -> None"""

class PureConvectionCrankNUtilities3D:
    def __init__(self) -> None:
        """__init__(self: KratosConvectionDiffusionApplication.PureConvectionCrankNUtilities3D) -> None"""
    def CalculateProjection(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: Kratos.Array1DVariable3, arg5: Kratos.DoubleVariable) -> None:
        """CalculateProjection(self: KratosConvectionDiffusionApplication.PureConvectionCrankNUtilities3D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: Kratos.Array1DVariable3, arg5: Kratos.DoubleVariable) -> None"""
    def ClearSystem(self) -> None:
        """ClearSystem(self: KratosConvectionDiffusionApplication.PureConvectionCrankNUtilities3D) -> None"""
    def ConstructSystem(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None:
        """ConstructSystem(self: KratosConvectionDiffusionApplication.PureConvectionCrankNUtilities3D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None"""
    def ConvectScalarVar(self, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: Kratos.Array1DVariable3, arg5: Kratos.DoubleVariable, arg6: int) -> None:
        """ConvectScalarVar(self: KratosConvectionDiffusionApplication.PureConvectionCrankNUtilities3D, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: Kratos.Array1DVariable3, arg5: Kratos.DoubleVariable, arg6: int) -> None"""

class PureConvectionUtilities2D:
    def __init__(self) -> None:
        """__init__(self: KratosConvectionDiffusionApplication.PureConvectionUtilities2D) -> None"""
    def CalculateProjection(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: Kratos.Array1DVariable3, arg5: Kratos.DoubleVariable) -> None:
        """CalculateProjection(self: KratosConvectionDiffusionApplication.PureConvectionUtilities2D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: Kratos.Array1DVariable3, arg5: Kratos.DoubleVariable) -> None"""
    def ClearSystem(self) -> None:
        """ClearSystem(self: KratosConvectionDiffusionApplication.PureConvectionUtilities2D) -> None"""
    def ConstructSystem(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None:
        """ConstructSystem(self: KratosConvectionDiffusionApplication.PureConvectionUtilities2D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None"""
    def ConvectScalarVar(self, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: Kratos.Array1DVariable3, arg5: Kratos.DoubleVariable, arg6: int) -> None:
        """ConvectScalarVar(self: KratosConvectionDiffusionApplication.PureConvectionUtilities2D, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: Kratos.Array1DVariable3, arg5: Kratos.DoubleVariable, arg6: int) -> None"""

class PureConvectionUtilities3D:
    def __init__(self) -> None:
        """__init__(self: KratosConvectionDiffusionApplication.PureConvectionUtilities3D) -> None"""
    def CalculateProjection(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: Kratos.Array1DVariable3, arg5: Kratos.DoubleVariable) -> None:
        """CalculateProjection(self: KratosConvectionDiffusionApplication.PureConvectionUtilities3D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: Kratos.Array1DVariable3, arg5: Kratos.DoubleVariable) -> None"""
    def ClearSystem(self) -> None:
        """ClearSystem(self: KratosConvectionDiffusionApplication.PureConvectionUtilities3D) -> None"""
    def ConstructSystem(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None:
        """ConstructSystem(self: KratosConvectionDiffusionApplication.PureConvectionUtilities3D, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: Kratos.Array1DVariable3) -> None"""
    def ConvectScalarVar(self, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: Kratos.Array1DVariable3, arg5: Kratos.DoubleVariable, arg6: int) -> None:
        """ConvectScalarVar(self: KratosConvectionDiffusionApplication.PureConvectionUtilities3D, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: Kratos.DoubleVariable, arg3: Kratos.Array1DVariable3, arg4: Kratos.Array1DVariable3, arg5: Kratos.DoubleVariable, arg6: int) -> None"""

class ResidualBasedConvectionDiffusionStrategy(Kratos.ImplicitSolvingStrategy):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: bool, arg3: int, arg4: int) -> None:
        """__init__(self: KratosConvectionDiffusionApplication.ResidualBasedConvectionDiffusionStrategy, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: bool, arg3: int, arg4: int) -> None"""
    def Clear(self) -> None:
        """Clear(self: KratosConvectionDiffusionApplication.ResidualBasedConvectionDiffusionStrategy) -> None"""

class ResidualBasedConvectionDiffusionStrategyNonLinear(Kratos.ImplicitSolvingStrategy):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: bool, arg3: int, arg4: int, arg5: float) -> None:
        """__init__(self: KratosConvectionDiffusionApplication.ResidualBasedConvectionDiffusionStrategyNonLinear, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: bool, arg3: int, arg4: int, arg5: float) -> None"""
    def Clear(self) -> None:
        """Clear(self: KratosConvectionDiffusionApplication.ResidualBasedConvectionDiffusionStrategyNonLinear) -> None"""

class ResidualBasedEulerianConvectionDiffusionStrategy(Kratos.ImplicitSolvingStrategy):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: bool, arg3: int) -> None:
        """__init__(self: KratosConvectionDiffusionApplication.ResidualBasedEulerianConvectionDiffusionStrategy, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: bool, arg3: int) -> None"""
    def Clear(self) -> None:
        """Clear(self: KratosConvectionDiffusionApplication.ResidualBasedEulerianConvectionDiffusionStrategy) -> None"""

class ResidualBasedSemiEulerianConvectionDiffusionStrategy(Kratos.ImplicitSolvingStrategy):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: bool, arg3: int) -> None:
        """__init__(self: KratosConvectionDiffusionApplication.ResidualBasedSemiEulerianConvectionDiffusionStrategy, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: bool, arg3: int) -> None"""
    def Clear(self) -> None:
        """Clear(self: KratosConvectionDiffusionApplication.ResidualBasedSemiEulerianConvectionDiffusionStrategy) -> None"""
