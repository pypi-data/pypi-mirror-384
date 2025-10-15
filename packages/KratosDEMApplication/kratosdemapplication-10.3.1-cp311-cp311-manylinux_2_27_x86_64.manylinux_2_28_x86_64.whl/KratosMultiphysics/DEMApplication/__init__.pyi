import Kratos
from typing import overload

DEM_BEAM_CONSTITUTIVE_LAW_POINTER: DEMBeamConstitutiveLawPointerVariable
DEM_CONTINUUM_CONSTITUTIVE_LAW_POINTER: DEMContinuumConstitutiveLawPointerVariable
DEM_DISCONTINUUM_CONSTITUTIVE_LAW_POINTER: DEMDiscontinuumConstitutiveLawPointerVariable
DEM_GLOBAL_DAMPING_MODEL_POINTER: DEMGlobalDampingModelPointerVariable
DEM_ROLLING_FRICTION_MODEL_POINTER: DEMRollingFrictionModelPointerVariable
DEM_ROTATIONAL_INTEGRATION_SCHEME_POINTER: DEMIntegrationSchemePointerVariable
DEM_TRANSLATIONAL_INTEGRATION_SCHEME_POINTER: DEMIntegrationSchemePointerVariable

class AnalyticFaceWatcher:
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosDEMApplication.AnalyticFaceWatcher, arg0: Kratos.ModelPart) -> None"""
    def ClearData(self) -> None:
        """ClearData(self: KratosDEMApplication.AnalyticFaceWatcher) -> None"""
    def GetTotalFlux(self, arg0: list, arg1: list, arg2: list, arg3: list, arg4: list) -> None:
        """GetTotalFlux(self: KratosDEMApplication.AnalyticFaceWatcher, arg0: list, arg1: list, arg2: list, arg3: list, arg4: list) -> None"""
    def MakeMeasurements(self) -> None:
        """MakeMeasurements(self: KratosDEMApplication.AnalyticFaceWatcher) -> None"""

class AnalyticModelPartFiller:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.AnalyticModelPartFiller) -> None"""
    def FillAnalyticModelPartGivenFractionOfParticlesToTransform(self, fraction_of_particles_to_convert: float, spheres_model_part: Kratos.ModelPart, particle_creator_destructor: ParticleCreatorDestructor, analytic_sub_model_part_name: str = ...) -> None:
        """FillAnalyticModelPartGivenFractionOfParticlesToTransform(self: KratosDEMApplication.AnalyticModelPartFiller, fraction_of_particles_to_convert: float, spheres_model_part: Kratos.ModelPart, particle_creator_destructor: KratosDEMApplication.ParticleCreatorDestructor, analytic_sub_model_part_name: str = '') -> None"""

class AnalyticParticleWatcher:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.AnalyticParticleWatcher) -> None"""
    def MakeMeasurements(self, arg0: Kratos.ModelPart) -> None:
        """MakeMeasurements(self: KratosDEMApplication.AnalyticParticleWatcher, arg0: Kratos.ModelPart) -> None"""
    def SetNodalMaxFaceImpactVelocities(self, arg0: Kratos.ModelPart) -> None:
        """SetNodalMaxFaceImpactVelocities(self: KratosDEMApplication.AnalyticParticleWatcher, arg0: Kratos.ModelPart) -> None"""
    def SetNodalMaxImpactVelocities(self, arg0: Kratos.ModelPart) -> None:
        """SetNodalMaxImpactVelocities(self: KratosDEMApplication.AnalyticParticleWatcher, arg0: Kratos.ModelPart) -> None"""

class AnalyticWatcher:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.AnalyticWatcher) -> None"""

class ApplyForcesAndMomentsProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDEMApplication.ApplyForcesAndMomentsProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class ApplyKinematicConstraintsProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDEMApplication.ApplyKinematicConstraintsProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class AutomaticDTProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDEMApplication.AutomaticDTProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class AuxiliaryUtilities:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.AuxiliaryUtilities) -> None"""
    def ComputeAverageZStressFor2D(self, arg0: Kratos.ModelPart) -> float:
        """ComputeAverageZStressFor2D(self: KratosDEMApplication.AuxiliaryUtilities, arg0: Kratos.ModelPart) -> float"""
    def UpdateTimeInOneModelPart(self, arg0: Kratos.ModelPart, arg1: float, arg2: float, arg3: bool) -> None:
        """UpdateTimeInOneModelPart(self: KratosDEMApplication.AuxiliaryUtilities, arg0: Kratos.ModelPart, arg1: float, arg2: float, arg3: bool) -> None"""

class ContactElementGlobalPhysicsCalculator:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.ContactElementGlobalPhysicsCalculator) -> None"""
    def CalculateAveragedCoordinationNumberWithinSphere(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: float, arg3: Kratos.Array3) -> float:
        """CalculateAveragedCoordinationNumberWithinSphere(self: KratosDEMApplication.ContactElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: float, arg3: Kratos.Array3) -> float"""
    def CalculateFabricTensorWithinSphere(self, arg0: Kratos.ModelPart, arg1: float, arg2: Kratos.Array3) -> list[list[float]]:
        """CalculateFabricTensorWithinSphere(self: KratosDEMApplication.ContactElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart, arg1: float, arg2: Kratos.Array3) -> list[list[float]]"""
    def CalculateTotalStressTensor(self, arg0: Kratos.ModelPart, arg1: float, arg2: float, arg3: float) -> list[list[float]]:
        """CalculateTotalStressTensor(self: KratosDEMApplication.ContactElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart, arg1: float, arg2: float, arg3: float) -> list[list[float]]"""
    def CalculateTotalStressTensorWithinCubic(self, arg0: Kratos.ModelPart, arg1: float, arg2: Kratos.Array3, arg3: float, arg4: float, arg5: float) -> list[list[float]]:
        """CalculateTotalStressTensorWithinCubic(self: KratosDEMApplication.ContactElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart, arg1: float, arg2: Kratos.Array3, arg3: float, arg4: float, arg5: float) -> list[list[float]]"""
    def CalculateTotalStressTensorWithinSphere(self, arg0: Kratos.ModelPart, arg1: float, arg2: Kratos.Array3, arg3: float, arg4: float, arg5: float) -> list[list[float]]:
        """CalculateTotalStressTensorWithinSphere(self: KratosDEMApplication.ContactElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart, arg1: float, arg2: Kratos.Array3, arg3: float, arg4: float, arg5: float) -> list[list[float]]"""
    def CalculateUnbalancedForceWithinSphere(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: float, arg3: Kratos.Array3) -> float:
        """CalculateUnbalancedForceWithinSphere(self: KratosDEMApplication.ContactElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: float, arg3: Kratos.Array3) -> float"""

class ContinuumExplicitSolverStrategy(ExplicitSolverStrategy):
    def __init__(self, arg0: ExplicitSolverSettings, arg1: float, arg2: int, arg3: float, arg4: int, arg5, arg6, arg7: Kratos.SpatialSearch, arg8: Kratos.Parameters) -> None:
        """__init__(self: KratosDEMApplication.ContinuumExplicitSolverStrategy, arg0: KratosDEMApplication.ExplicitSolverSettings, arg1: float, arg2: int, arg3: float, arg4: int, arg5: Kratos::ParticleCreatorDestructor, arg6: Kratos::DEM_FEM_Search, arg7: Kratos.SpatialSearch, arg8: Kratos.Parameters) -> None"""
    def BreakAllBonds(self) -> None:
        """BreakAllBonds(self: KratosDEMApplication.ContinuumExplicitSolverStrategy) -> None"""
    def ComputeCoordinationNumber(self, arg0: float) -> float:
        """ComputeCoordinationNumber(self: KratosDEMApplication.ContinuumExplicitSolverStrategy, arg0: float) -> float"""
    def ComputeSkin(self, arg0: Kratos.ModelPart, arg1: float) -> None:
        """ComputeSkin(self: KratosDEMApplication.ContinuumExplicitSolverStrategy, arg0: Kratos.ModelPart, arg1: float) -> None"""
    def HealAllBonds(self) -> None:
        """HealAllBonds(self: KratosDEMApplication.ContinuumExplicitSolverStrategy) -> None"""
    def RebuildListOfContinuumSphericParticles(self) -> None:
        """RebuildListOfContinuumSphericParticles(self: KratosDEMApplication.ContinuumExplicitSolverStrategy) -> None"""

class ContinuumVelocityVerletSolverStrategy(ContinuumExplicitSolverStrategy):
    def __init__(self, arg0: ExplicitSolverSettings, arg1: float, arg2: float, arg3: float, arg4: int, arg5, arg6, arg7: Kratos.SpatialSearch, arg8: Kratos.Parameters) -> None:
        """__init__(self: KratosDEMApplication.ContinuumVelocityVerletSolverStrategy, arg0: KratosDEMApplication.ExplicitSolverSettings, arg1: float, arg2: float, arg3: float, arg4: int, arg5: Kratos::ParticleCreatorDestructor, arg6: Kratos::DEM_FEM_Search, arg7: Kratos.SpatialSearch, arg8: Kratos.Parameters) -> None"""

