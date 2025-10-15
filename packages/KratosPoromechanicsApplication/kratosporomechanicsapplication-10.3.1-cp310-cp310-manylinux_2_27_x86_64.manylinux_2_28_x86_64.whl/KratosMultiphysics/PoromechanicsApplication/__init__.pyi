import Kratos

class ApplyComponentTableProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosPoromechanicsApplication.ApplyComponentTableProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class ApplyConstantHydrostaticPressureProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosPoromechanicsApplication.ApplyConstantHydrostaticPressureProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class ApplyDoubleTableProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosPoromechanicsApplication.ApplyDoubleTableProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class ApplyHydrostaticPressureTableProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosPoromechanicsApplication.ApplyHydrostaticPressureTableProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class BilinearCohesive2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.BilinearCohesive2DLaw) -> None"""

class BilinearCohesive3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.BilinearCohesive3DLaw) -> None"""

class ElasticCohesive2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.ElasticCohesive2DLaw) -> None"""

class ElasticCohesive3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.ElasticCohesive3DLaw) -> None"""

class ElastoPlasticModMohrCoulombCohesive2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.ElastoPlasticModMohrCoulombCohesive2DLaw) -> None"""

class ElastoPlasticModMohrCoulombCohesive3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.ElastoPlasticModMohrCoulombCohesive3DLaw) -> None"""

class ElastoPlasticMohrCoulombCohesive2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.ElastoPlasticMohrCoulombCohesive2DLaw) -> None"""

class ElastoPlasticMohrCoulombCohesive3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.ElastoPlasticMohrCoulombCohesive3DLaw) -> None"""

class ExponentialCohesive2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.ExponentialCohesive2DLaw) -> None"""

class ExponentialCohesive3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.ExponentialCohesive3DLaw) -> None"""

class FracturePropagation2DUtilities:
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.FracturePropagation2DUtilities) -> None"""
    def CheckFracturePropagation(self, arg0: Kratos.Parameters, arg1: Kratos.ModelPart, arg2: bool) -> bool:
        """CheckFracturePropagation(self: KratosPoromechanicsApplication.FracturePropagation2DUtilities, arg0: Kratos.Parameters, arg1: Kratos.ModelPart, arg2: bool) -> bool"""
    def MappingModelParts(self, arg0: Kratos.Parameters, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart, arg3: bool) -> None:
        """MappingModelParts(self: KratosPoromechanicsApplication.FracturePropagation2DUtilities, arg0: Kratos.Parameters, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart, arg3: bool) -> None"""

class FracturePropagation3DUtilities:
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.FracturePropagation3DUtilities) -> None"""
    def CheckFracturePropagation(self, arg0: Kratos.Parameters, arg1: Kratos.ModelPart, arg2: bool) -> bool:
        """CheckFracturePropagation(self: KratosPoromechanicsApplication.FracturePropagation3DUtilities, arg0: Kratos.Parameters, arg1: Kratos.ModelPart, arg2: bool) -> bool"""
    def MappingModelParts(self, arg0: Kratos.Parameters, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart, arg3: bool) -> None:
        """MappingModelParts(self: KratosPoromechanicsApplication.FracturePropagation3DUtilities, arg0: Kratos.Parameters, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart, arg3: bool) -> None"""

class HyperElasticSolid3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.HyperElasticSolid3DLaw) -> None"""

class InitialStress2DUtilities:
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.InitialStress2DUtilities) -> None"""
    def SaveInitialStresses(self, arg0: Kratos.Parameters, arg1: Kratos.ModelPart) -> None:
        """SaveInitialStresses(self: KratosPoromechanicsApplication.InitialStress2DUtilities, arg0: Kratos.Parameters, arg1: Kratos.ModelPart) -> None"""
    def TransferInitialStresses(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: bool) -> None:
        """TransferInitialStresses(self: KratosPoromechanicsApplication.InitialStress2DUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: bool) -> None"""

class InitialStress3DUtilities:
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.InitialStress3DUtilities) -> None"""
    def SaveInitialStresses(self, arg0: Kratos.Parameters, arg1: Kratos.ModelPart) -> None:
        """SaveInitialStresses(self: KratosPoromechanicsApplication.InitialStress3DUtilities, arg0: Kratos.Parameters, arg1: Kratos.ModelPart) -> None"""
    def TransferInitialStresses(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: bool) -> None:
        """TransferInitialStresses(self: KratosPoromechanicsApplication.InitialStress3DUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: bool) -> None"""

class IsotropicDamageCohesive2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.IsotropicDamageCohesive2DLaw) -> None"""

class IsotropicDamageCohesive3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.IsotropicDamageCohesive3DLaw) -> None"""

class KratosPoromechanicsApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.KratosPoromechanicsApplication) -> None"""

class LinearElasticPlaneStrainSolid2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.LinearElasticPlaneStrainSolid2DLaw) -> None"""

class LinearElasticPlaneStressSolid2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.LinearElasticPlaneStressSolid2DLaw) -> None"""

class LinearElasticSolid3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.LinearElasticSolid3DLaw) -> None"""

class ModifiedMisesNonlocalDamage3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.ModifiedMisesNonlocalDamage3DLaw) -> None"""

class ModifiedMisesNonlocalDamagePlaneStrain2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.ModifiedMisesNonlocalDamagePlaneStrain2DLaw) -> None"""

class ModifiedMisesNonlocalDamagePlaneStress2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.ModifiedMisesNonlocalDamagePlaneStress2DLaw) -> None"""

class PeriodicInterfaceProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosPoromechanicsApplication.PeriodicInterfaceProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class PoroExplicitCDScheme(Kratos.Scheme):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.PoroExplicitCDScheme) -> None"""

class PoroExplicitVVScheme(Kratos.Scheme):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.PoroExplicitVVScheme) -> None"""

class PoroNewmarkDynamicUPlScheme(Kratos.Scheme):
    def __init__(self, arg0: float, arg1: float, arg2: float, arg3: float) -> None:
        """__init__(self: KratosPoromechanicsApplication.PoroNewmarkDynamicUPlScheme, arg0: float, arg1: float, arg2: float, arg3: float) -> None"""

class PoroNewmarkQuasistaticDampedUPlScheme(Kratos.Scheme):
    def __init__(self, arg0: float, arg1: float, arg2: float, arg3: float) -> None:
        """__init__(self: KratosPoromechanicsApplication.PoroNewmarkQuasistaticDampedUPlScheme, arg0: float, arg1: float, arg2: float, arg3: float) -> None"""

class PoroNewmarkQuasistaticUPlScheme(Kratos.Scheme):
    def __init__(self, arg0: float, arg1: float, arg2: float, arg3: float) -> None:
        """__init__(self: KratosPoromechanicsApplication.PoroNewmarkQuasistaticUPlScheme, arg0: float, arg1: float, arg2: float, arg3: float) -> None"""

class PoromechanicsExplicitNonlocalStrategy(Kratos.ImplicitSolvingStrategy):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.Parameters, arg3: bool, arg4: bool, arg5: bool) -> None:
        """__init__(self: KratosPoromechanicsApplication.PoromechanicsExplicitNonlocalStrategy, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.Parameters, arg3: bool, arg4: bool, arg5: bool) -> None"""

class PoromechanicsExplicitStrategy(Kratos.ImplicitSolvingStrategy):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.Parameters, arg3: bool, arg4: bool, arg5: bool) -> None:
        """__init__(self: KratosPoromechanicsApplication.PoromechanicsExplicitStrategy, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.Parameters, arg3: bool, arg4: bool, arg5: bool) -> None"""

class PoromechanicsFaceLoadControlModuleProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosPoromechanicsApplication.PoromechanicsFaceLoadControlModuleProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class PoromechanicsNewtonRaphsonNonlocalStrategy(Kratos.ImplicitSolvingStrategy):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.ConvergenceCriteria, arg3: Kratos.BuilderAndSolver, arg4: Kratos.Parameters, arg5: int, arg6: bool, arg7: bool, arg8: bool) -> None:
        """__init__(self: KratosPoromechanicsApplication.PoromechanicsNewtonRaphsonNonlocalStrategy, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.ConvergenceCriteria, arg3: Kratos.BuilderAndSolver, arg4: Kratos.Parameters, arg5: int, arg6: bool, arg7: bool, arg8: bool) -> None"""

class PoromechanicsNewtonRaphsonStrategy(Kratos.ImplicitSolvingStrategy):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.ConvergenceCriteria, arg3: Kratos.BuilderAndSolver, arg4: Kratos.Parameters, arg5: int, arg6: bool, arg7: bool, arg8: bool) -> None:
        """__init__(self: KratosPoromechanicsApplication.PoromechanicsNewtonRaphsonStrategy, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.ConvergenceCriteria, arg3: Kratos.BuilderAndSolver, arg4: Kratos.Parameters, arg5: int, arg6: bool, arg7: bool, arg8: bool) -> None"""

class PoromechanicsRammArcLengthNonlocalStrategy(Kratos.ImplicitSolvingStrategy):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.ConvergenceCriteria, arg3: Kratos.BuilderAndSolver, arg4: Kratos.Parameters, arg5: int, arg6: bool, arg7: bool, arg8: bool) -> None:
        """__init__(self: KratosPoromechanicsApplication.PoromechanicsRammArcLengthNonlocalStrategy, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.ConvergenceCriteria, arg3: Kratos.BuilderAndSolver, arg4: Kratos.Parameters, arg5: int, arg6: bool, arg7: bool, arg8: bool) -> None"""

class PoromechanicsRammArcLengthStrategy(Kratos.ImplicitSolvingStrategy):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.ConvergenceCriteria, arg3: Kratos.BuilderAndSolver, arg4: Kratos.Parameters, arg5: int, arg6: bool, arg7: bool, arg8: bool) -> None:
        """__init__(self: KratosPoromechanicsApplication.PoromechanicsRammArcLengthStrategy, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.ConvergenceCriteria, arg3: Kratos.BuilderAndSolver, arg4: Kratos.Parameters, arg5: int, arg6: bool, arg7: bool, arg8: bool) -> None"""
    def UpdateLoads(self) -> None:
        """UpdateLoads(self: KratosPoromechanicsApplication.PoromechanicsRammArcLengthStrategy) -> None"""

class SimoJuLocalDamage3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.SimoJuLocalDamage3DLaw) -> None"""

class SimoJuLocalDamagePlaneStrain2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.SimoJuLocalDamagePlaneStrain2DLaw) -> None"""

class SimoJuLocalDamagePlaneStress2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.SimoJuLocalDamagePlaneStress2DLaw) -> None"""

class SimoJuNonlocalDamage3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.SimoJuNonlocalDamage3DLaw) -> None"""

class SimoJuNonlocalDamagePlaneStrain2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.SimoJuNonlocalDamagePlaneStrain2DLaw) -> None"""

class SimoJuNonlocalDamagePlaneStress2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosPoromechanicsApplication.SimoJuNonlocalDamagePlaneStress2DLaw) -> None"""
