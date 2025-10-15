import Kratos
from typing import overload

class ApplyPerturbationFunctionToScalar(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Node, arg2: Kratos.DoubleVariable, arg3: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosShallowWaterApplication.ApplyPerturbationFunctionToScalar, arg0: Kratos.ModelPart, arg1: Kratos.Node, arg2: Kratos.DoubleVariable, arg3: Kratos.Parameters) -> None

        2. __init__(self: KratosShallowWaterApplication.ApplyPerturbationFunctionToScalar, arg0: Kratos.ModelPart, arg1: Kratos.NodesArray, arg2: Kratos.DoubleVariable, arg3: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.NodesArray, arg2: Kratos.DoubleVariable, arg3: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosShallowWaterApplication.ApplyPerturbationFunctionToScalar, arg0: Kratos.ModelPart, arg1: Kratos.Node, arg2: Kratos.DoubleVariable, arg3: Kratos.Parameters) -> None

        2. __init__(self: KratosShallowWaterApplication.ApplyPerturbationFunctionToScalar, arg0: Kratos.ModelPart, arg1: Kratos.NodesArray, arg2: Kratos.DoubleVariable, arg3: Kratos.Parameters) -> None
        """

class ApplySinusoidalFunctionToScalar(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosShallowWaterApplication.ApplySinusoidalFunctionToScalar, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Parameters) -> None"""

class ApplySinusoidalFunctionToVector(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosShallowWaterApplication.ApplySinusoidalFunctionToVector, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Parameters) -> None"""

class CalculateDistanceToBoundaryProcess(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosShallowWaterApplication.CalculateDistanceToBoundaryProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosShallowWaterApplication.CalculateDistanceToBoundaryProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: float) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: float) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosShallowWaterApplication.CalculateDistanceToBoundaryProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None

        2. __init__(self: KratosShallowWaterApplication.CalculateDistanceToBoundaryProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: float) -> None
        """