class ControlModule2DProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDEMApplication.ControlModule2DProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class DEMBeamConstitutiveLaw:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEMBeamConstitutiveLaw) -> None"""
    def CheckRequirementsOfStressTensor(self) -> bool:
        """CheckRequirementsOfStressTensor(self: KratosDEMApplication.DEMBeamConstitutiveLaw) -> bool"""
    def Clone(self) -> DEMBeamConstitutiveLaw:
        """Clone(self: KratosDEMApplication.DEMBeamConstitutiveLaw) -> KratosDEMApplication.DEMBeamConstitutiveLaw"""
    def GetTypeOfLaw(self) -> str:
        """GetTypeOfLaw(self: KratosDEMApplication.DEMBeamConstitutiveLaw) -> str"""
    def SetConstitutiveLawInProperties(self, arg0: Kratos.Properties, arg1: bool) -> None:
        """SetConstitutiveLawInProperties(self: KratosDEMApplication.DEMBeamConstitutiveLaw, arg0: Kratos.Properties, arg1: bool) -> None"""

class DEMBeamConstitutiveLawPointerVariable:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class DEMContinuumConstitutiveLaw:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEMContinuumConstitutiveLaw) -> None"""
    def CheckRequirementsOfStressTensor(self) -> bool:
        """CheckRequirementsOfStressTensor(self: KratosDEMApplication.DEMContinuumConstitutiveLaw) -> bool"""
    def Clone(self) -> DEMContinuumConstitutiveLaw:
        """Clone(self: KratosDEMApplication.DEMContinuumConstitutiveLaw) -> KratosDEMApplication.DEMContinuumConstitutiveLaw"""
    def GetTypeOfLaw(self) -> str:
        """GetTypeOfLaw(self: KratosDEMApplication.DEMContinuumConstitutiveLaw) -> str"""
    def SetConstitutiveLawInProperties(self, arg0: Kratos.Properties, arg1: bool) -> None:
        """SetConstitutiveLawInProperties(self: KratosDEMApplication.DEMContinuumConstitutiveLaw, arg0: Kratos.Properties, arg1: bool) -> None"""
    def SetConstitutiveLawInPropertiesWithParameters(self, arg0: Kratos.Properties, arg1: Kratos.Parameters, arg2: bool) -> None:
        """SetConstitutiveLawInPropertiesWithParameters(self: KratosDEMApplication.DEMContinuumConstitutiveLaw, arg0: Kratos.Properties, arg1: Kratos.Parameters, arg2: bool) -> None"""

class DEMContinuumConstitutiveLawPointerVariable:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class DEMDiscontinuumConstitutiveLaw:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEMDiscontinuumConstitutiveLaw) -> None"""
    def Clone(self) -> DEMDiscontinuumConstitutiveLaw:
        """Clone(self: KratosDEMApplication.DEMDiscontinuumConstitutiveLaw) -> KratosDEMApplication.DEMDiscontinuumConstitutiveLaw"""
    def GetTypeOfLaw(self) -> str:
        """GetTypeOfLaw(self: KratosDEMApplication.DEMDiscontinuumConstitutiveLaw) -> str"""
    def SetConstitutiveLawInProperties(self, arg0: Kratos.Properties, arg1: bool) -> None:
        """SetConstitutiveLawInProperties(self: KratosDEMApplication.DEMDiscontinuumConstitutiveLaw, arg0: Kratos.Properties, arg1: bool) -> None"""

class DEMDiscontinuumConstitutiveLawPointerVariable:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class DEMFEMUtilities:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEMFEMUtilities) -> None"""
    def CreateRigidFacesFromAllElements(self, arg0: Kratos.ModelPart, arg1: Kratos.Properties) -> None:
        """CreateRigidFacesFromAllElements(self: KratosDEMApplication.DEMFEMUtilities, arg0: Kratos.ModelPart, arg1: Kratos.Properties) -> None"""
    def MoveAllMeshes(self, arg0: Kratos.ModelPart, arg1: float, arg2: float) -> None:
        """MoveAllMeshes(self: KratosDEMApplication.DEMFEMUtilities, arg0: Kratos.ModelPart, arg1: float, arg2: float) -> None"""

class DEMGlobalDampingModel:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEMGlobalDampingModel) -> None"""
    def Clone(self) -> DEMGlobalDampingModel:
        """Clone(self: KratosDEMApplication.DEMGlobalDampingModel) -> KratosDEMApplication.DEMGlobalDampingModel"""
    def SetGlobalDampingModelInProperties(self, arg0: Kratos.Properties, arg1: bool) -> None:
        """SetGlobalDampingModelInProperties(self: KratosDEMApplication.DEMGlobalDampingModel, arg0: Kratos.Properties, arg1: bool) -> None"""

class DEMGlobalDampingModelPointerVariable:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class DEMGlobalDampingNonViscousCstForceDir(DEMGlobalDampingModel):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEMGlobalDampingNonViscousCstForceDir) -> None"""

class DEMGlobalDampingNonViscousVarForceDir(DEMGlobalDampingModel):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEMGlobalDampingNonViscousVarForceDir) -> None"""

class DEMGlobalDampingViscous(DEMGlobalDampingModel):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEMGlobalDampingViscous) -> None"""

class DEMIntegrationScheme:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEMIntegrationScheme) -> None"""
    def SetRotationalIntegrationSchemeInProperties(self, arg0: Kratos.Properties, arg1: bool) -> None:
        """SetRotationalIntegrationSchemeInProperties(self: KratosDEMApplication.DEMIntegrationScheme, arg0: Kratos.Properties, arg1: bool) -> None"""
    def SetTranslationalIntegrationSchemeInProperties(self, arg0: Kratos.Properties, arg1: bool) -> None:
        """SetTranslationalIntegrationSchemeInProperties(self: KratosDEMApplication.DEMIntegrationScheme, arg0: Kratos.Properties, arg1: bool) -> None"""

class DEMIntegrationSchemePointerVariable:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class DEMIntegrationSchemeRawPointerVariable:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class DEMRollingFrictionModel:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEMRollingFrictionModel) -> None"""
    def Clone(self) -> DEMRollingFrictionModel:
        """Clone(self: KratosDEMApplication.DEMRollingFrictionModel) -> KratosDEMApplication.DEMRollingFrictionModel"""
    def SetAPrototypeOfThisInProperties(self, arg0: Kratos.Properties, arg1: bool) -> None:
        """SetAPrototypeOfThisInProperties(self: KratosDEMApplication.DEMRollingFrictionModel, arg0: Kratos.Properties, arg1: bool) -> None"""

class DEMRollingFrictionModelBounded(DEMRollingFrictionModel):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEMRollingFrictionModelBounded) -> None"""

class DEMRollingFrictionModelConstantTorque(DEMRollingFrictionModel):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEMRollingFrictionModelConstantTorque) -> None"""

class DEMRollingFrictionModelPointerVariable:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""

class DEMRollingFrictionModelViscousTorque(DEMRollingFrictionModel):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEMRollingFrictionModelViscousTorque) -> None"""

class DEM_D_Bentonite_Colloid(DEMDiscontinuumConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_D_Bentonite_Colloid) -> None"""

class DEM_D_Conical_damage(DEMDiscontinuumConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_D_Conical_damage) -> None"""

class DEM_D_Hertz_confined(DEM_D_Hertz_viscous_Coulomb):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_D_Hertz_confined) -> None"""

class DEM_D_Hertz_viscous_Coulomb(DEMDiscontinuumConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_D_Hertz_viscous_Coulomb) -> None"""

class DEM_D_Hertz_viscous_Coulomb2D(DEM_D_Hertz_viscous_Coulomb):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_D_Hertz_viscous_Coulomb2D) -> None"""

class DEM_D_Hertz_viscous_Coulomb_DMT(DEM_D_Hertz_viscous_Coulomb):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_D_Hertz_viscous_Coulomb_DMT) -> None"""

class DEM_D_Hertz_viscous_Coulomb_JKR(DEM_D_Hertz_viscous_Coulomb):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_D_Hertz_viscous_Coulomb_JKR) -> None"""

class DEM_D_Hertz_viscous_Coulomb_Nestle(DEM_D_Hertz_viscous_Coulomb):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_D_Hertz_viscous_Coulomb_Nestle) -> None"""

class DEM_D_Linear_Custom_Constants(DEM_D_Linear_viscous_Coulomb):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_D_Linear_Custom_Constants) -> None"""

class DEM_D_Linear_HighStiffness(DEMDiscontinuumConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_D_Linear_HighStiffness) -> None"""

class DEM_D_Linear_HighStiffness_2D(DEMDiscontinuumConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_D_Linear_HighStiffness_2D) -> None"""

class DEM_D_Linear_Simple_Coulomb(DEMDiscontinuumConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_D_Linear_Simple_Coulomb) -> None"""

class DEM_D_Linear_classic(DEMDiscontinuumConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_D_Linear_classic) -> None"""

class DEM_D_Linear_confined(DEM_D_Linear_viscous_Coulomb):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_D_Linear_confined) -> None"""

class DEM_D_Linear_viscous_Coulomb(DEMDiscontinuumConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_D_Linear_viscous_Coulomb) -> None"""

class DEM_D_Linear_viscous_Coulomb2D(DEM_D_Linear_viscous_Coulomb):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_D_Linear_viscous_Coulomb2D) -> None"""

class DEM_D_Linear_viscous_Coulomb_DMT(DEM_D_Linear_viscous_Coulomb):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_D_Linear_viscous_Coulomb_DMT) -> None"""

