import Kratos

class ApplyComponentTableProcessDam(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.ApplyComponentTableProcessDam, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class BossakDisplacementSmoothingScheme(Kratos.Scheme):
    def __init__(self, arg0: float, arg1: float, arg2: float) -> None:
        """__init__(self: KratosDamApplication.BossakDisplacementSmoothingScheme, arg0: float, arg1: float, arg2: float) -> None"""

class ConstructionUtility:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.PiecewiseLinearTable, arg3: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.ConstructionUtility, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.PiecewiseLinearTable, arg3: Kratos.Parameters) -> None"""
    def ActiveHeatFluxAzenha(self, arg0: Kratos.Parameters) -> None:
        """ActiveHeatFluxAzenha(self: KratosDamApplication.ConstructionUtility, arg0: Kratos.Parameters) -> None"""
    def ActiveHeatFluxNoorzai(self, arg0: Kratos.Parameters) -> None:
        """ActiveHeatFluxNoorzai(self: KratosDamApplication.ConstructionUtility, arg0: Kratos.Parameters) -> None"""
    def AfterOutputStep(self) -> None:
        """AfterOutputStep(self: KratosDamApplication.ConstructionUtility) -> None"""
    def AssignTimeActivation(self, arg0: str, arg1: int, arg2: float, arg3: float) -> None:
        """AssignTimeActivation(self: KratosDamApplication.ConstructionUtility, arg0: str, arg1: int, arg2: float, arg3: float) -> None"""
    def CheckTemperature(self, arg0: Kratos.Parameters) -> None:
        """CheckTemperature(self: KratosDamApplication.ConstructionUtility, arg0: Kratos.Parameters) -> None"""
    def Initialize(self) -> None:
        """Initialize(self: KratosDamApplication.ConstructionUtility) -> None"""
    def InitializeSolutionStep(self, arg0: str, arg1: str, arg2: str, arg3: str, arg4: bool, arg5: bool, arg6: int) -> None:
        """InitializeSolutionStep(self: KratosDamApplication.ConstructionUtility, arg0: str, arg1: str, arg2: str, arg3: str, arg4: bool, arg5: bool, arg6: int) -> None"""
    def SearchingFluxes(self) -> None:
        """SearchingFluxes(self: KratosDamApplication.ConstructionUtility) -> None"""

class DamAddedMassConditionProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.DamAddedMassConditionProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class DamAzenhaHeatFluxProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.DamAzenhaHeatFluxProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class DamBofangConditionTemperatureProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.DamBofangConditionTemperatureProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class DamChemoMechanicalAgingYoungProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.DamChemoMechanicalAgingYoungProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class DamFixTemperatureConditionProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.DamFixTemperatureConditionProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class DamGroutingReferenceTemperatureProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.DamGroutingReferenceTemperatureProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class DamHydroConditionLoadProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.DamHydroConditionLoadProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class DamInputTableNodalYoungModulusProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.PiecewiseLinearTable, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.DamInputTableNodalYoungModulusProcess, arg0: Kratos.ModelPart, arg1: Kratos.PiecewiseLinearTable, arg2: Kratos.Parameters) -> None"""

class DamNodalReferenceTemperatureProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.PiecewiseLinearTable, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.DamNodalReferenceTemperatureProcess, arg0: Kratos.ModelPart, arg1: Kratos.PiecewiseLinearTable, arg2: Kratos.Parameters) -> None"""

class DamNodalYoungModulusProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.DamNodalYoungModulusProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class DamNoorzaiHeatFluxProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.DamNoorzaiHeatFluxProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class DamPScheme(Kratos.Scheme):
    def __init__(self, arg0: float, arg1: float) -> None:
        """__init__(self: KratosDamApplication.DamPScheme, arg0: float, arg1: float) -> None"""

class DamRandomFieldsVariableProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.PiecewiseLinearTable, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.DamRandomFieldsVariableProcess, arg0: Kratos.ModelPart, arg1: Kratos.PiecewiseLinearTable, arg2: Kratos.Parameters) -> None"""

class DamReservoirConstantTemperatureProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.DamReservoirConstantTemperatureProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class DamReservoirMonitoringTemperatureProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.DamReservoirMonitoringTemperatureProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class DamTSolAirHeatFluxProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.DamTSolAirHeatFluxProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class DamTemperaturebyDeviceProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.DamTemperaturebyDeviceProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class DamUPScheme(Kratos.Scheme):
    def __init__(self, arg0: float, arg1: float, arg2: float, arg3: float) -> None:
        """__init__(self: KratosDamApplication.DamUPScheme, arg0: float, arg1: float, arg2: float, arg3: float) -> None"""

class DamUpliftCircularConditionLoadProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.DamUpliftCircularConditionLoadProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None"""

class DamUpliftConditionLoadProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.DamUpliftConditionLoadProcess, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None"""

class DamWestergaardConditionLoadProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.DamWestergaardConditionLoadProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class GlobalJointStressUtility:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDamApplication.GlobalJointStressUtility, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""
    def ComputingGlobalStress(self) -> None:
        """ComputingGlobalStress(self: KratosDamApplication.GlobalJointStressUtility) -> None"""

class IncrementalUpdateStaticDampedSmoothingScheme(Kratos.Scheme):
    def __init__(self, arg0: float, arg1: float) -> None:
        """__init__(self: KratosDamApplication.IncrementalUpdateStaticDampedSmoothingScheme, arg0: float, arg1: float) -> None"""

class IncrementalUpdateStaticSmoothingScheme(Kratos.Scheme):
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.IncrementalUpdateStaticSmoothingScheme) -> None"""

class KratosDamApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.KratosDamApplication) -> None"""

class LinearElastic2DPlaneStrainNodal(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.LinearElastic2DPlaneStrainNodal) -> None"""

class LinearElastic2DPlaneStressNodal(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.LinearElastic2DPlaneStressNodal) -> None"""

class LinearElastic3DLawNodal(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.LinearElastic3DLawNodal) -> None"""

class MappingVariables2DUtilities:
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.MappingVariables2DUtilities) -> None"""
    def MappingMechanicalModelParts(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: bool, arg3: bool) -> None:
        """MappingMechanicalModelParts(self: KratosDamApplication.MappingVariables2DUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: bool, arg3: bool) -> None"""
    def MappingThermalModelParts(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: bool, arg3: bool) -> None:
        """MappingThermalModelParts(self: KratosDamApplication.MappingVariables2DUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: bool, arg3: bool) -> None"""

class MappingVariables3DUtilities:
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.MappingVariables3DUtilities) -> None"""
    def MappingMechanicalModelParts(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: bool, arg3: bool) -> None:
        """MappingMechanicalModelParts(self: KratosDamApplication.MappingVariables3DUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: bool, arg3: bool) -> None"""
    def MappingThermalModelParts(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: bool, arg3: bool) -> None:
        """MappingThermalModelParts(self: KratosDamApplication.MappingVariables3DUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: bool, arg3: bool) -> None"""

class StreamlinesOutput3DUtilities:
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.StreamlinesOutput3DUtilities) -> None"""
    def ComputeOutputStep(self, arg0: Kratos.ModelPart, arg1: int) -> None:
        """ComputeOutputStep(self: KratosDamApplication.StreamlinesOutput3DUtilities, arg0: Kratos.ModelPart, arg1: int) -> None"""

class ThermalLinearElastic2DPlaneStrain(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.ThermalLinearElastic2DPlaneStrain) -> None"""

class ThermalLinearElastic2DPlaneStrainNodal(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.ThermalLinearElastic2DPlaneStrainNodal) -> None"""

class ThermalLinearElastic2DPlaneStress(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.ThermalLinearElastic2DPlaneStress) -> None"""

class ThermalLinearElastic2DPlaneStressNodal(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.ThermalLinearElastic2DPlaneStressNodal) -> None"""

class ThermalLinearElastic3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.ThermalLinearElastic3DLaw) -> None"""

class ThermalLinearElastic3DLawNodal(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.ThermalLinearElastic3DLawNodal) -> None"""

class ThermalModifiedMisesNonlocalDamage3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.ThermalModifiedMisesNonlocalDamage3DLaw) -> None"""

class ThermalModifiedMisesNonlocalDamagePlaneStrain2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.ThermalModifiedMisesNonlocalDamagePlaneStrain2DLaw) -> None"""

class ThermalModifiedMisesNonlocalDamagePlaneStress2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.ThermalModifiedMisesNonlocalDamagePlaneStress2DLaw) -> None"""

class ThermalSimoJuLocalDamage3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.ThermalSimoJuLocalDamage3DLaw) -> None"""

class ThermalSimoJuLocalDamagePlaneStrain2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.ThermalSimoJuLocalDamagePlaneStrain2DLaw) -> None"""

class ThermalSimoJuLocalDamagePlaneStress2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.ThermalSimoJuLocalDamagePlaneStress2DLaw) -> None"""

class ThermalSimoJuNonlocalDamage3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.ThermalSimoJuNonlocalDamage3DLaw) -> None"""

class ThermalSimoJuNonlocalDamagePlaneStrain2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.ThermalSimoJuNonlocalDamagePlaneStrain2DLaw) -> None"""

class ThermalSimoJuNonlocalDamagePlaneStress2DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.ThermalSimoJuNonlocalDamagePlaneStress2DLaw) -> None"""

class TransferSelfweightStressUtility:
    def __init__(self) -> None:
        """__init__(self: KratosDamApplication.TransferSelfweightStressUtility) -> None"""
    def Transfer(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: int) -> None:
        """Transfer(self: KratosDamApplication.TransferSelfweightStressUtility, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: int) -> None"""
    def TransferInitialStress(self, arg0: Kratos.ModelPart, arg1: int) -> None:
        """TransferInitialStress(self: KratosDamApplication.TransferSelfweightStressUtility, arg0: Kratos.ModelPart, arg1: int) -> None"""
