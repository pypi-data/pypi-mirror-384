import Kratos
from typing import overload

class AdjointLinearStrainEnergyResponseFunction(Kratos.AdjointResponseFunction):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.AdjointLinearStrainEnergyResponseFunction, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class AdjointLocalStressResponseFunction(Kratos.AdjointResponseFunction):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.AdjointLocalStressResponseFunction, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class AdjointMaxStressResponseFunction(Kratos.AdjointResponseFunction):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.AdjointMaxStressResponseFunction, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class AdjointNodalDisplacementResponseFunction(Kratos.AdjointResponseFunction):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.AdjointNodalDisplacementResponseFunction, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class AdjointNodalReactionResponseFunction(Kratos.AdjointResponseFunction):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.AdjointNodalReactionResponseFunction, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class BeamConstitutiveLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.BeamConstitutiveLaw) -> None"""

class ComputeCenterOfGravityProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.ComputeCenterOfGravityProcess, arg0: Kratos.ModelPart) -> None"""

class ComputeMassMomentOfInertiaProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Point, arg2: Kratos.Point) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.ComputeMassMomentOfInertiaProcess, arg0: Kratos.ModelPart, arg1: Kratos.Point, arg2: Kratos.Point) -> None"""

class DistributeLoadOnSurfaceProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.DistributeLoadOnSurfaceProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class EigenfrequencyResponseFunctionUtility:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.EigenfrequencyResponseFunctionUtility, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""
    def CalculateGradient(self) -> None:
        """CalculateGradient(self: KratosStructuralMechanicsApplication.EigenfrequencyResponseFunctionUtility) -> None"""
    def CalculateValue(self) -> float:
        """CalculateValue(self: KratosStructuralMechanicsApplication.EigenfrequencyResponseFunctionUtility) -> float"""
    def Initialize(self) -> None:
        """Initialize(self: KratosStructuralMechanicsApplication.EigenfrequencyResponseFunctionUtility) -> None"""

class EigensolverDynamicScheme(Kratos.Scheme):
    def __init__(self) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.EigensolverDynamicScheme) -> None"""

class EigensolverStrategy(Kratos.ImplicitSolvingStrategy):
    def __init__(self, model_part: Kratos.ModelPart, scheme: Kratos.Scheme, builder_and_solver: Kratos.BuilderAndSolver, mass_matrix_diagonal_value: float, stiffness_matrix_diagonal_value: float, compute_modal_decomposition: bool = ...) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.EigensolverStrategy, model_part: Kratos.ModelPart, scheme: Kratos.Scheme, builder_and_solver: Kratos.BuilderAndSolver, mass_matrix_diagonal_value: float, stiffness_matrix_diagonal_value: float, compute_modal_decomposition: bool = False) -> None"""

class ErrorMeshCriteria(Kratos.ConvergenceCriteria):
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.ErrorMeshCriteria, arg0: Kratos.Parameters) -> None"""

class ExplicitCentralDifferencesScheme(Kratos.Scheme):
    @overload
    def __init__(self, arg0: float, arg1: float, arg2: float) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosStructuralMechanicsApplication.ExplicitCentralDifferencesScheme, arg0: float, arg1: float, arg2: float) -> None

        2. __init__(self: KratosStructuralMechanicsApplication.ExplicitCentralDifferencesScheme, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosStructuralMechanicsApplication.ExplicitCentralDifferencesScheme, arg0: float, arg1: float, arg2: float) -> None

        2. __init__(self: KratosStructuralMechanicsApplication.ExplicitCentralDifferencesScheme, arg0: Kratos.Parameters) -> None
        """

class ExplicitMultiStageKimScheme(Kratos.Scheme):
    @overload
    def __init__(self, arg0: float) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosStructuralMechanicsApplication.ExplicitMultiStageKimScheme, arg0: float) -> None

        2. __init__(self: KratosStructuralMechanicsApplication.ExplicitMultiStageKimScheme, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosStructuralMechanicsApplication.ExplicitMultiStageKimScheme, arg0: float) -> None

        2. __init__(self: KratosStructuralMechanicsApplication.ExplicitMultiStageKimScheme, arg0: Kratos.Parameters) -> None
        """

