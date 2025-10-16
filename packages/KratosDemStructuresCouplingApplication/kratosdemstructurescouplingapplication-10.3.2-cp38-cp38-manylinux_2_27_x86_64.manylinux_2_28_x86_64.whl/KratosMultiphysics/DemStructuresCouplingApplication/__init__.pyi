import Kratos

class ComputeDEMFaceLoadUtility:
    def __init__(self) -> None:
        """__init__(self: KratosDemStructuresCouplingApplication.ComputeDEMFaceLoadUtility) -> None"""
    def CalculateDEMFaceLoads(self, arg0: Kratos.ModelPart, arg1: float, arg2: float) -> None:
        """CalculateDEMFaceLoads(self: KratosDemStructuresCouplingApplication.ComputeDEMFaceLoadUtility, arg0: Kratos.ModelPart, arg1: float, arg2: float) -> None"""
    def ClearDEMFaceLoads(self, arg0: Kratos.ModelPart) -> None:
        """ClearDEMFaceLoads(self: KratosDemStructuresCouplingApplication.ComputeDEMFaceLoadUtility, arg0: Kratos.ModelPart) -> None"""

class ControlModuleFemDem2DUtilities:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosDemStructuresCouplingApplication.ControlModuleFemDem2DUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None"""
    def ExecuteFinalizeSolutionStep(self) -> None:
        """ExecuteFinalizeSolutionStep(self: KratosDemStructuresCouplingApplication.ControlModuleFemDem2DUtilities) -> None"""
    def ExecuteInitialize(self) -> None:
        """ExecuteInitialize(self: KratosDemStructuresCouplingApplication.ControlModuleFemDem2DUtilities) -> None"""
    def ExecuteInitializeSolutionStep(self) -> None:
        """ExecuteInitializeSolutionStep(self: KratosDemStructuresCouplingApplication.ControlModuleFemDem2DUtilities) -> None"""

class ControlModuleFemDemUtilities:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosDemStructuresCouplingApplication.ControlModuleFemDemUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None"""
    def ExecuteFinalizeSolutionStep(self) -> None:
        """ExecuteFinalizeSolutionStep(self: KratosDemStructuresCouplingApplication.ControlModuleFemDemUtilities) -> None"""
    def ExecuteInitialize(self) -> None:
        """ExecuteInitialize(self: KratosDemStructuresCouplingApplication.ControlModuleFemDemUtilities) -> None"""
    def ExecuteInitializeSolutionStep(self) -> None:
        """ExecuteInitializeSolutionStep(self: KratosDemStructuresCouplingApplication.ControlModuleFemDemUtilities) -> None"""

class ControlModuleProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDemStructuresCouplingApplication.ControlModuleProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class DemStructuresCouplingUtilities:
    def __init__(self) -> None:
        """__init__(self: KratosDemStructuresCouplingApplication.DemStructuresCouplingUtilities) -> None"""
    def CheckProvidedProperties(self, arg0: Kratos.Properties) -> str:
        """CheckProvidedProperties(self: KratosDemStructuresCouplingApplication.DemStructuresCouplingUtilities, arg0: Kratos.Properties) -> str"""
    def ComputeSandProduction(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: float) -> float:
        """ComputeSandProduction(self: KratosDemStructuresCouplingApplication.DemStructuresCouplingUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: float) -> float"""
    def ComputeSandProductionWithDepthFirstSearch(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: float) -> None:
        """ComputeSandProductionWithDepthFirstSearch(self: KratosDemStructuresCouplingApplication.DemStructuresCouplingUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: float) -> None"""
    def ComputeSandProductionWithDepthFirstSearchNonRecursiveImplementation(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: float) -> float:
        """ComputeSandProductionWithDepthFirstSearchNonRecursiveImplementation(self: KratosDemStructuresCouplingApplication.DemStructuresCouplingUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: float) -> float"""
    def ComputeTriaxialSandProduction(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart, arg3: float) -> None:
        """ComputeTriaxialSandProduction(self: KratosDemStructuresCouplingApplication.DemStructuresCouplingUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.ModelPart, arg3: float) -> None"""
    def MarkBrokenSpheres(self, arg0: Kratos.ModelPart) -> None:
        """MarkBrokenSpheres(self: KratosDemStructuresCouplingApplication.DemStructuresCouplingUtilities, arg0: Kratos.ModelPart) -> None"""
    def SmoothLoadTrasferredToFem(self, arg0: Kratos.ModelPart, arg1: float) -> None:
        """SmoothLoadTrasferredToFem(self: KratosDemStructuresCouplingApplication.DemStructuresCouplingUtilities, arg0: Kratos.ModelPart, arg1: float) -> None"""
    def TransferStructuresSkinToDem(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Properties) -> None:
        """TransferStructuresSkinToDem(self: KratosDemStructuresCouplingApplication.DemStructuresCouplingUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Properties) -> None"""

