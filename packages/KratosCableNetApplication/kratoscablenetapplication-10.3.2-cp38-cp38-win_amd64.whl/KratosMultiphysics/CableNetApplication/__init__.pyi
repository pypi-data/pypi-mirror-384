import Kratos

class ApplyWeakSlidingProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosCableNetApplication.ApplyWeakSlidingProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class EdgeCableElementProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosCableNetApplication.EdgeCableElementProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""

class EmpiricalSpringElementProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters, arg2: list[float]) -> None:
        """__init__(self: KratosCableNetApplication.EmpiricalSpringElementProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters, arg2: list[float]) -> None"""

class KratosCableNetApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosCableNetApplication.KratosCableNetApplication) -> None"""

class SlidingEdgeProcess(Kratos.Process):
    def __init__(self, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None:
        """__init__(self: KratosCableNetApplication.SlidingEdgeProcess, arg0: Kratos.ModelPart, arg1: Kratos.Parameters) -> None"""