class FormfindingStrategy(Kratos.ResidualBasedNewtonRaphsonStrategy):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.ConvergenceCriteria, arg3: Kratos.BuilderAndSolver, arg4: Kratos.ModelPart, arg5: bool, arg6: str, arg7: Kratos.Parameters, arg8: int, arg9: bool, arg10: bool, arg11: bool) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.FormfindingStrategy, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.ConvergenceCriteria, arg3: Kratos.BuilderAndSolver, arg4: Kratos.ModelPart, arg5: bool, arg6: str, arg7: Kratos.Parameters, arg8: int, arg9: bool, arg10: bool, arg11: bool) -> None"""
    @staticmethod
    def WriteFormFoundMdpa(arg0: Kratos.ModelPart) -> None:
        """WriteFormFoundMdpa(arg0: Kratos.ModelPart) -> None"""

class HarmonicAnalysisStrategy(Kratos.ImplicitSolvingStrategy):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.BuilderAndSolver, arg3: bool) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.HarmonicAnalysisStrategy, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.BuilderAndSolver, arg3: bool) -> None"""
    def GetUseMaterialDampingFlag(self) -> bool:
        """GetUseMaterialDampingFlag(self: KratosStructuralMechanicsApplication.HarmonicAnalysisStrategy) -> bool"""
    def SetUseMaterialDampingFlag(self, arg0: bool) -> None:
        """SetUseMaterialDampingFlag(self: KratosStructuralMechanicsApplication.HarmonicAnalysisStrategy, arg0: bool) -> None"""

class ImposeRigidMovementProcess(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosStructuralMechanicsApplication.ImposeRigidMovementProcess, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosStructuralMechanicsApplication.ImposeRigidMovementProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosStructuralMechanicsApplication.ImposeRigidMovementProcess, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosStructuralMechanicsApplication.ImposeRigidMovementProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """

class ImposeZStrainProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.ImposeZStrainProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class KratosStructuralMechanicsApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.KratosStructuralMechanicsApplication) -> None"""

class LinearElastic3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.LinearElastic3DLaw) -> None"""

class LinearElasticAxisym2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.LinearElasticAxisym2DLaw) -> None"""

class LinearElasticPlaneStrain2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.LinearElasticPlaneStrain2DLaw) -> None"""

class LinearElasticPlaneStress2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.LinearElasticPlaneStress2DLaw) -> None"""

class LinkConstraint(Kratos.MasterSlaveConstraint):
    """A constraint enforcing the distance between two nodes to remain constant."""
    def __init__(self, Id: int, FirstNode: Kratos.Node, SecondNode: Kratos.Node, Dimensions: int, IsMeshMoved: bool) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.LinkConstraint, Id: int, FirstNode: Kratos.Node, SecondNode: Kratos.Node, Dimensions: int, IsMeshMoved: bool) -> None"""

class MassResponseFunctionUtility:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.MassResponseFunctionUtility, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""
    def CalculateGradient(self) -> None:
        """CalculateGradient(self: KratosStructuralMechanicsApplication.MassResponseFunctionUtility) -> None"""
    def CalculateValue(self) -> float:
        """CalculateValue(self: KratosStructuralMechanicsApplication.MassResponseFunctionUtility) -> float"""
    def Initialize(self) -> None:
        """Initialize(self: KratosStructuralMechanicsApplication.MassResponseFunctionUtility) -> None"""

class MechanicalExplicitStrategy(Kratos.ImplicitSolvingStrategy):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: bool, arg3: bool, arg4: bool) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.MechanicalExplicitStrategy, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: bool, arg3: bool, arg4: bool) -> None"""
    def GetInitializePerformedFlag(self) -> bool:
        """GetInitializePerformedFlag(self: KratosStructuralMechanicsApplication.MechanicalExplicitStrategy) -> bool"""
    def SetInitializePerformedFlag(self, arg0: bool) -> None:
        """SetInitializePerformedFlag(self: KratosStructuralMechanicsApplication.MechanicalExplicitStrategy, arg0: bool) -> None"""

