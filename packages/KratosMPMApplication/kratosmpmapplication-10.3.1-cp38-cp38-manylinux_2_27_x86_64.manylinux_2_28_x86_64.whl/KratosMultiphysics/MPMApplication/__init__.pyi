import Kratos
from typing import overload

class DispNewtonianFluid3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosMPMApplication.DispNewtonianFluid3DLaw) -> None"""

class DispNewtonianFluidPlaneStrain2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosMPMApplication.DispNewtonianFluidPlaneStrain2DLaw) -> None"""

class HenckyBorjaCamClayPlastic3DLaw(Kratos.ConstitutiveLaw):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyBorjaCamClayPlastic3DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyBorjaCamClayPlastic3DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """
    @overload
    def __init__(self, arg0, arg1, arg2) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyBorjaCamClayPlastic3DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyBorjaCamClayPlastic3DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """

class HenckyBorjaCamClayPlasticAxisym2DLaw(Kratos.ConstitutiveLaw):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyBorjaCamClayPlasticAxisym2DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyBorjaCamClayPlasticAxisym2DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """
    @overload
    def __init__(self, arg0, arg1, arg2) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyBorjaCamClayPlasticAxisym2DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyBorjaCamClayPlasticAxisym2DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """

class HenckyBorjaCamClayPlasticPlaneStrain2DLaw(Kratos.ConstitutiveLaw):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyBorjaCamClayPlasticPlaneStrain2DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyBorjaCamClayPlasticPlaneStrain2DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """
    @overload
    def __init__(self, arg0, arg1, arg2) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyBorjaCamClayPlasticPlaneStrain2DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyBorjaCamClayPlasticPlaneStrain2DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """

class HenckyMCPlastic3DLaw(Kratos.ConstitutiveLaw):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyMCPlastic3DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyMCPlastic3DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """
    @overload
    def __init__(self, arg0, arg1, arg2) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyMCPlastic3DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyMCPlastic3DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """

class HenckyMCPlasticAxisym2DLaw(Kratos.ConstitutiveLaw):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyMCPlasticAxisym2DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyMCPlasticAxisym2DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """
    @overload
    def __init__(self, arg0, arg1, arg2) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyMCPlasticAxisym2DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyMCPlasticAxisym2DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """

class HenckyMCPlasticPlaneStrain2DLaw(Kratos.ConstitutiveLaw):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyMCPlasticPlaneStrain2DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyMCPlasticPlaneStrain2DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """
    @overload
    def __init__(self, arg0, arg1, arg2) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyMCPlasticPlaneStrain2DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyMCPlasticPlaneStrain2DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """

class HenckyMCPlasticPlaneStrainUP2DLaw(Kratos.ConstitutiveLaw):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyMCPlasticPlaneStrainUP2DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyMCPlasticPlaneStrainUP2DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """
    @overload
    def __init__(self, arg0, arg1, arg2) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyMCPlasticPlaneStrainUP2DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyMCPlasticPlaneStrainUP2DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """

class HenckyMCPlasticUP3DLaw(Kratos.ConstitutiveLaw):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyMCPlasticUP3DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyMCPlasticUP3DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """
    @overload
    def __init__(self, arg0, arg1, arg2) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyMCPlasticUP3DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyMCPlasticUP3DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """

class HenckyMCStrainSofteningPlastic3DLaw(Kratos.ConstitutiveLaw):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyMCStrainSofteningPlastic3DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyMCStrainSofteningPlastic3DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """
    @overload
    def __init__(self, arg0, arg1, arg2) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyMCStrainSofteningPlastic3DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyMCStrainSofteningPlastic3DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """

class HenckyMCStrainSofteningPlasticAxisym2DLaw(Kratos.ConstitutiveLaw):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyMCStrainSofteningPlasticAxisym2DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyMCStrainSofteningPlasticAxisym2DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """
    @overload
    def __init__(self, arg0, arg1, arg2) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyMCStrainSofteningPlasticAxisym2DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyMCStrainSofteningPlasticAxisym2DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """

class HenckyMCStrainSofteningPlasticPlaneStrain2DLaw(Kratos.ConstitutiveLaw):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyMCStrainSofteningPlasticPlaneStrain2DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyMCStrainSofteningPlasticPlaneStrain2DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """
    @overload
    def __init__(self, arg0, arg1, arg2) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.HenckyMCStrainSofteningPlasticPlaneStrain2DLaw) -> None

        2. __init__(self: KratosMPMApplication.HenckyMCStrainSofteningPlasticPlaneStrain2DLaw, arg0: Kratos::MPMFlowRule, arg1: Kratos::MPMYieldCriterion, arg2: Kratos::MPMHardeningLaw) -> None
        """

class HyperElasticNeoHookean3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosMPMApplication.HyperElasticNeoHookean3DLaw) -> None"""

class HyperElasticNeoHookeanAxisym2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosMPMApplication.HyperElasticNeoHookeanAxisym2DLaw) -> None"""

class HyperElasticNeoHookeanPlaneStrain2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosMPMApplication.HyperElasticNeoHookeanPlaneStrain2DLaw) -> None"""

class HyperElasticNeoHookeanUP3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosMPMApplication.HyperElasticNeoHookeanUP3DLaw) -> None"""

class HyperElasticPlaneStrainUP2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosMPMApplication.HyperElasticPlaneStrainUP2DLaw) -> None"""

class JohnsonCookThermalPlastic2DAxisymLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosMPMApplication.JohnsonCookThermalPlastic2DAxisymLaw) -> None"""