class DepthIntegrationProcess2D(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosShallowWaterApplication.DepthIntegrationProcess2D, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class DepthIntegrationProcess3D(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosShallowWaterApplication.DepthIntegrationProcess3D, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class DerivativesRecoveryUtility2D:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    @staticmethod
    def CalculatePolynomialWeights(arg0: Kratos.ModelPart) -> None:
        """CalculatePolynomialWeights(arg0: Kratos.ModelPart) -> None"""
    @staticmethod
    def Check(arg0: Kratos.ModelPart) -> None:
        """Check(arg0: Kratos.ModelPart) -> None"""
    @staticmethod
    def RecoverDivergence(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.DoubleVariable, arg3: int) -> None:
        """RecoverDivergence(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.DoubleVariable, arg3: int) -> None"""
    @staticmethod
    def RecoverGradient(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: int) -> None:
        """RecoverGradient(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: int) -> None"""
    @overload
    @staticmethod
    def RecoverLaplacian(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: int) -> None:
        """RecoverLaplacian(*args, **kwargs)
        Overloaded function.

        1. RecoverLaplacian(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: int) -> None

        2. RecoverLaplacian(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3, arg3: int) -> None
        """
    @overload
    @staticmethod
    def RecoverLaplacian(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3, arg3: int) -> None:
        """RecoverLaplacian(*args, **kwargs)
        Overloaded function.

        1. RecoverLaplacian(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: int) -> None

        2. RecoverLaplacian(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3, arg3: int) -> None
        """

class DerivativesRecoveryUtility3D:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    @staticmethod
    def CalculatePolynomialWeights(arg0: Kratos.ModelPart) -> None:
        """CalculatePolynomialWeights(arg0: Kratos.ModelPart) -> None"""
    @staticmethod
    def Check(arg0: Kratos.ModelPart) -> None:
        """Check(arg0: Kratos.ModelPart) -> None"""
    @staticmethod
    def RecoverDivergence(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.DoubleVariable, arg3: int) -> None:
        """RecoverDivergence(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.DoubleVariable, arg3: int) -> None"""
    @staticmethod
    def RecoverGradient(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: int) -> None:
        """RecoverGradient(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Array1DVariable3, arg3: int) -> None"""
    @overload
    @staticmethod
    def RecoverLaplacian(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: int) -> None:
        """RecoverLaplacian(*args, **kwargs)
        Overloaded function.

        1. RecoverLaplacian(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: int) -> None

        2. RecoverLaplacian(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3, arg3: int) -> None
        """
    @overload
    @staticmethod
    def RecoverLaplacian(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3, arg3: int) -> None:
        """RecoverLaplacian(*args, **kwargs)
        Overloaded function.

        1. RecoverLaplacian(arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.DoubleVariable, arg3: int) -> None

        2. RecoverLaplacian(arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: Kratos.Array1DVariable3, arg3: int) -> None
        """

class EstimateTimeStepUtility:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosShallowWaterApplication.EstimateTimeStepUtility, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""
    def Execute(self) -> float:
        """Execute(self: KratosShallowWaterApplication.EstimateTimeStepUtility) -> float"""

class FluxCorrectedShallowWaterScheme(Kratos.Scheme):
    @overload
    def __init__(self, arg0: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosShallowWaterApplication.FluxCorrectedShallowWaterScheme, arg0: int) -> None

        2. __init__(self: KratosShallowWaterApplication.FluxCorrectedShallowWaterScheme, arg0: int, arg1: bool) -> None

        3. __init__(self: KratosShallowWaterApplication.FluxCorrectedShallowWaterScheme, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: int, arg1: bool) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosShallowWaterApplication.FluxCorrectedShallowWaterScheme, arg0: int) -> None

        2. __init__(self: KratosShallowWaterApplication.FluxCorrectedShallowWaterScheme, arg0: int, arg1: bool) -> None

        3. __init__(self: KratosShallowWaterApplication.FluxCorrectedShallowWaterScheme, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosShallowWaterApplication.FluxCorrectedShallowWaterScheme, arg0: int) -> None

        2. __init__(self: KratosShallowWaterApplication.FluxCorrectedShallowWaterScheme, arg0: int, arg1: bool) -> None

        3. __init__(self: KratosShallowWaterApplication.FluxCorrectedShallowWaterScheme, arg0: Kratos.Parameters) -> None
        """

class InterpolateSwToPfemUtility:
    def __init__(self) -> None:
        """__init__(self: KratosShallowWaterApplication.InterpolateSwToPfemUtility) -> None"""
    def InterpolateVariables(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """InterpolateVariables(self: KratosShallowWaterApplication.InterpolateSwToPfemUtility, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""

class KratosShallowWaterApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosShallowWaterApplication.KratosShallowWaterApplication) -> None"""

class MeshMovingModeler(Kratos.Modeler):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosShallowWaterApplication.MeshMovingModeler) -> None

        2. __init__(self: KratosShallowWaterApplication.MeshMovingModeler, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosShallowWaterApplication.MeshMovingModeler) -> None

        2. __init__(self: KratosShallowWaterApplication.MeshMovingModeler, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None
        """

class MoveShallowMeshUtility:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosShallowWaterApplication.MoveShallowMeshUtility, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None"""
    def Check(self) -> int:
        """Check(self: KratosShallowWaterApplication.MoveShallowMeshUtility) -> int"""
    def Initialize(self) -> None:
        """Initialize(self: KratosShallowWaterApplication.MoveShallowMeshUtility) -> None"""
    def MapResults(self) -> None:
        """MapResults(self: KratosShallowWaterApplication.MoveShallowMeshUtility) -> None"""
    def MoveMesh(self) -> None:
        """MoveMesh(self: KratosShallowWaterApplication.MoveShallowMeshUtility) -> None"""

class ResidualBasedAdamsMoultonScheme(Kratos.Scheme):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosShallowWaterApplication.ResidualBasedAdamsMoultonScheme) -> None

        2. __init__(self: KratosShallowWaterApplication.ResidualBasedAdamsMoultonScheme, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosShallowWaterApplication.ResidualBasedAdamsMoultonScheme) -> None

        2. __init__(self: KratosShallowWaterApplication.ResidualBasedAdamsMoultonScheme, arg0: Kratos.Parameters) -> None
        """

class ShallowWaterResidualBasedBDFScheme(Kratos.Scheme):
    @overload
    def __init__(self, arg0: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosShallowWaterApplication.ShallowWaterResidualBasedBDFScheme, arg0: int) -> None

        2. __init__(self: KratosShallowWaterApplication.ShallowWaterResidualBasedBDFScheme, arg0: int, arg1: bool) -> None

        3. __init__(self: KratosShallowWaterApplication.ShallowWaterResidualBasedBDFScheme, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: int, arg1: bool) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosShallowWaterApplication.ShallowWaterResidualBasedBDFScheme, arg0: int) -> None

        2. __init__(self: KratosShallowWaterApplication.ShallowWaterResidualBasedBDFScheme, arg0: int, arg1: bool) -> None

        3. __init__(self: KratosShallowWaterApplication.ShallowWaterResidualBasedBDFScheme, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosShallowWaterApplication.ShallowWaterResidualBasedBDFScheme, arg0: int) -> None

        2. __init__(self: KratosShallowWaterApplication.ShallowWaterResidualBasedBDFScheme, arg0: int, arg1: bool) -> None

        3. __init__(self: KratosShallowWaterApplication.ShallowWaterResidualBasedBDFScheme, arg0: Kratos.Parameters) -> None
        """

class ShallowWaterUtilities:
    def __init__(self) -> None:
        """__init__(self: KratosShallowWaterApplication.ShallowWaterUtilities) -> None"""
    def ComputeEnergy(self, arg0: Kratos.ModelPart) -> None:
        """ComputeEnergy(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart) -> None"""
    def ComputeEnergyNonHistorical(self, arg0: Kratos.ModelPart) -> None:
        """ComputeEnergyNonHistorical(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart) -> None"""
    def ComputeFreeSurfaceElevation(self, arg0: Kratos.ModelPart) -> None:
        """ComputeFreeSurfaceElevation(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart) -> None"""
    def ComputeFroude(self, arg0: Kratos.ModelPart, arg1: float) -> None:
        """ComputeFroude(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart, arg1: float) -> None"""
    def ComputeFroudeNonHistorical(self, arg0: Kratos.ModelPart, arg1: float) -> None:
        """ComputeFroudeNonHistorical(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart, arg1: float) -> None"""
    def ComputeHeightFromFreeSurface(self, arg0: Kratos.ModelPart) -> None:
        """ComputeHeightFromFreeSurface(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart) -> None"""
    @overload
    def ComputeHydrostaticForces(self, arg0: Kratos.ElementsArray, arg1: Kratos.ProcessInfo) -> Kratos.Array3:
        """ComputeHydrostaticForces(*args, **kwargs)
        Overloaded function.

        1. ComputeHydrostaticForces(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray, arg1: Kratos.ProcessInfo) -> Kratos.Array3

        2. ComputeHydrostaticForces(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray, arg1: Kratos.ProcessInfo, arg2: float) -> Kratos.Array3

        3. ComputeHydrostaticForces(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray, arg1: Kratos.ProcessInfo) -> Kratos.Array3

        4. ComputeHydrostaticForces(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray, arg1: Kratos.ProcessInfo, arg2: float) -> Kratos.Array3
        """
    @overload
    def ComputeHydrostaticForces(self, arg0: Kratos.ElementsArray, arg1: Kratos.ProcessInfo, arg2: float) -> Kratos.Array3:
        """ComputeHydrostaticForces(*args, **kwargs)
        Overloaded function.

        1. ComputeHydrostaticForces(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray, arg1: Kratos.ProcessInfo) -> Kratos.Array3

        2. ComputeHydrostaticForces(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray, arg1: Kratos.ProcessInfo, arg2: float) -> Kratos.Array3

        3. ComputeHydrostaticForces(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray, arg1: Kratos.ProcessInfo) -> Kratos.Array3

        4. ComputeHydrostaticForces(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray, arg1: Kratos.ProcessInfo, arg2: float) -> Kratos.Array3
        """
    @overload
    def ComputeHydrostaticForces(self, arg0: Kratos.ConditionsArray, arg1: Kratos.ProcessInfo) -> Kratos.Array3:
        """ComputeHydrostaticForces(*args, **kwargs)
        Overloaded function.

        1. ComputeHydrostaticForces(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray, arg1: Kratos.ProcessInfo) -> Kratos.Array3

        2. ComputeHydrostaticForces(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray, arg1: Kratos.ProcessInfo, arg2: float) -> Kratos.Array3

        3. ComputeHydrostaticForces(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray, arg1: Kratos.ProcessInfo) -> Kratos.Array3

        4. ComputeHydrostaticForces(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray, arg1: Kratos.ProcessInfo, arg2: float) -> Kratos.Array3
        """
    @overload
    def ComputeHydrostaticForces(self, arg0: Kratos.ConditionsArray, arg1: Kratos.ProcessInfo, arg2: float) -> Kratos.Array3:
        """ComputeHydrostaticForces(*args, **kwargs)
        Overloaded function.

        1. ComputeHydrostaticForces(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray, arg1: Kratos.ProcessInfo) -> Kratos.Array3

        2. ComputeHydrostaticForces(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray, arg1: Kratos.ProcessInfo, arg2: float) -> Kratos.Array3

        3. ComputeHydrostaticForces(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray, arg1: Kratos.ProcessInfo) -> Kratos.Array3

        4. ComputeHydrostaticForces(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray, arg1: Kratos.ProcessInfo, arg2: float) -> Kratos.Array3
        """
    @overload
    def ComputeL2Norm(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float:
        """ComputeL2Norm(*args, **kwargs)
        Overloaded function.

        1. ComputeL2Norm(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float

        2. ComputeL2Norm(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Point, arg3: Kratos.Point) -> float
        """
    @overload
    def ComputeL2Norm(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Point, arg3: Kratos.Point) -> float:
        """ComputeL2Norm(*args, **kwargs)
        Overloaded function.

        1. ComputeL2Norm(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float

        2. ComputeL2Norm(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Point, arg3: Kratos.Point) -> float
        """
    @overload
    def ComputeL2NormNonHistorical(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float:
        """ComputeL2NormNonHistorical(*args, **kwargs)
        Overloaded function.

        1. ComputeL2NormNonHistorical(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float

        2. ComputeL2NormNonHistorical(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Point, arg3: Kratos.Point) -> float
        """
    @overload
    def ComputeL2NormNonHistorical(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Point, arg3: Kratos.Point) -> float:
        """ComputeL2NormNonHistorical(*args, **kwargs)
        Overloaded function.

        1. ComputeL2NormNonHistorical(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float

        2. ComputeL2NormNonHistorical(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: Kratos.Point, arg3: Kratos.Point) -> float
        """
    def ComputeMomentum(self, arg0: Kratos.ModelPart) -> None:
        """ComputeMomentum(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart) -> None"""
    def ComputeVelocity(self, arg0: Kratos.ModelPart, arg1: bool) -> None:
        """ComputeVelocity(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart, arg1: bool) -> None"""
    @overload
    def CopyVariableToPreviousTimeStep(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None:
        """CopyVariableToPreviousTimeStep(*args, **kwargs)
        Overloaded function.

        1. CopyVariableToPreviousTimeStep(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

        2. CopyVariableToPreviousTimeStep(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None
        """
    @overload
    def CopyVariableToPreviousTimeStep(self, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None:
        """CopyVariableToPreviousTimeStep(*args, **kwargs)
        Overloaded function.

        1. CopyVariableToPreviousTimeStep(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None

        2. CopyVariableToPreviousTimeStep(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None
        """
    def FlipScalarVariable(self, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable, arg2: Kratos.ModelPart) -> None:
        """FlipScalarVariable(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.DoubleVariable, arg1: Kratos.DoubleVariable, arg2: Kratos.ModelPart) -> None"""
    def IdentifySolidBoundary(self, arg0: Kratos.ModelPart, arg1: float, arg2: Kratos.Flags) -> None:
        """IdentifySolidBoundary(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart, arg1: float, arg2: Kratos.Flags) -> None"""
    def NormalizeVector(self, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None:
        """NormalizeVector(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3) -> None"""
    @overload
    def OffsetIds(self, arg0: Kratos.NodesArray) -> None:
        """OffsetIds(*args, **kwargs)
        Overloaded function.

        1. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.NodesArray) -> None

        2. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray) -> None

        3. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray) -> None

        4. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.PropertiesArray) -> None

        5. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.NodesArray, arg1: float) -> None

        6. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray, arg1: float) -> None

        7. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray, arg1: float) -> None

        8. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.PropertiesArray, arg1: float) -> None
        """
    @overload
    def OffsetIds(self, arg0: Kratos.ElementsArray) -> None:
        """OffsetIds(*args, **kwargs)
        Overloaded function.

        1. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.NodesArray) -> None

        2. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray) -> None

        3. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray) -> None

        4. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.PropertiesArray) -> None

        5. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.NodesArray, arg1: float) -> None

        6. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray, arg1: float) -> None

        7. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray, arg1: float) -> None

        8. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.PropertiesArray, arg1: float) -> None
        """
    @overload
    def OffsetIds(self, arg0: Kratos.ConditionsArray) -> None:
        """OffsetIds(*args, **kwargs)
        Overloaded function.

        1. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.NodesArray) -> None

        2. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray) -> None

        3. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray) -> None

        4. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.PropertiesArray) -> None

        5. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.NodesArray, arg1: float) -> None

        6. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray, arg1: float) -> None

        7. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray, arg1: float) -> None

        8. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.PropertiesArray, arg1: float) -> None
        """
    @overload
    def OffsetIds(self, arg0: Kratos.PropertiesArray) -> None:
        """OffsetIds(*args, **kwargs)
        Overloaded function.

        1. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.NodesArray) -> None

        2. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray) -> None

        3. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray) -> None

        4. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.PropertiesArray) -> None

        5. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.NodesArray, arg1: float) -> None

        6. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray, arg1: float) -> None

        7. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray, arg1: float) -> None

        8. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.PropertiesArray, arg1: float) -> None
        """
    @overload
    def OffsetIds(self, arg0: Kratos.NodesArray, arg1: float) -> None:
        """OffsetIds(*args, **kwargs)
        Overloaded function.

        1. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.NodesArray) -> None

        2. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray) -> None

        3. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray) -> None

        4. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.PropertiesArray) -> None

        5. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.NodesArray, arg1: float) -> None

        6. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray, arg1: float) -> None

        7. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray, arg1: float) -> None

        8. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.PropertiesArray, arg1: float) -> None
        """
    @overload
    def OffsetIds(self, arg0: Kratos.ElementsArray, arg1: float) -> None:
        """OffsetIds(*args, **kwargs)
        Overloaded function.

        1. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.NodesArray) -> None

        2. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray) -> None

        3. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray) -> None

        4. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.PropertiesArray) -> None

        5. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.NodesArray, arg1: float) -> None

        6. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray, arg1: float) -> None

        7. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray, arg1: float) -> None

        8. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.PropertiesArray, arg1: float) -> None
        """
    @overload
    def OffsetIds(self, arg0: Kratos.ConditionsArray, arg1: float) -> None:
        """OffsetIds(*args, **kwargs)
        Overloaded function.

        1. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.NodesArray) -> None

        2. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray) -> None

        3. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray) -> None

        4. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.PropertiesArray) -> None

        5. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.NodesArray, arg1: float) -> None

        6. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray, arg1: float) -> None

        7. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray, arg1: float) -> None

        8. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.PropertiesArray, arg1: float) -> None
        """
    @overload
    def OffsetIds(self, arg0: Kratos.PropertiesArray, arg1: float) -> None:
        """OffsetIds(*args, **kwargs)
        Overloaded function.

        1. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.NodesArray) -> None

        2. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray) -> None

        3. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray) -> None

        4. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.PropertiesArray) -> None

        5. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.NodesArray, arg1: float) -> None

        6. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ElementsArray, arg1: float) -> None

        7. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ConditionsArray, arg1: float) -> None

        8. OffsetIds(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.PropertiesArray, arg1: float) -> None
        """
    def OffsetMeshZCoordinate(self, arg0: Kratos.ModelPart, arg1: float) -> None:
        """OffsetMeshZCoordinate(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart, arg1: float) -> None"""
    def SetMeshZ0CoordinateToZero(self, arg0: Kratos.ModelPart) -> None:
        """SetMeshZ0CoordinateToZero(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart) -> None"""
    def SetMeshZCoordinate(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None:
        """SetMeshZCoordinate(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None"""
    def SetMeshZCoordinateToZero(self, arg0: Kratos.ModelPart) -> None:
        """SetMeshZCoordinateToZero(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart) -> None"""
    def SetMinimumValue(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float) -> None:
        """SetMinimumValue(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float) -> None"""
    @overload
    def SmoothHistoricalVariable(self, arg0: Kratos.DoubleVariable, arg1: Kratos.NodesArray, arg2: float, arg3: float) -> None:
        """SmoothHistoricalVariable(*args, **kwargs)
        Overloaded function.

        1. SmoothHistoricalVariable(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.DoubleVariable, arg1: Kratos.NodesArray, arg2: float, arg3: float) -> None

        2. SmoothHistoricalVariable(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.Array1DVariable3, arg1: Kratos.NodesArray, arg2: float, arg3: float) -> None
        """
    @overload
    def SmoothHistoricalVariable(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.NodesArray, arg2: float, arg3: float) -> None:
        """SmoothHistoricalVariable(*args, **kwargs)
        Overloaded function.

        1. SmoothHistoricalVariable(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.DoubleVariable, arg1: Kratos.NodesArray, arg2: float, arg3: float) -> None

        2. SmoothHistoricalVariable(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.Array1DVariable3, arg1: Kratos.NodesArray, arg2: float, arg3: float) -> None
        """
    def StoreNonHistoricalGiDNoDataIfDry(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None:
        """StoreNonHistoricalGiDNoDataIfDry(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> None"""
    def SwapY0Z0Coordinates(self, arg0: Kratos.ModelPart) -> None:
        """SwapY0Z0Coordinates(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart) -> None"""
    def SwapYZComponents(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.NodesArray) -> None:
        """SwapYZComponents(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.Array1DVariable3, arg1: Kratos.NodesArray) -> None"""
    @overload
    def SwapYZComponentsNonHistorical(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.NodesArray) -> None:
        """SwapYZComponentsNonHistorical(*args, **kwargs)
        Overloaded function.

        1. SwapYZComponentsNonHistorical(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.Array1DVariable3, arg1: Kratos.NodesArray) -> None

        2. SwapYZComponentsNonHistorical(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.Array1DVariable3, arg1: Kratos.ElementsArray) -> None

        3. SwapYZComponentsNonHistorical(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.Array1DVariable3, arg1: Kratos.ConditionsArray) -> None
        """
    @overload
    def SwapYZComponentsNonHistorical(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.ElementsArray) -> None:
        """SwapYZComponentsNonHistorical(*args, **kwargs)
        Overloaded function.

        1. SwapYZComponentsNonHistorical(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.Array1DVariable3, arg1: Kratos.NodesArray) -> None

        2. SwapYZComponentsNonHistorical(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.Array1DVariable3, arg1: Kratos.ElementsArray) -> None

        3. SwapYZComponentsNonHistorical(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.Array1DVariable3, arg1: Kratos.ConditionsArray) -> None
        """
    @overload
    def SwapYZComponentsNonHistorical(self, arg0: Kratos.Array1DVariable3, arg1: Kratos.ConditionsArray) -> None:
        """SwapYZComponentsNonHistorical(*args, **kwargs)
        Overloaded function.

        1. SwapYZComponentsNonHistorical(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.Array1DVariable3, arg1: Kratos.NodesArray) -> None

        2. SwapYZComponentsNonHistorical(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.Array1DVariable3, arg1: Kratos.ElementsArray) -> None

        3. SwapYZComponentsNonHistorical(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.Array1DVariable3, arg1: Kratos.ConditionsArray) -> None
        """
    def SwapYZCoordinates(self, arg0: Kratos.ModelPart) -> None:
        """SwapYZCoordinates(self: KratosShallowWaterApplication.ShallowWaterUtilities, arg0: Kratos.ModelPart) -> None"""

class WriteFromSwAtInterfaceProcess2D(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosShallowWaterApplication.WriteFromSwAtInterfaceProcess2D, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class WriteFromSwAtInterfaceProcess3D(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosShallowWaterApplication.WriteFromSwAtInterfaceProcess3D, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""