class DEM_D_Linear_viscous_Coulomb_JKR(DEM_D_Linear_viscous_Coulomb):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_D_Linear_viscous_Coulomb_JKR) -> None"""

class DEM_D_Quadratic(DEMDiscontinuumConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_D_Quadratic) -> None"""

class DEM_D_Stress_Dependent_Cohesive(DEMDiscontinuumConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_D_Stress_Dependent_Cohesive) -> None"""

class DEM_D_void(DEMDiscontinuumConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_D_void) -> None"""

class DEM_Dempack(DEMContinuumConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_Dempack) -> None"""

class DEM_Dempack2D(DEM_Dempack):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_Dempack2D) -> None"""

class DEM_Dempack2D_dev(DEM_Dempack_dev):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_Dempack2D_dev) -> None"""

class DEM_Dempack_dev(DEM_Dempack):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_Dempack_dev) -> None"""

class DEM_Dempack_torque(DEM_Dempack):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_Dempack_torque) -> None"""

class DEM_ExponentialHC(DEMContinuumConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_ExponentialHC) -> None"""

class DEM_FEM_Search:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_FEM_Search) -> None"""
    def GetBBHighPoint(self) -> Kratos.Array3:
        """GetBBHighPoint(self: KratosDEMApplication.DEM_FEM_Search) -> Kratos.Array3"""
    def GetBBLowPoint(self) -> Kratos.Array3:
        """GetBBLowPoint(self: KratosDEMApplication.DEM_FEM_Search) -> Kratos.Array3"""

class DEM_Force_Based_Inlet(DEM_Inlet):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.DEM_Force_Based_Inlet, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: int) -> None

        2. __init__(self: KratosDEMApplication.DEM_Force_Based_Inlet, arg0: Kratos.ModelPart, arg1: Kratos.Array3) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Array3) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.DEM_Force_Based_Inlet, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: int) -> None

        2. __init__(self: KratosDEMApplication.DEM_Force_Based_Inlet, arg0: Kratos.ModelPart, arg1: Kratos.Array3) -> None
        """

class DEM_Inlet:
    @overload
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.DEM_Inlet, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosDEMApplication.DEM_Inlet, arg0: Kratos.ModelPart, arg1: int) -> None

        3. __init__(self: KratosDEMApplication.DEM_Inlet, arg0: Kratos.ModelPart, arg1: Kratos.Parameters, arg2: int) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.DEM_Inlet, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosDEMApplication.DEM_Inlet, arg0: Kratos.ModelPart, arg1: int) -> None

        3. __init__(self: KratosDEMApplication.DEM_Inlet, arg0: Kratos.ModelPart, arg1: Kratos.Parameters, arg2: int) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters, arg2: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.DEM_Inlet, arg0: Kratos.ModelPart) -> None

        2. __init__(self: KratosDEMApplication.DEM_Inlet, arg0: Kratos.ModelPart, arg1: int) -> None

        3. __init__(self: KratosDEMApplication.DEM_Inlet, arg0: Kratos.ModelPart, arg1: Kratos.Parameters, arg2: int) -> None
        """
    def CreateElementsFromInletMesh(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: ParticleCreatorDestructor) -> None:
        """CreateElementsFromInletMesh(self: KratosDEMApplication.DEM_Inlet, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: KratosDEMApplication.ParticleCreatorDestructor) -> None"""
    def GetMaxRadius(self, arg0: Kratos.ModelPart) -> float:
        """GetMaxRadius(self: KratosDEMApplication.DEM_Inlet, arg0: Kratos.ModelPart) -> float"""
    def GetTotalMassInjectedSoFar(self) -> float:
        """GetTotalMassInjectedSoFar(self: KratosDEMApplication.DEM_Inlet) -> float"""
    def GetTotalNumberOfParticlesInjectedSoFar(self) -> int:
        """GetTotalNumberOfParticlesInjectedSoFar(self: KratosDEMApplication.DEM_Inlet) -> int"""
    def InitializeDEM_Inlet(self, model_part: Kratos.ModelPart, creator_destructor: ParticleCreatorDestructor, using_strategy_for_continuum: bool = ...) -> None:
        """InitializeDEM_Inlet(self: KratosDEMApplication.DEM_Inlet, model_part: Kratos.ModelPart, creator_destructor: KratosDEMApplication.ParticleCreatorDestructor, using_strategy_for_continuum: bool = False) -> None"""

class DEM_KDEM(DEMContinuumConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_KDEM) -> None"""

class DEM_KDEM2D(DEM_KDEM):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_KDEM2D) -> None"""

class DEM_KDEMFabric(DEM_KDEM):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_KDEMFabric) -> None"""

class DEM_KDEMFabric2D(DEM_KDEM2D):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_KDEMFabric2D) -> None"""

class DEM_KDEM_CamClay(DEM_KDEM_Rankine):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_KDEM_CamClay) -> None"""

class DEM_KDEM_Fissured_Rock(DEM_KDEM_Rankine):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_KDEM_Fissured_Rock) -> None"""

class DEM_KDEM_Mohr_Coulomb(DEM_KDEM_Rankine):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_KDEM_Mohr_Coulomb) -> None"""

class DEM_KDEM_Rankine(DEM_KDEM):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_KDEM_Rankine) -> None"""

class DEM_KDEM_soft_torque(DEM_KDEM):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_KDEM_soft_torque) -> None"""

class DEM_KDEM_soft_torque_with_noise(DEM_KDEM_soft_torque):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_KDEM_soft_torque_with_noise) -> None"""

class DEM_KDEM_with_damage(DEM_KDEM_soft_torque):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_KDEM_with_damage) -> None"""

class DEM_KDEM_with_damage_parallel_bond(DEM_KDEM_with_damage):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_KDEM_with_damage_parallel_bond) -> None"""

class DEM_KDEM_with_damage_parallel_bond_2D(DEM_KDEM_with_damage_parallel_bond):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_KDEM_with_damage_parallel_bond_2D) -> None"""

class DEM_KDEM_with_damage_parallel_bond_Hertz(DEM_KDEM_with_damage_parallel_bond):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_KDEM_with_damage_parallel_bond_Hertz) -> None"""

class DEM_KDEM_with_damage_parallel_bond_Hertz_2D(DEM_KDEM_with_damage_parallel_bond_Hertz):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_KDEM_with_damage_parallel_bond_Hertz_2D) -> None"""

class DEM_KDEM_with_damage_parallel_bond_capped(DEM_KDEM_with_damage_parallel_bond):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_KDEM_with_damage_parallel_bond_capped) -> None"""

class DEM_parallel_bond(DEMContinuumConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_parallel_bond) -> None"""

class DEM_parallel_bond_Hertz(DEM_parallel_bond):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_parallel_bond_Hertz) -> None"""

class DEM_parallel_bond_Linear(DEM_parallel_bond):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_parallel_bond_Linear) -> None"""

class DEM_parallel_bond_Quadratic(DEM_parallel_bond):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_parallel_bond_Quadratic) -> None"""

class DEM_parallel_bond_bilinear_damage(DEM_parallel_bond):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_parallel_bond_bilinear_damage) -> None"""

class DEM_parallel_bond_bilinear_damage_Hertz(DEM_parallel_bond_bilinear_damage):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_parallel_bond_bilinear_damage_Hertz) -> None"""

class DEM_parallel_bond_bilinear_damage_Linear(DEM_parallel_bond_bilinear_damage):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_parallel_bond_bilinear_damage_Linear) -> None"""

class DEM_parallel_bond_bilinear_damage_Quadratic(DEM_parallel_bond_bilinear_damage):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_parallel_bond_bilinear_damage_Quadratic) -> None"""

class DEM_parallel_bond_bilinear_damage_mixed(DEM_parallel_bond):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_parallel_bond_bilinear_damage_mixed) -> None"""

class DEM_parallel_bond_bilinear_damage_mixed_Hertz(DEM_parallel_bond_bilinear_damage_mixed):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_parallel_bond_bilinear_damage_mixed_Hertz) -> None"""

class DEM_parallel_bond_bilinear_damage_mixed_Linear(DEM_parallel_bond_bilinear_damage_mixed):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_parallel_bond_bilinear_damage_mixed_Linear) -> None"""

class DEM_parallel_bond_bilinear_damage_mixed_Quadratic(DEM_parallel_bond_bilinear_damage_mixed):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_parallel_bond_bilinear_damage_mixed_Quadratic) -> None"""

class DEM_parallel_bond_for_membrane(DEM_parallel_bond):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_parallel_bond_for_membrane) -> None"""