class EffectiveStressesCommunicatorUtility:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """__init__(self: KratosDemStructuresCouplingApplication.EffectiveStressesCommunicatorUtility, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
    def CommunicateCurrentRadialEffectiveStressesToDemWalls(self) -> None:
        """CommunicateCurrentRadialEffectiveStressesToDemWalls(self: KratosDemStructuresCouplingApplication.EffectiveStressesCommunicatorUtility) -> None"""
    def CommunicateGivenRadialEffectiveStressesToDemWalls(self, arg0: Kratos.Matrix) -> None:
        """CommunicateGivenRadialEffectiveStressesToDemWalls(self: KratosDemStructuresCouplingApplication.EffectiveStressesCommunicatorUtility, arg0: Kratos.Matrix) -> None"""
    def CopyWallCurrentEffectiveStressesToOldEffectiveStresses(self) -> None:
        """CopyWallCurrentEffectiveStressesToOldEffectiveStresses(self: KratosDemStructuresCouplingApplication.EffectiveStressesCommunicatorUtility) -> None"""
    def Initialize(self) -> None:
        """Initialize(self: KratosDemStructuresCouplingApplication.EffectiveStressesCommunicatorUtility) -> None"""

class InterpolateStructuralSolutionForDEM:
    def __init__(self) -> None:
        """__init__(self: KratosDemStructuresCouplingApplication.InterpolateStructuralSolutionForDEM) -> None"""
    def InterpolateStructuralSolution(self, arg0: Kratos.ModelPart, arg1: float, arg2: float, arg3: float, arg4: float) -> None:
        """InterpolateStructuralSolution(self: KratosDemStructuresCouplingApplication.InterpolateStructuralSolutionForDEM, arg0: Kratos.ModelPart, arg1: float, arg2: float, arg3: float, arg4: float) -> None"""
    def RestoreStructuralSolution(self, arg0: Kratos.ModelPart) -> None:
        """RestoreStructuralSolution(self: KratosDemStructuresCouplingApplication.InterpolateStructuralSolutionForDEM, arg0: Kratos.ModelPart) -> None"""
    def SaveStructuralSolution(self, arg0: Kratos.ModelPart) -> None:
        """SaveStructuralSolution(self: KratosDemStructuresCouplingApplication.InterpolateStructuralSolutionForDEM, arg0: Kratos.ModelPart) -> None"""

class KratosDemStructuresCouplingApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosDemStructuresCouplingApplication.KratosDemStructuresCouplingApplication) -> None"""

class MultiaxialControlModuleFEMDEMGeneralized2DUtilities:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosDemStructuresCouplingApplication.MultiaxialControlModuleFEMDEMGeneralized2DUtilities, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None"""
    def ExecuteFinalizeSolutionStep(self) -> None:
        """ExecuteFinalizeSolutionStep(self: KratosDemStructuresCouplingApplication.MultiaxialControlModuleFEMDEMGeneralized2DUtilities) -> None"""
    def ExecuteInitialize(self) -> None:
        """ExecuteInitialize(self: KratosDemStructuresCouplingApplication.MultiaxialControlModuleFEMDEMGeneralized2DUtilities) -> None"""
    def ExecuteInitializeSolutionStep(self) -> None:
        """ExecuteInitializeSolutionStep(self: KratosDemStructuresCouplingApplication.MultiaxialControlModuleFEMDEMGeneralized2DUtilities) -> None"""

class PermeabilityTensorCommunicatorUtility:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """__init__(self: KratosDemStructuresCouplingApplication.PermeabilityTensorCommunicatorUtility, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
    def Initialize(self) -> None:
        """Initialize(self: KratosDemStructuresCouplingApplication.PermeabilityTensorCommunicatorUtility) -> None"""
    def TrasferUpdatedPermeabilityTensor(self) -> None:
        """TrasferUpdatedPermeabilityTensor(self: KratosDemStructuresCouplingApplication.PermeabilityTensorCommunicatorUtility) -> None"""

class PorePressureCommunicatorUtility:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
        """__init__(self: KratosDemStructuresCouplingApplication.PorePressureCommunicatorUtility, arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None"""
    def ComputeForceOnParticlesDueToPorePressureGradient(self) -> None:
        """ComputeForceOnParticlesDueToPorePressureGradient(self: KratosDemStructuresCouplingApplication.PorePressureCommunicatorUtility) -> None"""
    def Initialize(self) -> None:
        """Initialize(self: KratosDemStructuresCouplingApplication.PorePressureCommunicatorUtility) -> None"""

class PostProcessUtilities:
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosDemStructuresCouplingApplication.PostProcessUtilities, arg0: Kratos.ModelPart) -> None"""
    def GetCurrentContinuumBonds(self, arg0: list) -> None:
        """GetCurrentContinuumBonds(self: KratosDemStructuresCouplingApplication.PostProcessUtilities, arg0: list) -> None"""
    def GetInitialContinuumBonds(self, arg0: list) -> None:
        """GetInitialContinuumBonds(self: KratosDemStructuresCouplingApplication.PostProcessUtilities, arg0: list) -> None"""
    def GetStickyStatus(self, arg0: list) -> None:
        """GetStickyStatus(self: KratosDemStructuresCouplingApplication.PostProcessUtilities, arg0: list) -> None"""

class SandProductionUtilities:
    def __init__(self) -> None:
        """__init__(self: KratosDemStructuresCouplingApplication.SandProductionUtilities) -> None"""
    def MarkSandProductionParticlesForErasing(self, arg0: Kratos.ModelPart) -> None:
        """MarkSandProductionParticlesForErasing(self: KratosDemStructuresCouplingApplication.SandProductionUtilities, arg0: Kratos.ModelPart) -> None"""

class StressFailureCheckUtilities:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosDemStructuresCouplingApplication.StressFailureCheckUtilities, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""
    def ExecuteFinalizeSolutionStep(self) -> None:
        """ExecuteFinalizeSolutionStep(self: KratosDemStructuresCouplingApplication.StressFailureCheckUtilities) -> None"""
