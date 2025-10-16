import Kratos
import KratosFluidDynamicsApplication
from typing import overload

class ApplyChimeraProcessFractionalStep2d(BaseApplyChimera2D):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosChimeraApplication.ApplyChimeraProcessFractionalStep2d, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class ApplyChimeraProcessFractionalStep3d(BaseApplyChimera3D):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosChimeraApplication.ApplyChimeraProcessFractionalStep3d, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class ApplyChimeraProcessMonolithic2d(BaseApplyChimera2D):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosChimeraApplication.ApplyChimeraProcessMonolithic2d, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class ApplyChimeraProcessMonolithic3d(BaseApplyChimera3D):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosChimeraApplication.ApplyChimeraProcessMonolithic3d, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class BaseApplyChimera2D(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosChimeraApplication.BaseApplyChimera2D, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""
    def SetEchoLevel(self, arg0: int) -> None:
        """SetEchoLevel(self: KratosChimeraApplication.BaseApplyChimera2D, arg0: int) -> None"""
    def SetReformulateEveryStep(self, arg0: bool) -> None:
        """SetReformulateEveryStep(self: KratosChimeraApplication.BaseApplyChimera2D, arg0: bool) -> None"""

class BaseApplyChimera3D(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosChimeraApplication.BaseApplyChimera3D, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""
    def SetEchoLevel(self, arg0: int) -> None:
        """SetEchoLevel(self: KratosChimeraApplication.BaseApplyChimera3D, arg0: int) -> None"""
    def SetReformulateEveryStep(self, arg0: bool) -> None:
        """SetReformulateEveryStep(self: KratosChimeraApplication.BaseApplyChimera3D, arg0: bool) -> None"""

class FractionalStepSettingsChimera(KratosFluidDynamicsApplication.BaseSettingsType):
    def __init__(self, arg0: Kratos.ModelPart, arg1: int, arg2: int, arg3: bool, arg4: bool, arg5: bool) -> None:
        """__init__(self: KratosChimeraApplication.FractionalStepSettingsChimera, arg0: Kratos.ModelPart, arg1: int, arg2: int, arg3: bool, arg4: bool, arg5: bool) -> None"""
    def GetStrategy(self, arg0: KratosFluidDynamicsApplication.StrategyLabel) -> Kratos.ImplicitSolvingStrategy:
        """GetStrategy(self: KratosChimeraApplication.FractionalStepSettingsChimera, arg0: KratosFluidDynamicsApplication.StrategyLabel) -> Kratos.ImplicitSolvingStrategy"""
    def SetEchoLevel(self, arg0: int) -> None:
        """SetEchoLevel(self: KratosChimeraApplication.FractionalStepSettingsChimera, arg0: int) -> None"""
    def SetStrategy(self, arg0: KratosFluidDynamicsApplication.StrategyLabel, arg1: Kratos.LinearSolver, arg2: float, arg3: int) -> None:
        """SetStrategy(self: KratosChimeraApplication.FractionalStepSettingsChimera, arg0: KratosFluidDynamicsApplication.StrategyLabel, arg1: Kratos.LinearSolver, arg2: float, arg3: int) -> None"""

class FractionalStepStrategyForChimera(KratosFluidDynamicsApplication.FractionalStepStrategy):
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: FractionalStepSettingsChimera, arg2: bool) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosChimeraApplication.FractionalStepStrategyForChimera, arg0: Kratos.ModelPart, arg1: KratosChimeraApplication.FractionalStepSettingsChimera, arg2: bool) -> None

        2. __init__(self: KratosChimeraApplication.FractionalStepStrategyForChimera, arg0: Kratos.ModelPart, arg1: KratosChimeraApplication.FractionalStepSettingsChimera, arg2: bool, arg3: bool) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.ModelPart, arg1: FractionalStepSettingsChimera, arg2: bool, arg3: bool) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosChimeraApplication.FractionalStepStrategyForChimera, arg0: Kratos.ModelPart, arg1: KratosChimeraApplication.FractionalStepSettingsChimera, arg2: bool) -> None

        2. __init__(self: KratosChimeraApplication.FractionalStepStrategyForChimera, arg0: Kratos.ModelPart, arg1: KratosChimeraApplication.FractionalStepSettingsChimera, arg2: bool, arg3: bool) -> None
        """

class KratosChimeraApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosChimeraApplication.KratosChimeraApplication) -> None"""

class ResidualBasedBlockBuilderAndSolverWithConstraintsForChimera(Kratos.ResidualBasedBlockBuilderAndSolver):
    def __init__(self, arg0: Kratos.LinearSolver) -> None:
        """__init__(self: KratosChimeraApplication.ResidualBasedBlockBuilderAndSolverWithConstraintsForChimera, arg0: Kratos.LinearSolver) -> None"""

class RotateRegionProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosChimeraApplication.RotateRegionProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

def TransferSolutionStepData(arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None:
    """TransferSolutionStepData(arg0: Kratos.ModelPart, arg1: Kratos.ModelPart) -> None

    Utility function to transfer the solution step data between the modelparts.
    """