class DEM_smooth_joint(DEMContinuumConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DEM_smooth_joint) -> None"""

class DemSearchUtilities:
    def __init__(self, arg0: Kratos.SpatialSearch) -> None:
        """__init__(self: KratosDEMApplication.DemSearchUtilities, arg0: Kratos.SpatialSearch) -> None"""
    @overload
    def SearchNodeNeighboursDistances(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: float, arg3: Kratos.DoubleVariable) -> None:
        """SearchNodeNeighboursDistances(*args, **kwargs)
        Overloaded function.

        1. SearchNodeNeighboursDistances(self: KratosDEMApplication.DemSearchUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: float, arg3: Kratos.DoubleVariable) -> None

        2. SearchNodeNeighboursDistances(self: KratosDEMApplication.DemSearchUtilities, arg0: Kratos.NodesArray, arg1: Kratos.ModelPart, arg2: float, arg3: Kratos.DoubleVariable) -> None

        3. SearchNodeNeighboursDistances(self: KratosDEMApplication.DemSearchUtilities, arg0: Kratos.ModelPart, arg1: Kratos.NodesArray, arg2: float, arg3: Kratos.DoubleVariable) -> None

        4. SearchNodeNeighboursDistances(self: KratosDEMApplication.DemSearchUtilities, arg0: Kratos.NodesArray, arg1: Kratos.NodesArray, arg2: float, arg3: Kratos.DoubleVariable) -> None
        """
    @overload
    def SearchNodeNeighboursDistances(self, arg0: Kratos.NodesArray, arg1: Kratos.ModelPart, arg2: float, arg3: Kratos.DoubleVariable) -> None:
        """SearchNodeNeighboursDistances(*args, **kwargs)
        Overloaded function.

        1. SearchNodeNeighboursDistances(self: KratosDEMApplication.DemSearchUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: float, arg3: Kratos.DoubleVariable) -> None

        2. SearchNodeNeighboursDistances(self: KratosDEMApplication.DemSearchUtilities, arg0: Kratos.NodesArray, arg1: Kratos.ModelPart, arg2: float, arg3: Kratos.DoubleVariable) -> None

        3. SearchNodeNeighboursDistances(self: KratosDEMApplication.DemSearchUtilities, arg0: Kratos.ModelPart, arg1: Kratos.NodesArray, arg2: float, arg3: Kratos.DoubleVariable) -> None

        4. SearchNodeNeighboursDistances(self: KratosDEMApplication.DemSearchUtilities, arg0: Kratos.NodesArray, arg1: Kratos.NodesArray, arg2: float, arg3: Kratos.DoubleVariable) -> None
        """
    @overload
    def SearchNodeNeighboursDistances(self, arg0: Kratos.ModelPart, arg1: Kratos.NodesArray, arg2: float, arg3: Kratos.DoubleVariable) -> None:
        """SearchNodeNeighboursDistances(*args, **kwargs)
        Overloaded function.

        1. SearchNodeNeighboursDistances(self: KratosDEMApplication.DemSearchUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: float, arg3: Kratos.DoubleVariable) -> None

        2. SearchNodeNeighboursDistances(self: KratosDEMApplication.DemSearchUtilities, arg0: Kratos.NodesArray, arg1: Kratos.ModelPart, arg2: float, arg3: Kratos.DoubleVariable) -> None

        3. SearchNodeNeighboursDistances(self: KratosDEMApplication.DemSearchUtilities, arg0: Kratos.ModelPart, arg1: Kratos.NodesArray, arg2: float, arg3: Kratos.DoubleVariable) -> None

        4. SearchNodeNeighboursDistances(self: KratosDEMApplication.DemSearchUtilities, arg0: Kratos.NodesArray, arg1: Kratos.NodesArray, arg2: float, arg3: Kratos.DoubleVariable) -> None
        """
    @overload
    def SearchNodeNeighboursDistances(self, arg0: Kratos.NodesArray, arg1: Kratos.NodesArray, arg2: float, arg3: Kratos.DoubleVariable) -> None:
        """SearchNodeNeighboursDistances(*args, **kwargs)
        Overloaded function.

        1. SearchNodeNeighboursDistances(self: KratosDEMApplication.DemSearchUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: float, arg3: Kratos.DoubleVariable) -> None

        2. SearchNodeNeighboursDistances(self: KratosDEMApplication.DemSearchUtilities, arg0: Kratos.NodesArray, arg1: Kratos.ModelPart, arg2: float, arg3: Kratos.DoubleVariable) -> None

        3. SearchNodeNeighboursDistances(self: KratosDEMApplication.DemSearchUtilities, arg0: Kratos.ModelPart, arg1: Kratos.NodesArray, arg2: float, arg3: Kratos.DoubleVariable) -> None

        4. SearchNodeNeighboursDistances(self: KratosDEMApplication.DemSearchUtilities, arg0: Kratos.NodesArray, arg1: Kratos.NodesArray, arg2: float, arg3: Kratos.DoubleVariable) -> None
        """

class DiscreteRandomVariable(RandomVariable):
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.DiscreteRandomVariable, arg0: Kratos.Parameters) -> None

        2. __init__(self: KratosDEMApplication.DiscreteRandomVariable, arg0: Kratos.Parameters, arg1: int) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters, arg1: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.DiscreteRandomVariable, arg0: Kratos.Parameters) -> None

        2. __init__(self: KratosDEMApplication.DiscreteRandomVariable, arg0: Kratos.Parameters, arg1: int) -> None
        """
    def GetMean(self) -> float:
        """GetMean(self: KratosDEMApplication.DiscreteRandomVariable) -> float"""
    def ProbabilityDensity(self, arg0: float) -> float:
        """ProbabilityDensity(self: KratosDEMApplication.DiscreteRandomVariable, arg0: float) -> float"""
    def Sample(self) -> float:
        """Sample(self: KratosDEMApplication.DiscreteRandomVariable) -> float"""

class DoubleList:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.DoubleList) -> None"""

class ExcavatorUtility:
    def __init__(self, arg0: Kratos.ModelPart, arg1: float, arg2: float, arg3: float, arg4: float, arg5: float, arg6: float, arg7: float, arg8: float, arg9: float, arg10: float, arg11: float, arg12: float, arg13: float) -> None:
        """__init__(self: KratosDEMApplication.ExcavatorUtility, arg0: Kratos.ModelPart, arg1: float, arg2: float, arg3: float, arg4: float, arg5: float, arg6: float, arg7: float, arg8: float, arg9: float, arg10: float, arg11: float, arg12: float, arg13: float) -> None"""
    def ExecuteInitializeSolutionStep(self) -> None:
        """ExecuteInitializeSolutionStep(self: KratosDEMApplication.ExcavatorUtility) -> None"""

class ExplicitSolverSettings:
    cluster_model_part: Kratos.ModelPart
    contact_model_part: Kratos.ModelPart
    fem_model_part: Kratos.ModelPart
    inlet_model_part: Kratos.ModelPart
    r_model_part: Kratos.ModelPart
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.ExplicitSolverSettings) -> None"""

class ExplicitSolverStrategy:
    def __init__(self, arg0: ExplicitSolverSettings, arg1: float, arg2: int, arg3: float, arg4: int, arg5, arg6, arg7: Kratos.SpatialSearch, arg8: Kratos.Parameters) -> None:
        """__init__(self: KratosDEMApplication.ExplicitSolverStrategy, arg0: KratosDEMApplication.ExplicitSolverSettings, arg1: float, arg2: int, arg3: float, arg4: int, arg5: Kratos::ParticleCreatorDestructor, arg6: Kratos::DEM_FEM_Search, arg7: Kratos.SpatialSearch, arg8: Kratos.Parameters) -> None"""
    def AttachSpheresToStickyWalls(self) -> None:
        """AttachSpheresToStickyWalls(self: KratosDEMApplication.ExplicitSolverStrategy) -> None"""
    def ComputeCoordinationNumber(self, arg0: float) -> float:
        """ComputeCoordinationNumber(self: KratosDEMApplication.ExplicitSolverStrategy, arg0: float) -> float"""
    def FinalizeSolutionStep(self) -> None:
        """FinalizeSolutionStep(self: KratosDEMApplication.ExplicitSolverStrategy) -> None"""
    def Initialize(self) -> None:
        """Initialize(self: KratosDEMApplication.ExplicitSolverStrategy) -> None"""
    def InitializeSolutionStep(self) -> None:
        """InitializeSolutionStep(self: KratosDEMApplication.ExplicitSolverStrategy) -> None"""
    def PrepareContactElementsForPrinting(self) -> None:
        """PrepareContactElementsForPrinting(self: KratosDEMApplication.ExplicitSolverStrategy) -> None"""
    def PrepareElementsForPrinting(self) -> None:
        """PrepareElementsForPrinting(self: KratosDEMApplication.ExplicitSolverStrategy) -> None"""
    def RebuildListOfDiscontinuumSphericParticles(self) -> None:
        """RebuildListOfDiscontinuumSphericParticles(self: KratosDEMApplication.ExplicitSolverStrategy) -> None"""
    def ResetPrescribedMotionFlagsRespectingImposedDofs(self) -> None:
        """ResetPrescribedMotionFlagsRespectingImposedDofs(self: KratosDEMApplication.ExplicitSolverStrategy) -> None"""
    def SearchDemNeighbours(self, arg0: Kratos.ModelPart, arg1: bool) -> None:
        """SearchDemNeighbours(self: KratosDEMApplication.ExplicitSolverStrategy, arg0: Kratos.ModelPart, arg1: bool) -> None"""
    def SearchFemNeighbours(self, arg0: Kratos.ModelPart, arg1: bool) -> None:
        """SearchFemNeighbours(self: KratosDEMApplication.ExplicitSolverStrategy, arg0: Kratos.ModelPart, arg1: bool) -> None"""
    def SetNormalRadiiOnAllParticles(self, arg0: Kratos.ModelPart) -> None:
        """SetNormalRadiiOnAllParticles(self: KratosDEMApplication.ExplicitSolverStrategy, arg0: Kratos.ModelPart) -> None"""
    def SetNormalRadiiOnAllParticlesBeforeInitilization(self, arg0: Kratos.ModelPart) -> None:
        """SetNormalRadiiOnAllParticlesBeforeInitilization(self: KratosDEMApplication.ExplicitSolverStrategy, arg0: Kratos.ModelPart) -> None"""
    def SetSearchRadiiOnAllParticles(self, arg0: Kratos.ModelPart, arg1: float, arg2: float) -> None:
        """SetSearchRadiiOnAllParticles(self: KratosDEMApplication.ExplicitSolverStrategy, arg0: Kratos.ModelPart, arg1: float, arg2: float) -> None"""
    def SetSearchRadiiWithFemOnAllParticles(self, arg0: Kratos.ModelPart, arg1: float, arg2: float) -> None:
        """SetSearchRadiiWithFemOnAllParticles(self: KratosDEMApplication.ExplicitSolverStrategy, arg0: Kratos.ModelPart, arg1: float, arg2: float) -> None"""
    def SolveSolutionStep(self) -> float:
        """SolveSolutionStep(self: KratosDEMApplication.ExplicitSolverStrategy) -> float"""