class PerturbGeometrySparseUtility:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.PerturbGeometrySparseUtility, arg0: Kratos.ModelPart, arg1: Kratos.LinearSolver, arg2: Kratos.Parameters) -> None"""
    def ApplyRandomFieldVectorsToGeometry(self, arg0: Kratos.ModelPart, arg1: list[float]) -> None:
        """ApplyRandomFieldVectorsToGeometry(self: KratosStructuralMechanicsApplication.PerturbGeometrySparseUtility, arg0: Kratos.ModelPart, arg1: list[float]) -> None"""
    def CreateRandomFieldVectors(self) -> int:
        """CreateRandomFieldVectors(self: KratosStructuralMechanicsApplication.PerturbGeometrySparseUtility) -> int"""

class PerturbGeometrySubgridUtility:
    def __init__(self, *args, **kwargs) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.PerturbGeometrySubgridUtility, arg0: Kratos.ModelPart, arg1: Kratos::LinearSolver<Kratos::UblasSpace<double, boost::numeric::ublas::matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::UblasSpace<double, boost::numeric::ublas::matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::Reorderer<Kratos::UblasSpace<double, boost::numeric::ublas::matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > >, Kratos::UblasSpace<double, boost::numeric::ublas::matrix<double, boost::numeric::ublas::basic_row_major<unsigned long, long>, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > >, boost::numeric::ublas::vector<double, boost::numeric::ublas::unbounded_array<double, std::allocator<double> > > > > >, arg2: Kratos.Parameters) -> None"""
    def ApplyRandomFieldVectorsToGeometry(self, arg0: Kratos.ModelPart, arg1: list[float]) -> None:
        """ApplyRandomFieldVectorsToGeometry(self: KratosStructuralMechanicsApplication.PerturbGeometrySubgridUtility, arg0: Kratos.ModelPart, arg1: list[float]) -> None"""
    def CreateRandomFieldVectors(self) -> int:
        """CreateRandomFieldVectors(self: KratosStructuralMechanicsApplication.PerturbGeometrySubgridUtility) -> int"""

class PostprocessEigenvaluesProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.PostprocessEigenvaluesProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class PrebucklingStrategy(Kratos.ImplicitSolvingStrategy):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.BuilderAndSolver, arg3: Kratos.BuilderAndSolver, arg4: Kratos.ConvergenceCriteria, arg5: int, arg6: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.PrebucklingStrategy, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.BuilderAndSolver, arg3: Kratos.BuilderAndSolver, arg4: Kratos.ConvergenceCriteria, arg5: int, arg6: Kratos.Parameters) -> None"""
    def GetSolutionFoundFlag(self) -> bool:
        """GetSolutionFoundFlag(self: KratosStructuralMechanicsApplication.PrebucklingStrategy) -> bool"""

class PrismNeighboursProcess(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosStructuralMechanicsApplication.PrismNeighboursProcess, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosStructuralMechanicsApplication.PrismNeighboursProcess, arg0: Kratos.ModelPart, arg1: bool) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: bool) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosStructuralMechanicsApplication.PrismNeighboursProcess, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosStructuralMechanicsApplication.PrismNeighboursProcess, arg0: Kratos.ModelPart, arg1: bool) -> None
        """

class ProjectVectorOnSurfaceUtility:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    @staticmethod
    def Execute(arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """Execute(arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class QuadrilateralShellToSolidShellProcess(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosStructuralMechanicsApplication.QuadrilateralShellToSolidShellProcess, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosStructuralMechanicsApplication.QuadrilateralShellToSolidShellProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosStructuralMechanicsApplication.QuadrilateralShellToSolidShellProcess, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosStructuralMechanicsApplication.QuadrilateralShellToSolidShellProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """

class ReplaceMultipleElementsAndConditionsProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.ReplaceMultipleElementsAndConditionsProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class ResidualBasedRelaxationScheme(Kratos.Scheme):
    def __init__(self, arg0: float, arg1: float) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.ResidualBasedRelaxationScheme, arg0: float, arg1: float) -> None"""
    def Initialize(self, arg0: Kratos.ModelPart) -> None:
        """Initialize(self: KratosStructuralMechanicsApplication.ResidualBasedRelaxationScheme, arg0: Kratos.ModelPart) -> None"""

class ResidualDisplacementAndOtherDoFCriteria(Kratos.ConvergenceCriteria):
    @overload
    def __init__(self, arg0: float, arg1: float, arg2: str) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosStructuralMechanicsApplication.ResidualDisplacementAndOtherDoFCriteria, arg0: float, arg1: float, arg2: str) -> None

        2. __init__(self: KratosStructuralMechanicsApplication.ResidualDisplacementAndOtherDoFCriteria, arg0: float, arg1: float) -> None
        """
    @overload
    def __init__(self, arg0: float, arg1: float) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosStructuralMechanicsApplication.ResidualDisplacementAndOtherDoFCriteria, arg0: float, arg1: float, arg2: str) -> None

        2. __init__(self: KratosStructuralMechanicsApplication.ResidualDisplacementAndOtherDoFCriteria, arg0: float, arg1: float) -> None
        """

class SPRErrorProcess2D(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosStructuralMechanicsApplication.SPRErrorProcess2D, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosStructuralMechanicsApplication.SPRErrorProcess2D, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosStructuralMechanicsApplication.SPRErrorProcess2D, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosStructuralMechanicsApplication.SPRErrorProcess2D, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """

class SPRErrorProcess3D(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosStructuralMechanicsApplication.SPRErrorProcess3D, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosStructuralMechanicsApplication.SPRErrorProcess3D, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosStructuralMechanicsApplication.SPRErrorProcess3D, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosStructuralMechanicsApplication.SPRErrorProcess3D, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """

class SetAutomatedInitialVariableProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.SetAutomatedInitialVariableProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class SetCartesianLocalAxesProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.SetCartesianLocalAxesProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class SetCylindricalLocalAxesProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.SetCylindricalLocalAxesProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class SetMovingLoadProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.SetMovingLoadProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class SetSphericalLocalAxesProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.SetSphericalLocalAxesProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class ShellCrossSectionVariable(Kratos.VariableData):
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class SolidShellThickComputeProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.SolidShellThickComputeProcess, arg0: Kratos.ModelPart) -> None"""

class StrainEnergyResponseFunctionUtility:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.StrainEnergyResponseFunctionUtility, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""
    def CalculateGradient(self) -> None:
        """CalculateGradient(self: KratosStructuralMechanicsApplication.StrainEnergyResponseFunctionUtility) -> None"""
    def CalculateValue(self) -> float:
        """CalculateValue(self: KratosStructuralMechanicsApplication.StrainEnergyResponseFunctionUtility) -> float"""
    def Initialize(self) -> None:
        """Initialize(self: KratosStructuralMechanicsApplication.StrainEnergyResponseFunctionUtility) -> None"""

class StructuralMechanicsBossakScheme(Kratos.ResidualBasedBossakDisplacementScheme):
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.StructuralMechanicsBossakScheme, arg0: Kratos.Parameters) -> None"""

class StructuralMechanicsStaticScheme(Kratos.ResidualBasedIncrementalUpdateStaticScheme):
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.StructuralMechanicsStaticScheme, arg0: Kratos.Parameters) -> None"""

class TimoshenkoBeamElasticConstitutiveLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.TimoshenkoBeamElasticConstitutiveLaw) -> None"""

class TimoshenkoBeamPlaneStrainElasticConstitutiveLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.TimoshenkoBeamPlaneStrainElasticConstitutiveLaw) -> None"""

class TotalStructuralMassProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.TotalStructuralMassProcess, arg0: Kratos.ModelPart) -> None"""
    @staticmethod
    def CalculateElementMass(arg0: Kratos.Element, arg1: int) -> float:
        """CalculateElementMass(arg0: Kratos.Element, arg1: int) -> float"""

class TriangleShellToSolidShellProcess(Kratos.Process):
    @overload
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosStructuralMechanicsApplication.TriangleShellToSolidShellProcess, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosStructuralMechanicsApplication.TriangleShellToSolidShellProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosStructuralMechanicsApplication.TriangleShellToSolidShellProcess, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosStructuralMechanicsApplication.TriangleShellToSolidShellProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None
        """

class TrussConstitutiveLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.TrussConstitutiveLaw) -> None"""

class UserProvidedLinearElastic2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.UserProvidedLinearElastic2DLaw) -> None"""

class UserProvidedLinearElastic3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosStructuralMechanicsApplication.UserProvidedLinearElastic3DLaw) -> None"""

def CalculateDeltaTime(arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> float:
    """CalculateDeltaTime(arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> float"""
def ComputeDampingCoefficients(arg0: Kratos.Parameters) -> Kratos.Vector:
    """ComputeDampingCoefficients(arg0: Kratos.Parameters) -> Kratos.Vector"""
