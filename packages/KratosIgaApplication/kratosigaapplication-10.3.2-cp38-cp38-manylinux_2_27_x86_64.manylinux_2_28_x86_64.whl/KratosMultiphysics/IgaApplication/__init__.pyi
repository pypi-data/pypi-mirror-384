import Kratos
from typing import ClassVar

class AdditiveSchwarzPreconditioner(Kratos.Preconditioner):
    def __init__(self) -> None:
        """__init__(self: KratosIgaApplication.AdditiveSchwarzPreconditioner) -> None"""

class AssignIgaExternalConditionsProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosIgaApplication.AssignIgaExternalConditionsProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class AssignIntegrationPointsToBackgroundElementsProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosIgaApplication.AssignIntegrationPointsToBackgroundElementsProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class DirectorUtilities:
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosIgaApplication.DirectorUtilities, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""
    def ComputeDirectors(self) -> None:
        """ComputeDirectors(self: KratosIgaApplication.DirectorUtilities) -> None"""

class EigensolverNitscheStabilizationScheme(Kratos.Scheme):
    def __init__(self) -> None:
        """__init__(self: KratosIgaApplication.EigensolverNitscheStabilizationScheme) -> None"""

class EigensolverNitscheStabilizationStrategy(Kratos.ImplicitSolvingStrategy):
    def __init__(self, model_part: Kratos.ModelPart, scheme: Kratos.Scheme, builder_and_solver: Kratos.BuilderAndSolver) -> None:
        """__init__(self: KratosIgaApplication.EigensolverNitscheStabilizationStrategy, model_part: Kratos.ModelPart, scheme: Kratos.Scheme, builder_and_solver: Kratos.BuilderAndSolver) -> None"""

class IgaFlags:
    FIX_DISPLACEMENT_X: ClassVar[Kratos.Flags] = ...
    FIX_DISPLACEMENT_Y: ClassVar[Kratos.Flags] = ...
    FIX_DISPLACEMENT_Z: ClassVar[Kratos.Flags] = ...
    FIX_ROTATION_X: ClassVar[Kratos.Flags] = ...
    FIX_ROTATION_Y: ClassVar[Kratos.Flags] = ...
    FIX_ROTATION_Z: ClassVar[Kratos.Flags] = ...
    def __init__(self) -> None:
        """__init__(self: KratosIgaApplication.IgaFlags) -> None"""

class KratosIgaApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosIgaApplication.KratosIgaApplication) -> None"""

class MapNurbsVolumeResultsToEmbeddedGeometryProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosIgaApplication.MapNurbsVolumeResultsToEmbeddedGeometryProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""
    def MapVariables(self) -> None:
        """MapVariables(self: KratosIgaApplication.MapNurbsVolumeResultsToEmbeddedGeometryProcess) -> None"""

class NitscheStabilizationModelPartProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart) -> None:
        """__init__(self: KratosIgaApplication.NitscheStabilizationModelPartProcess, arg0: Kratos.ModelPart) -> None"""

class OutputEigenValuesProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosIgaApplication.OutputEigenValuesProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""

class OutputQuadratureDomainProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosIgaApplication.OutputQuadratureDomainProcess, arg0: Kratos.Model, arg1: Kratos.Parameters) -> None"""