class Fast_Filling_Creator:
    @overload
    def __init__(self, arg0: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.Fast_Filling_Creator, arg0: int) -> None

        2. __init__(self: KratosDEMApplication.Fast_Filling_Creator, arg0: Kratos.Parameters, arg1: int) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters, arg1: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.Fast_Filling_Creator, arg0: int) -> None

        2. __init__(self: KratosDEMApplication.Fast_Filling_Creator, arg0: Kratos.Parameters, arg1: int) -> None
        """
    def CheckHasIndentationOrNot(self, arg0: float, arg1: float, arg2: float, arg3: float, arg4: float, arg5: float, arg6: float, arg7: float) -> bool:
        """CheckHasIndentationOrNot(self: KratosDEMApplication.Fast_Filling_Creator, arg0: float, arg1: float, arg2: float, arg3: float, arg4: float, arg5: float, arg6: float, arg7: float) -> bool"""
    def GetRandomParticleRadius(self, creator_destructor: ParticleCreatorDestructor) -> float:
        """GetRandomParticleRadius(self: KratosDEMApplication.Fast_Filling_Creator, creator_destructor: KratosDEMApplication.ParticleCreatorDestructor) -> float"""

class ForwardEulerScheme(DEMIntegrationScheme):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.ForwardEulerScheme) -> None"""

class IntList:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.IntList) -> None"""

class IterativeSolverStrategy(ExplicitSolverStrategy):
    def __init__(self, arg0: ExplicitSolverSettings, arg1: float, arg2: float, arg3: float, arg4: int, arg5, arg6, arg7: Kratos.SpatialSearch, arg8: Kratos.Parameters) -> None:
        """__init__(self: KratosDEMApplication.IterativeSolverStrategy, arg0: KratosDEMApplication.ExplicitSolverSettings, arg1: float, arg2: float, arg3: float, arg4: int, arg5: Kratos::ParticleCreatorDestructor, arg6: Kratos::DEM_FEM_Search, arg7: Kratos.SpatialSearch, arg8: Kratos.Parameters) -> None"""

class KratosDEMApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.KratosDEMApplication) -> None"""

class MoveMeshUtility:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.MoveMeshUtility) -> None"""
    def MoveDemMesh(self, arg0: Kratos.NodesArray, arg1: bool) -> None:
        """MoveDemMesh(self: KratosDEMApplication.MoveMeshUtility, arg0: Kratos.NodesArray, arg1: bool) -> None"""

class MultiaxialControlModuleGeneralized2DUtilities:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosDEMApplication.MultiaxialControlModuleGeneralized2DUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None"""
    def ExecuteFinalizeSolutionStep(self) -> None:
        """ExecuteFinalizeSolutionStep(self: KratosDEMApplication.MultiaxialControlModuleGeneralized2DUtilities) -> None"""
    def ExecuteInitialize(self) -> None:
        """ExecuteInitialize(self: KratosDEMApplication.MultiaxialControlModuleGeneralized2DUtilities) -> None"""
    def ExecuteInitializeSolutionStep(self) -> None:
        """ExecuteInitializeSolutionStep(self: KratosDEMApplication.MultiaxialControlModuleGeneralized2DUtilities) -> None"""

class OMP_DEMSearch(Kratos.SpatialSearch):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.OMP_DEMSearch) -> None

        2. __init__(self: KratosDEMApplication.OMP_DEMSearch, min_x: float, min_y: float, min_z: float, max_x: float, max_y: float, max_z: float) -> None
        """
    @overload
    def __init__(self, min_x: float, min_y: float, min_z: float, max_x: float, max_y: float, max_z: float) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.OMP_DEMSearch) -> None

        2. __init__(self: KratosDEMApplication.OMP_DEMSearch, min_x: float, min_y: float, min_z: float, max_x: float, max_y: float, max_z: float) -> None
        """
    def SearchNodesInRadiusExclusive(self, arg0: Kratos.NodesArray, arg1: Kratos.NodesArray, arg2: list, arg3: VectorResultNodesContainer, arg4: VectorDistances, arg5: list, arg6: list) -> None:
        """SearchNodesInRadiusExclusive(self: KratosDEMApplication.OMP_DEMSearch, arg0: Kratos.NodesArray, arg1: Kratos.NodesArray, arg2: list, arg3: KratosDEMApplication.VectorResultNodesContainer, arg4: KratosDEMApplication.VectorDistances, arg5: list, arg6: list) -> None"""