class JohnsonCookThermalPlastic2DPlaneStrainLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosMPMApplication.JohnsonCookThermalPlastic2DPlaneStrainLaw) -> None"""

class JohnsonCookThermalPlastic3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosMPMApplication.JohnsonCookThermalPlastic3DLaw) -> None"""

class KratosMPMApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosMPMApplication.KratosMPMApplication) -> None"""

class LinearElasticIsotropic3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosMPMApplication.LinearElasticIsotropic3DLaw) -> None"""

class LinearElasticIsotropicAxisym2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosMPMApplication.LinearElasticIsotropicAxisym2DLaw) -> None"""

class LinearElasticIsotropicPlaneStrain2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosMPMApplication.LinearElasticIsotropicPlaneStrain2DLaw) -> None"""

class LinearElasticIsotropicPlaneStress2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosMPMApplication.LinearElasticIsotropicPlaneStress2DLaw) -> None"""

class MPMExplicitScheme(Kratos.Scheme):
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosMPMApplication.MPMExplicitScheme, arg0: Kratos.ModelPart) -> None"""
    def Initialize(self, arg0: Kratos.ModelPart) -> None:
        """Initialize(self: KratosMPMApplication.MPMExplicitScheme, arg0: Kratos.ModelPart) -> None"""

class MPMExplicitStrategy(Kratos.ImplicitSolvingStrategy):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: bool, arg3: bool, arg4: bool) -> None:
        """__init__(self: KratosMPMApplication.MPMExplicitStrategy, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: bool, arg3: bool, arg4: bool) -> None"""

class MPMResidualBasedBossakScheme(Kratos.Scheme):
    def __init__(self, arg0: Kratos.ModelPart, arg1: int, arg2: int, arg3: float, arg4: float, arg5: bool) -> None:
        """__init__(self: KratosMPMApplication.MPMResidualBasedBossakScheme, arg0: Kratos.ModelPart, arg1: int, arg2: int, arg3: float, arg4: float, arg5: bool) -> None"""
    def Initialize(self, arg0: Kratos.ModelPart) -> None:
        """Initialize(self: KratosMPMApplication.MPMResidualBasedBossakScheme, arg0: Kratos.ModelPart) -> None"""

class MPMResidualBasedNewtonRaphsonStrategy(Kratos.ImplicitSolvingStrategy):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.LinearSolver, arg3: Kratos.ConvergenceCriteria, arg4: int, arg5: bool, arg6: bool, arg7: bool) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.MPMResidualBasedNewtonRaphsonStrategy, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.LinearSolver, arg3: Kratos.ConvergenceCriteria, arg4: int, arg5: bool, arg6: bool, arg7: bool) -> None

        2. __init__(self: KratosMPMApplication.MPMResidualBasedNewtonRaphsonStrategy, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.ConvergenceCriteria, arg3: Kratos.BuilderAndSolver, arg4: int, arg5: bool, arg6: bool, arg7: bool) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.ConvergenceCriteria, arg3: Kratos.BuilderAndSolver, arg4: int, arg5: bool, arg6: bool, arg7: bool) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosMPMApplication.MPMResidualBasedNewtonRaphsonStrategy, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.LinearSolver, arg3: Kratos.ConvergenceCriteria, arg4: int, arg5: bool, arg6: bool, arg7: bool) -> None

        2. __init__(self: KratosMPMApplication.MPMResidualBasedNewtonRaphsonStrategy, arg0: Kratos.ModelPart, arg1: Kratos.Scheme, arg2: Kratos.ConvergenceCriteria, arg3: Kratos.BuilderAndSolver, arg4: int, arg5: bool, arg6: bool, arg7: bool) -> None
        """

class MPMVtkOutput(Kratos.IO):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosMPMApplication.MPMVtkOutput, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""
    @staticmethod
    def GetDefaultParameters() -> Kratos.Parameters:
        """GetDefaultParameters() -> Kratos.Parameters"""
    def PrintOutput(self, output_filename: str = ...) -> None:
        """PrintOutput(self: KratosMPMApplication.MPMVtkOutput, output_filename: str = '') -> None"""

class MPM_MPI_Utilities:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    @staticmethod
    def TransferConditions(arg0: Kratos.ModelPart, arg1: list[Kratos.ConditionsArray]) -> None:
        """TransferConditions(arg0: Kratos.ModelPart, arg1: list[Kratos.ConditionsArray]) -> None"""
    @staticmethod
    def TransferElements(arg0: Kratos.ModelPart, arg1: list[Kratos.ElementsArray]) -> None:
        """TransferElements(arg0: Kratos.ModelPart, arg1: list[Kratos.ElementsArray]) -> None"""

class MaterialPointEraseProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosMPMApplication.MaterialPointEraseProcess, arg0: Kratos.ModelPart) -> None"""

def GenerateLagrangeNodes(arg0: Kratos.ModelPart) -> None:
    """GenerateLagrangeNodes(arg0: Kratos.ModelPart) -> None"""
def GenerateMaterialPointCondition(arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart) -> None:
    """GenerateMaterialPointCondition(arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart) -> None"""
def GenerateMaterialPointElement(arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart, arg3: bool) -> None:
    """GenerateMaterialPointElement(arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart, arg3: bool) -> None"""
def SearchElement(arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: int, arg3: float) -> None:
    """SearchElement(arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: int, arg3: float) -> None"""