class ParallelBondUtilities:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.ParallelBondUtilities) -> None"""
    def SetCurrentIndentationAsAReferenceInParallelBonds(self, arg0: Kratos.ModelPart) -> None:
        """SetCurrentIndentationAsAReferenceInParallelBonds(self: KratosDEMApplication.ParallelBondUtilities, arg0: Kratos.ModelPart) -> None"""
    def SetCurrentIndentationAsAReferenceInParallelBondsForPBM(self, arg0: Kratos.ModelPart) -> None:
        """SetCurrentIndentationAsAReferenceInParallelBondsForPBM(self: KratosDEMApplication.ParallelBondUtilities, arg0: Kratos.ModelPart) -> None"""

class ParticleCreatorDestructor:
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.ParticleCreatorDestructor) -> None

        2. __init__(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.Parameters) -> None

        3. __init__(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos::AnalyticWatcher) -> None

        4. __init__(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos::AnalyticWatcher, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.ParticleCreatorDestructor) -> None

        2. __init__(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.Parameters) -> None

        3. __init__(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos::AnalyticWatcher) -> None

        4. __init__(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos::AnalyticWatcher, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.ParticleCreatorDestructor) -> None

        2. __init__(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.Parameters) -> None

        3. __init__(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos::AnalyticWatcher) -> None

        4. __init__(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos::AnalyticWatcher, arg1: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0, arg1: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.ParticleCreatorDestructor) -> None

        2. __init__(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.Parameters) -> None

        3. __init__(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos::AnalyticWatcher) -> None

        4. __init__(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos::AnalyticWatcher, arg1: Kratos.Parameters) -> None
        """
    def CalculateSurroundingBoundingBox(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart, arg3: Kratos.ModelPart, arg4: float, arg5: bool) -> None:
        """CalculateSurroundingBoundingBox(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart, arg3: Kratos.ModelPart, arg4: float, arg5: bool) -> None"""
    @overload
    def CreateSphericParticle(self, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Array3, arg3: Kratos.Properties, arg4: float, arg5: Kratos.Element) -> Kratos.Element:
        """CreateSphericParticle(*args, **kwargs)
        Overloaded function.

        1. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Array3, arg3: Kratos.Properties, arg4: float, arg5: Kratos.Element) -> Kratos.Element

        2. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Node, arg3: Kratos.Properties, arg4: float, arg5: Kratos.Element) -> Kratos.Element

        3. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Node, arg3: Kratos.Properties, arg4: float, arg5: str) -> Kratos.Element

        4. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.Node, arg2: Kratos.Properties, arg3: float, arg4: str) -> Kratos.Element

        5. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Array3, arg3: Kratos.Properties, arg4: float, arg5: str) -> Kratos.Element

        6. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: Kratos.Properties, arg3: float, arg4: str) -> Kratos.Element
        """
    @overload
    def CreateSphericParticle(self, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Node, arg3: Kratos.Properties, arg4: float, arg5: Kratos.Element) -> Kratos.Element:
        """CreateSphericParticle(*args, **kwargs)
        Overloaded function.

        1. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Array3, arg3: Kratos.Properties, arg4: float, arg5: Kratos.Element) -> Kratos.Element

        2. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Node, arg3: Kratos.Properties, arg4: float, arg5: Kratos.Element) -> Kratos.Element

        3. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Node, arg3: Kratos.Properties, arg4: float, arg5: str) -> Kratos.Element

        4. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.Node, arg2: Kratos.Properties, arg3: float, arg4: str) -> Kratos.Element

        5. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Array3, arg3: Kratos.Properties, arg4: float, arg5: str) -> Kratos.Element

        6. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: Kratos.Properties, arg3: float, arg4: str) -> Kratos.Element
        """
    @overload
    def CreateSphericParticle(self, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Node, arg3: Kratos.Properties, arg4: float, arg5: str) -> Kratos.Element:
        """CreateSphericParticle(*args, **kwargs)
        Overloaded function.

        1. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Array3, arg3: Kratos.Properties, arg4: float, arg5: Kratos.Element) -> Kratos.Element

        2. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Node, arg3: Kratos.Properties, arg4: float, arg5: Kratos.Element) -> Kratos.Element

        3. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Node, arg3: Kratos.Properties, arg4: float, arg5: str) -> Kratos.Element

        4. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.Node, arg2: Kratos.Properties, arg3: float, arg4: str) -> Kratos.Element

        5. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Array3, arg3: Kratos.Properties, arg4: float, arg5: str) -> Kratos.Element

        6. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: Kratos.Properties, arg3: float, arg4: str) -> Kratos.Element
        """
    @overload
    def CreateSphericParticle(self, arg0: Kratos.ModelPart, arg1: Kratos.Node, arg2: Kratos.Properties, arg3: float, arg4: str) -> Kratos.Element:
        """CreateSphericParticle(*args, **kwargs)
        Overloaded function.

        1. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Array3, arg3: Kratos.Properties, arg4: float, arg5: Kratos.Element) -> Kratos.Element

        2. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Node, arg3: Kratos.Properties, arg4: float, arg5: Kratos.Element) -> Kratos.Element

        3. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Node, arg3: Kratos.Properties, arg4: float, arg5: str) -> Kratos.Element

        4. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.Node, arg2: Kratos.Properties, arg3: float, arg4: str) -> Kratos.Element

        5. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Array3, arg3: Kratos.Properties, arg4: float, arg5: str) -> Kratos.Element

        6. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: Kratos.Properties, arg3: float, arg4: str) -> Kratos.Element
        """
    @overload
    def CreateSphericParticle(self, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Array3, arg3: Kratos.Properties, arg4: float, arg5: str) -> Kratos.Element:
        """CreateSphericParticle(*args, **kwargs)
        Overloaded function.

        1. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Array3, arg3: Kratos.Properties, arg4: float, arg5: Kratos.Element) -> Kratos.Element

        2. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Node, arg3: Kratos.Properties, arg4: float, arg5: Kratos.Element) -> Kratos.Element

        3. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Node, arg3: Kratos.Properties, arg4: float, arg5: str) -> Kratos.Element

        4. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.Node, arg2: Kratos.Properties, arg3: float, arg4: str) -> Kratos.Element

        5. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Array3, arg3: Kratos.Properties, arg4: float, arg5: str) -> Kratos.Element

        6. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: Kratos.Properties, arg3: float, arg4: str) -> Kratos.Element
        """
    @overload
    def CreateSphericParticle(self, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: Kratos.Properties, arg3: float, arg4: str) -> Kratos.Element:
        """CreateSphericParticle(*args, **kwargs)
        Overloaded function.

        1. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Array3, arg3: Kratos.Properties, arg4: float, arg5: Kratos.Element) -> Kratos.Element

        2. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Node, arg3: Kratos.Properties, arg4: float, arg5: Kratos.Element) -> Kratos.Element

        3. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Node, arg3: Kratos.Properties, arg4: float, arg5: str) -> Kratos.Element

        4. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.Node, arg2: Kratos.Properties, arg3: float, arg4: str) -> Kratos.Element

        5. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int, arg2: Kratos.Array3, arg3: Kratos.Properties, arg4: float, arg5: str) -> Kratos.Element

        6. CreateSphericParticle(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: Kratos.Properties, arg3: float, arg4: str) -> Kratos.Element
        """
    def DestroyContactElements(self, arg0: Kratos.ModelPart) -> None:
        """DestroyContactElements(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart) -> None"""
    def DestroyContactElementsOutsideBoundingBox(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """DestroyContactElementsOutsideBoundingBox(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
    def DestroyMarkedParticles(self, arg0: Kratos.ModelPart) -> None:
        """DestroyMarkedParticles(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart) -> None"""
    @overload
    def DestroyParticlesOutsideBoundingBox(self, arg0: Kratos.ModelPart) -> None:
        """DestroyParticlesOutsideBoundingBox(*args, **kwargs)
        Overloaded function.

        1. DestroyParticlesOutsideBoundingBox(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart) -> None

        2. DestroyParticlesOutsideBoundingBox(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart) -> None
        """
    @overload
    def DestroyParticlesOutsideBoundingBox(self, arg0: Kratos.ModelPart) -> None:
        """DestroyParticlesOutsideBoundingBox(*args, **kwargs)
        Overloaded function.

        1. DestroyParticlesOutsideBoundingBox(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart) -> None

        2. DestroyParticlesOutsideBoundingBox(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart) -> None
        """
    def FindMaxConditionIdInModelPart(self, arg0: Kratos.ModelPart) -> int:
        """FindMaxConditionIdInModelPart(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart) -> int"""
    def FindMaxElementIdInModelPart(self, arg0: Kratos.ModelPart) -> int:
        """FindMaxElementIdInModelPart(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart) -> int"""
    def FindMaxNodeIdInModelPart(self, arg0: Kratos.ModelPart) -> int:
        """FindMaxNodeIdInModelPart(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart) -> int"""
    def GetDiameter(self) -> float:
        """GetDiameter(self: KratosDEMApplication.ParticleCreatorDestructor) -> float"""
    def GetHighNode(self) -> Kratos.Array3:
        """GetHighNode(self: KratosDEMApplication.ParticleCreatorDestructor) -> Kratos.Array3"""
    def GetLowNode(self) -> Kratos.Array3:
        """GetLowNode(self: KratosDEMApplication.ParticleCreatorDestructor) -> Kratos.Array3"""
    def MarkContactElementsForErasing(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """MarkContactElementsForErasing(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
    def MarkContactElementsForErasingContinuum(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """MarkContactElementsForErasingContinuum(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
    def MarkIsolatedParticlesForErasing(self, arg0: Kratos.ModelPart) -> None:
        """MarkIsolatedParticlesForErasing(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart) -> None"""
    @overload
    def MarkParticlesForErasingGivenBoundingBox(self, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: Kratos.Array3) -> None:
        """MarkParticlesForErasingGivenBoundingBox(*args, **kwargs)
        Overloaded function.

        1. MarkParticlesForErasingGivenBoundingBox(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: Kratos.Array3) -> None

        2. MarkParticlesForErasingGivenBoundingBox(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: Kratos.Array3) -> None
        """
    @overload
    def MarkParticlesForErasingGivenBoundingBox(self, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: Kratos.Array3) -> None:
        """MarkParticlesForErasingGivenBoundingBox(*args, **kwargs)
        Overloaded function.

        1. MarkParticlesForErasingGivenBoundingBox(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: Kratos.Array3) -> None

        2. MarkParticlesForErasingGivenBoundingBox(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: Kratos.Array3) -> None
        """
    def MarkParticlesForErasingGivenCylinder(self, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: Kratos.Array3, arg3: float) -> None:
        """MarkParticlesForErasingGivenCylinder(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: Kratos.Array3, arg3: float) -> None"""
    def MarkParticlesForErasingGivenScalarVariableValue(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float, arg3: float) -> None:
        """MarkParticlesForErasingGivenScalarVariableValue(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float, arg3: float) -> None"""
    def MarkParticlesForErasingGivenVectorVariableModulus(self, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: float, arg3: float) -> None:
        """MarkParticlesForErasingGivenVectorVariableModulus(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: Kratos.Array1DVariable3, arg2: float, arg3: float) -> None"""
    def RenumberElementIdsFromGivenValue(self, arg0: Kratos.ModelPart, arg1: int) -> None:
        """RenumberElementIdsFromGivenValue(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart, arg1: int) -> None"""
    def SetHighNode(self, arg0: Kratos.Array3) -> None:
        """SetHighNode(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.Array3) -> None"""
    def SetLowNode(self, arg0: Kratos.Array3) -> None:
        """SetLowNode(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.Array3) -> None"""
    def SetMaxNodeId(self, arg0: int) -> None:
        """SetMaxNodeId(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: int) -> None"""
    def UpdateSurroundingBoundingBox(self, arg0: Kratos.ModelPart) -> None:
        """UpdateSurroundingBoundingBox(self: KratosDEMApplication.ParticleCreatorDestructor, arg0: Kratos.ModelPart) -> None"""

class ParticlesHistoryWatcher(AnalyticWatcher):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.ParticlesHistoryWatcher) -> None"""
    def GetNewParticlesData(self, arg0: list[int], arg1: list[float], arg2: list[float], arg3: list[float], arg4: list[float], arg5: list[float]) -> None:
        """GetNewParticlesData(self: KratosDEMApplication.ParticlesHistoryWatcher, arg0: list[int], arg1: list[float], arg2: list[float], arg3: list[float], arg4: list[float], arg5: list[float]) -> None"""

class PiecewiseLinearRandomVariable(RandomVariable):
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.PiecewiseLinearRandomVariable, arg0: Kratos.Parameters) -> None

        2. __init__(self: KratosDEMApplication.PiecewiseLinearRandomVariable, arg0: Kratos.Parameters, arg1: int) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters, arg1: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.PiecewiseLinearRandomVariable, arg0: Kratos.Parameters) -> None

        2. __init__(self: KratosDEMApplication.PiecewiseLinearRandomVariable, arg0: Kratos.Parameters, arg1: int) -> None
        """
    def GetMean(self) -> float:
        """GetMean(self: KratosDEMApplication.PiecewiseLinearRandomVariable) -> float"""
    def ProbabilityDensity(self, arg0: float) -> float:
        """ProbabilityDensity(self: KratosDEMApplication.PiecewiseLinearRandomVariable, arg0: float) -> float"""
    def Sample(self) -> float:
        """Sample(self: KratosDEMApplication.PiecewiseLinearRandomVariable) -> float"""

class PostUtilities:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.PostUtilities) -> None"""
    def AddModelPartToModelPart(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """AddModelPartToModelPart(self: KratosDEMApplication.PostUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
    def AddSpheresNotBelongingToClustersToMixModelPart(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """AddSpheresNotBelongingToClustersToMixModelPart(self: KratosDEMApplication.PostUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
    def ComputeEulerAngles(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """ComputeEulerAngles(self: KratosDEMApplication.PostUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
    def ComputePoisson(self, arg0: Kratos.ModelPart) -> Kratos.Array3:
        """ComputePoisson(self: KratosDEMApplication.PostUtilities, arg0: Kratos.ModelPart) -> Kratos.Array3"""
    def ComputePoisson2D(self, arg0: Kratos.ModelPart) -> Kratos.Array3:
        """ComputePoisson2D(self: KratosDEMApplication.PostUtilities, arg0: Kratos.ModelPart) -> Kratos.Array3"""
    def IntegrationOfElasticForces(self, arg0: Kratos.NodesArray, arg1: Kratos.Array3) -> None:
        """IntegrationOfElasticForces(self: KratosDEMApplication.PostUtilities, arg0: Kratos.NodesArray, arg1: Kratos.Array3) -> None"""
    def IntegrationOfForces(self, arg0: Kratos.NodesArray, arg1: Kratos.Array3, arg2: Kratos.Array3, arg3: Kratos.Array3) -> None:
        """IntegrationOfForces(self: KratosDEMApplication.PostUtilities, arg0: Kratos.NodesArray, arg1: Kratos.Array3, arg2: Kratos.Array3, arg3: Kratos.Array3) -> None"""
    def QuasiStaticAdimensionalNumber(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.ProcessInfo) -> float:
        """QuasiStaticAdimensionalNumber(self: KratosDEMApplication.PostUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.ProcessInfo) -> float"""
    def VelocityTrap(self, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: Kratos.Array3) -> Kratos.Array3:
        """VelocityTrap(self: KratosDEMApplication.PostUtilities, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: Kratos.Array3) -> Kratos.Array3"""

class PreUtilities:
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.PreUtilities) -> None

        2. __init__(self: KratosDEMApplication.PreUtilities, arg0: Kratos.ModelPart) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.PreUtilities) -> None

        2. __init__(self: KratosDEMApplication.PreUtilities, arg0: Kratos.ModelPart) -> None
        """
    def ApplyConcentricForceOnParticles(self, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: float) -> None:
        """ApplyConcentricForceOnParticles(self: KratosDEMApplication.PreUtilities, arg0: Kratos.ModelPart, arg1: Kratos.Array3, arg2: float) -> None"""
    def BreakBondUtility(self, arg0: Kratos.ModelPart) -> None:
        """BreakBondUtility(self: KratosDEMApplication.PreUtilities, arg0: Kratos.ModelPart) -> None"""
    def CreateCartesianSpecimenMdpa(self, arg0: str) -> None:
        """CreateCartesianSpecimenMdpa(self: KratosDEMApplication.PreUtilities, arg0: str) -> None"""
    def FillAnalyticSubModelPartUtility(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """FillAnalyticSubModelPartUtility(self: KratosDEMApplication.PreUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
    def MarkToEraseParticlesOutsideBoundary(self, arg0: Kratos.ModelPart, arg1: float, arg2: float, arg3: float, arg4: float, arg5: float, arg6: float, arg7: float) -> None:
        """MarkToEraseParticlesOutsideBoundary(self: KratosDEMApplication.PreUtilities, arg0: Kratos.ModelPart, arg1: float, arg2: float, arg3: float, arg4: float, arg5: float, arg6: float, arg7: float) -> None"""
    def MarkToEraseParticlesOutsideRadius(self, arg0: Kratos.ModelPart, arg1: float, arg2: Kratos.Array3, arg3: float) -> None:
        """MarkToEraseParticlesOutsideRadius(self: KratosDEMApplication.PreUtilities, arg0: Kratos.ModelPart, arg1: float, arg2: Kratos.Array3, arg3: float) -> None"""
    def MarkToEraseParticlesOutsideRadiusForGettingCylinder(self, arg0: Kratos.ModelPart, arg1: float, arg2: Kratos.Array3, arg3: float) -> None:
        """MarkToEraseParticlesOutsideRadiusForGettingCylinder(self: KratosDEMApplication.PreUtilities, arg0: Kratos.ModelPart, arg1: float, arg2: Kratos.Array3, arg3: float) -> None"""
    def MeasureBotHeigh(self, arg0: Kratos.ModelPart) -> list:
        """MeasureBotHeigh(self: KratosDEMApplication.PreUtilities, arg0: Kratos.ModelPart) -> list"""
    def MeasureTopHeigh(self, arg0: Kratos.ModelPart) -> list:
        """MeasureTopHeigh(self: KratosDEMApplication.PreUtilities, arg0: Kratos.ModelPart) -> list"""
    def PrintNumberOfNeighboursHistogram(self, arg0: Kratos.ModelPart, arg1: str) -> None:
        """PrintNumberOfNeighboursHistogram(self: KratosDEMApplication.PreUtilities, arg0: Kratos.ModelPart, arg1: str) -> None"""
    def ResetSkinParticles(self, arg0: Kratos.ModelPart) -> None:
        """ResetSkinParticles(self: KratosDEMApplication.PreUtilities, arg0: Kratos.ModelPart) -> None"""
    def SetClusterInformationInProperties(self, arg0: str, arg1: list, arg2: list, arg3: float, arg4: float, arg5: list, arg6: Kratos.Properties) -> None:
        """SetClusterInformationInProperties(self: KratosDEMApplication.PreUtilities, arg0: str, arg1: list, arg2: list, arg3: float, arg4: float, arg5: list, arg6: Kratos.Properties) -> None"""
    def SetSkinParticlesInnerCircularBoundary(self, arg0: Kratos.ModelPart, arg1: float, arg2: float) -> None:
        """SetSkinParticlesInnerCircularBoundary(self: KratosDEMApplication.PreUtilities, arg0: Kratos.ModelPart, arg1: float, arg2: float) -> None"""
    def SetSkinParticlesOuterCircularBoundary(self, arg0: Kratos.ModelPart, arg1: float, arg2: float) -> None:
        """SetSkinParticlesOuterCircularBoundary(self: KratosDEMApplication.PreUtilities, arg0: Kratos.ModelPart, arg1: float, arg2: float) -> None"""
    def SetSkinParticlesOuterSquaredBoundary(self, arg0: Kratos.ModelPart, arg1: float, arg2: Kratos.Array3, arg3: float) -> None:
        """SetSkinParticlesOuterSquaredBoundary(self: KratosDEMApplication.PreUtilities, arg0: Kratos.ModelPart, arg1: float, arg2: Kratos.Array3, arg3: float) -> None"""

class PropertiesProxiesManager:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.PropertiesProxiesManager) -> None"""
    @overload
    def CreatePropertiesProxies(self, arg0: Kratos.ModelPart) -> None:
        """CreatePropertiesProxies(*args, **kwargs)
        Overloaded function.

        1. CreatePropertiesProxies(self: KratosDEMApplication.PropertiesProxiesManager, arg0: Kratos.ModelPart) -> None

        2. CreatePropertiesProxies(self: KratosDEMApplication.PropertiesProxiesManager, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart) -> None
        """
    @overload
    def CreatePropertiesProxies(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart) -> None:
        """CreatePropertiesProxies(*args, **kwargs)
        Overloaded function.

        1. CreatePropertiesProxies(self: KratosDEMApplication.PropertiesProxiesManager, arg0: Kratos.ModelPart) -> None

        2. CreatePropertiesProxies(self: KratosDEMApplication.PropertiesProxiesManager, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart) -> None
        """

class QuaternionIntegrationScheme(DEMIntegrationScheme):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.QuaternionIntegrationScheme) -> None"""

class RVEUtilities:
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.RVEUtilities) -> None

        2. __init__(self: KratosDEMApplication.RVEUtilities, arg0: int, arg1: int, arg2: list[float], arg3: str, arg4: float, arg5: float) -> None
        """
    @overload
    def __init__(self, arg0: int, arg1: int, arg2: list[float], arg3: str, arg4: float, arg5: float) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.RVEUtilities) -> None

        2. __init__(self: KratosDEMApplication.RVEUtilities, arg0: int, arg1: int, arg2: list[float], arg3: str, arg4: float, arg5: float) -> None
        """

class RVEWallBoundary2D(RVEUtilities):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.RVEWallBoundary2D) -> None

        2. __init__(self: KratosDEMApplication.RVEWallBoundary2D, arg0: int, arg1: int, arg2: list[float], arg3: str, arg4: float, arg5: float) -> None
        """
    @overload
    def __init__(self, arg0: int, arg1: int, arg2: list[float], arg3: str, arg4: float, arg5: float) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.RVEWallBoundary2D) -> None

        2. __init__(self: KratosDEMApplication.RVEWallBoundary2D, arg0: int, arg1: int, arg2: list[float], arg3: str, arg4: float, arg5: float) -> None
        """
    def Finalize(self) -> None:
        """Finalize(self: KratosDEMApplication.RVEWallBoundary2D) -> None"""
    def FinalizeSolutionStep(self) -> None:
        """FinalizeSolutionStep(self: KratosDEMApplication.RVEWallBoundary2D) -> None"""
    def Initialize(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """Initialize(self: KratosDEMApplication.RVEWallBoundary2D, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""

class RandomVariable:
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(self: KratosDEMApplication.RandomVariable, arg0: Kratos.Parameters) -> None"""
    def GetSupport(self, *args, **kwargs):
        """GetSupport(self: KratosDEMApplication.RandomVariable) -> Kratos::array_1d<double, 2ul>"""

class ReorderConsecutiveFromGivenIdsModelPartIO(Kratos.ReorderConsecutiveModelPartIO):
    @overload
    def __init__(self, arg0: str) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.ReorderConsecutiveFromGivenIdsModelPartIO, arg0: str) -> None

        2. __init__(self: KratosDEMApplication.ReorderConsecutiveFromGivenIdsModelPartIO, arg0: str, arg1: int, arg2: int, arg3: int) -> None

        3. __init__(self: KratosDEMApplication.ReorderConsecutiveFromGivenIdsModelPartIO, arg0: str, arg1: int, arg2: int, arg3: int, arg4: Kratos.Flags) -> None
        """
    @overload
    def __init__(self, arg0: str, arg1: int, arg2: int, arg3: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.ReorderConsecutiveFromGivenIdsModelPartIO, arg0: str) -> None

        2. __init__(self: KratosDEMApplication.ReorderConsecutiveFromGivenIdsModelPartIO, arg0: str, arg1: int, arg2: int, arg3: int) -> None

        3. __init__(self: KratosDEMApplication.ReorderConsecutiveFromGivenIdsModelPartIO, arg0: str, arg1: int, arg2: int, arg3: int, arg4: Kratos.Flags) -> None
        """
    @overload
    def __init__(self, arg0: str, arg1: int, arg2: int, arg3: int, arg4: Kratos.Flags) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosDEMApplication.ReorderConsecutiveFromGivenIdsModelPartIO, arg0: str) -> None

        2. __init__(self: KratosDEMApplication.ReorderConsecutiveFromGivenIdsModelPartIO, arg0: str, arg1: int, arg2: int, arg3: int) -> None

        3. __init__(self: KratosDEMApplication.ReorderConsecutiveFromGivenIdsModelPartIO, arg0: str, arg1: int, arg2: int, arg3: int, arg4: Kratos.Flags) -> None
        """

class RungeKuttaScheme(DEMIntegrationScheme):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.RungeKuttaScheme) -> None"""

class SphericElementGlobalPhysicsCalculator:
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosDEMApplication.SphericElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart) -> None"""
    def CalculateCenterOfMass(self, arg0: Kratos.ModelPart) -> Kratos.Array3:
        """CalculateCenterOfMass(self: KratosDEMApplication.SphericElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart) -> Kratos.Array3"""
    def CalculateD50(self, arg0: Kratos.ModelPart) -> float:
        """CalculateD50(self: KratosDEMApplication.SphericElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart) -> float"""
    def CalculateElasticEnergy(self, arg0: Kratos.ModelPart) -> float:
        """CalculateElasticEnergy(self: KratosDEMApplication.SphericElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart) -> float"""
    def CalculateGravitationalPotentialEnergy(self, arg0: Kratos.ModelPart, arg1: Kratos.Array3) -> float:
        """CalculateGravitationalPotentialEnergy(self: KratosDEMApplication.SphericElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart, arg1: Kratos.Array3) -> float"""
    def CalculateInelasticFrictionalEnergy(self, arg0: Kratos.ModelPart) -> float:
        """CalculateInelasticFrictionalEnergy(self: KratosDEMApplication.SphericElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart) -> float"""
    def CalculateInelasticRollingResistanceEnergy(self, arg0: Kratos.ModelPart) -> float:
        """CalculateInelasticRollingResistanceEnergy(self: KratosDEMApplication.SphericElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart) -> float"""
    def CalculateInelasticViscodampingEnergy(self, arg0: Kratos.ModelPart) -> float:
        """CalculateInelasticViscodampingEnergy(self: KratosDEMApplication.SphericElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart) -> float"""
    def CalculateMaxNodalVariable(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float:
        """CalculateMaxNodalVariable(self: KratosDEMApplication.SphericElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float"""
    def CalculateMinNodalVariable(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float:
        """CalculateMinNodalVariable(self: KratosDEMApplication.SphericElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable) -> float"""
    def CalculateParticleNumberTimesMaxNormalBallToBallForceTimesRadius(self, arg0: Kratos.ModelPart) -> float:
        """CalculateParticleNumberTimesMaxNormalBallToBallForceTimesRadius(self: KratosDEMApplication.SphericElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart) -> float"""
    def CalculatePorosityWithinSphere(self, arg0: Kratos.ModelPart, arg1: float, arg2: Kratos.Array3) -> float:
        """CalculatePorosityWithinSphere(self: KratosDEMApplication.SphericElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart, arg1: float, arg2: Kratos.Array3) -> float"""
    def CalculateRotationalKinematicEnergy(self, arg0: Kratos.ModelPart) -> float:
        """CalculateRotationalKinematicEnergy(self: KratosDEMApplication.SphericElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart) -> float"""
    def CalculateSumOfInternalForces(self, arg0: Kratos.ModelPart) -> Kratos.Array3:
        """CalculateSumOfInternalForces(self: KratosDEMApplication.SphericElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart) -> Kratos.Array3"""
    def CalculateSumOfParticlesWithinSphere(self, arg0: Kratos.ModelPart, arg1: float, arg2: Kratos.Array3) -> float:
        """CalculateSumOfParticlesWithinSphere(self: KratosDEMApplication.SphericElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart, arg1: float, arg2: Kratos.Array3) -> float"""
    def CalculateTotalMass(self, arg0: Kratos.ModelPart) -> float:
        """CalculateTotalMass(self: KratosDEMApplication.SphericElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart) -> float"""
    def CalculateTotalMomentum(self, arg0: Kratos.ModelPart) -> Kratos.Array3:
        """CalculateTotalMomentum(self: KratosDEMApplication.SphericElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart) -> Kratos.Array3"""
    def CalculateTotalVolume(self, arg0: Kratos.ModelPart) -> float:
        """CalculateTotalVolume(self: KratosDEMApplication.SphericElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart) -> float"""
    def CalculateTranslationalKinematicEnergy(self, arg0: Kratos.ModelPart) -> float:
        """CalculateTranslationalKinematicEnergy(self: KratosDEMApplication.SphericElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart) -> float"""
    def CalulateTotalAngularMomentum(self, arg0: Kratos.ModelPart) -> Kratos.Array3:
        """CalulateTotalAngularMomentum(self: KratosDEMApplication.SphericElementGlobalPhysicsCalculator, arg0: Kratos.ModelPart) -> Kratos.Array3"""
    def GetInitialCenterOfMass(self) -> Kratos.Array3:
        """GetInitialCenterOfMass(self: KratosDEMApplication.SphericElementGlobalPhysicsCalculator) -> Kratos.Array3"""

class StationarityChecker:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.StationarityChecker) -> None"""
    def CheckIfItsTimeToChangeGravity(self, arg0: Kratos.ModelPart, arg1: float, arg2: float, arg3: float) -> bool:
        """CheckIfItsTimeToChangeGravity(self: KratosDEMApplication.StationarityChecker, arg0: Kratos.ModelPart, arg1: float, arg2: float, arg3: float) -> bool"""
    def CheckIfVariableIsNullInModelPart(self, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float, arg3: bool) -> bool:
        """CheckIfVariableIsNullInModelPart(self: KratosDEMApplication.StationarityChecker, arg0: Kratos.ModelPart, arg1: Kratos.DoubleVariable, arg2: float, arg3: bool) -> bool"""

class SymplecticEulerScheme(DEMIntegrationScheme):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.SymplecticEulerScheme) -> None"""

class TaylorScheme(DEMIntegrationScheme):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.TaylorScheme) -> None"""

class VectorDistances:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.VectorDistances) -> None"""

class VectorResultNodesContainer:
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.VectorResultNodesContainer) -> None"""

class VelocityVerletScheme(DEMIntegrationScheme):
    def __init__(self) -> None:
        """__init__(self: KratosDEMApplication.VelocityVerletScheme) -> None"""

class VelocityVerletSolverStrategy(ExplicitSolverStrategy):
    def __init__(self, arg0: ExplicitSolverSettings, arg1: float, arg2: float, arg3: float, arg4: int, arg5, arg6, arg7: Kratos.SpatialSearch, arg8: Kratos.Parameters) -> None:
        """__init__(self: KratosDEMApplication.VelocityVerletSolverStrategy, arg0: KratosDEMApplication.ExplicitSolverSettings, arg1: float, arg2: float, arg3: float, arg4: int, arg5: Kratos::ParticleCreatorDestructor, arg6: Kratos::DEM_FEM_Search, arg7: Kratos.SpatialSearch, arg8: Kratos.Parameters) -> None"""
