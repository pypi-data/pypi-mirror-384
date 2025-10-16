import Kratos
import Kratos.Globals
import Kratos.TensorAdaptors
from typing import ClassVar, overload

class AMGCLCoarseningType:
    """Members:

      RUGE_STUBEN

      AGGREGATION

      SA

      SA_EMIN"""
    __members__: ClassVar[dict] = ...  # read-only
    AGGREGATION: ClassVar[AMGCLCoarseningType] = ...
    RUGE_STUBEN: ClassVar[AMGCLCoarseningType] = ...
    SA: ClassVar[AMGCLCoarseningType] = ...
    SA_EMIN: ClassVar[AMGCLCoarseningType] = ...
    __entries: ClassVar[dict] = ...
    def __init__(self, value: int) -> None:
        """__init__(self: Kratos.Future.AMGCLCoarseningType, value: int) -> None"""
    def __eq__(self, other: object) -> bool:
        """__eq__(self: object, other: object) -> bool"""
    def __hash__(self) -> int:
        """__hash__(self: object) -> int"""
    def __index__(self) -> int:
        """__index__(self: Kratos.Future.AMGCLCoarseningType) -> int"""
    def __int__(self) -> int:
        """__int__(self: Kratos.Future.AMGCLCoarseningType) -> int"""
    def __ne__(self, other: object) -> bool:
        """__ne__(self: object, other: object) -> bool"""
    @property
    def name(self) -> str:
        """name(self: object) -> str

        name(self: object) -> str
        """
    @property
    def value(self) -> int:
        """(arg0: Kratos.Future.AMGCLCoarseningType) -> int"""

class AMGCLIterativeSolverType:
    """Members:

      GMRES

      LGMRES

      FGMRES

      BICGSTAB

      CG

      BICGSTAB_WITH_GMRES_FALLBACK

      BICGSTAB2"""
    __members__: ClassVar[dict] = ...  # read-only
    BICGSTAB: ClassVar[AMGCLIterativeSolverType] = ...
    BICGSTAB2: ClassVar[AMGCLIterativeSolverType] = ...
    BICGSTAB_WITH_GMRES_FALLBACK: ClassVar[AMGCLIterativeSolverType] = ...
    CG: ClassVar[AMGCLIterativeSolverType] = ...
    FGMRES: ClassVar[AMGCLIterativeSolverType] = ...
    GMRES: ClassVar[AMGCLIterativeSolverType] = ...
    LGMRES: ClassVar[AMGCLIterativeSolverType] = ...
    __entries: ClassVar[dict] = ...
    def __init__(self, value: int) -> None:
        """__init__(self: Kratos.Future.AMGCLIterativeSolverType, value: int) -> None"""
    def __eq__(self, other: object) -> bool:
        """__eq__(self: object, other: object) -> bool"""
    def __hash__(self) -> int:
        """__hash__(self: object) -> int"""
    def __index__(self) -> int:
        """__index__(self: Kratos.Future.AMGCLIterativeSolverType) -> int"""
    def __int__(self) -> int:
        """__int__(self: Kratos.Future.AMGCLIterativeSolverType) -> int"""
    def __ne__(self, other: object) -> bool:
        """__ne__(self: object, other: object) -> bool"""
    @property
    def name(self) -> str:
        """name(self: object) -> str

        name(self: object) -> str
        """
    @property
    def value(self) -> int:
        """(arg0: Kratos.Future.AMGCLIterativeSolverType) -> int"""

class AMGCLSmoother:
    """Members:

      SPAI0

      SPAI1

      ILU0

      DAMPED_JACOBI

      GAUSS_SEIDEL

      CHEBYSHEV"""
    __members__: ClassVar[dict] = ...  # read-only
    CHEBYSHEV: ClassVar[AMGCLSmoother] = ...
    DAMPED_JACOBI: ClassVar[AMGCLSmoother] = ...
    GAUSS_SEIDEL: ClassVar[AMGCLSmoother] = ...
    ILU0: ClassVar[AMGCLSmoother] = ...
    SPAI0: ClassVar[AMGCLSmoother] = ...
    SPAI1: ClassVar[AMGCLSmoother] = ...
    __entries: ClassVar[dict] = ...
    def __init__(self, value: int) -> None:
        """__init__(self: Kratos.Future.AMGCLSmoother, value: int) -> None"""
    def __eq__(self, other: object) -> bool:
        """__eq__(self: object, other: object) -> bool"""
    def __hash__(self) -> int:
        """__hash__(self: object) -> int"""
    def __index__(self) -> int:
        """__index__(self: Kratos.Future.AMGCLSmoother) -> int"""
    def __int__(self) -> int:
        """__int__(self: Kratos.Future.AMGCLSmoother) -> int"""
    def __ne__(self, other: object) -> bool:
        """__ne__(self: object, other: object) -> bool"""
    @property
    def name(self) -> str:
        """name(self: object) -> str

        name(self: object) -> str
        """
    @property
    def value(self) -> int:
        """(arg0: Kratos.Future.AMGCLSmoother) -> int"""

class AMGCLSolver(LinearSolver):
    @overload
    def __init__(self, arg0: AMGCLSmoother, arg1: AMGCLIterativeSolverType, arg2: float, arg3: int, arg4: int, arg5: int) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.Future.AMGCLSolver, arg0: Kratos.Future.AMGCLSmoother, arg1: Kratos.Future.AMGCLIterativeSolverType, arg2: float, arg3: int, arg4: int, arg5: int) -> None

        2. __init__(self: Kratos.Future.AMGCLSolver, arg0: Kratos.Future.AMGCLSmoother, arg1: Kratos.Future.AMGCLIterativeSolverType, arg2: Kratos.Future.AMGCLCoarseningType, arg3: float, arg4: int, arg5: int, arg6: int, arg7: bool) -> None

        3. __init__(self: Kratos.Future.AMGCLSolver) -> None

        4. __init__(self: Kratos.Future.AMGCLSolver, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: AMGCLSmoother, arg1: AMGCLIterativeSolverType, arg2: AMGCLCoarseningType, arg3: float, arg4: int, arg5: int, arg6: int, arg7: bool) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.Future.AMGCLSolver, arg0: Kratos.Future.AMGCLSmoother, arg1: Kratos.Future.AMGCLIterativeSolverType, arg2: float, arg3: int, arg4: int, arg5: int) -> None

        2. __init__(self: Kratos.Future.AMGCLSolver, arg0: Kratos.Future.AMGCLSmoother, arg1: Kratos.Future.AMGCLIterativeSolverType, arg2: Kratos.Future.AMGCLCoarseningType, arg3: float, arg4: int, arg5: int, arg6: int, arg7: bool) -> None

        3. __init__(self: Kratos.Future.AMGCLSolver) -> None

        4. __init__(self: Kratos.Future.AMGCLSolver, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.Future.AMGCLSolver, arg0: Kratos.Future.AMGCLSmoother, arg1: Kratos.Future.AMGCLIterativeSolverType, arg2: float, arg3: int, arg4: int, arg5: int) -> None

        2. __init__(self: Kratos.Future.AMGCLSolver, arg0: Kratos.Future.AMGCLSmoother, arg1: Kratos.Future.AMGCLIterativeSolverType, arg2: Kratos.Future.AMGCLCoarseningType, arg3: float, arg4: int, arg5: int, arg6: int, arg7: bool) -> None

        3. __init__(self: Kratos.Future.AMGCLSolver) -> None

        4. __init__(self: Kratos.Future.AMGCLSolver, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.Future.AMGCLSolver, arg0: Kratos.Future.AMGCLSmoother, arg1: Kratos.Future.AMGCLIterativeSolverType, arg2: float, arg3: int, arg4: int, arg5: int) -> None

        2. __init__(self: Kratos.Future.AMGCLSolver, arg0: Kratos.Future.AMGCLSmoother, arg1: Kratos.Future.AMGCLIterativeSolverType, arg2: Kratos.Future.AMGCLCoarseningType, arg3: float, arg4: int, arg5: int, arg6: int, arg7: bool) -> None

        3. __init__(self: Kratos.Future.AMGCLSolver) -> None

        4. __init__(self: Kratos.Future.AMGCLSolver, arg0: Kratos.Parameters) -> None
        """
    def GetResidualNorm(self) -> float:
        """GetResidualNorm(self: Kratos.Future.AMGCLSolver) -> float"""

class DirectSolver(LinearSolver):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.Future.DirectSolver) -> None

        2. __init__(self: Kratos.Future.DirectSolver, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.Future.DirectSolver) -> None

        2. __init__(self: Kratos.Future.DirectSolver, arg0: Kratos.Parameters) -> None
        """

class LinearSolver:
    def __init__(self) -> None:
        """__init__(self: Kratos.Future.LinearSolver) -> None"""
    def GetIterationsNumber(self) -> int:
        """GetIterationsNumber(self: Kratos.Future.LinearSolver) -> int"""
    def Initialize(self, arg0: Kratos.CsrMatrix, arg1: Kratos.SystemVector, arg2: Kratos.SystemVector) -> None:
        """Initialize(self: Kratos.Future.LinearSolver, arg0: Kratos.CsrMatrix, arg1: Kratos.SystemVector, arg2: Kratos.SystemVector) -> None"""

class Process(Kratos.Flags):
    def __init__(self) -> None:
        """__init__(self: Kratos.Future.Process) -> None"""
    def Execute(self) -> None:
        """Execute(self: Kratos.Future.Process) -> None"""
    def Info(self) -> str:
        """Info(self: Kratos.Future.Process) -> str"""

class SkylineLUFactorizationSolver(DirectSolver):
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.Future.SkylineLUFactorizationSolver) -> None

        2. __init__(self: Kratos.Future.SkylineLUFactorizationSolver, arg0: Kratos.Parameters) -> None
        """
    @overload
    def __init__(self, arg0: Kratos.Parameters) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.Future.SkylineLUFactorizationSolver) -> None

        2. __init__(self: Kratos.Future.SkylineLUFactorizationSolver, arg0: Kratos.Parameters) -> None
        """

class VtuOutput:
    class WriterFormat:
        """Members:

          ASCII

          BINARY

          RAW

          COMPRESSED_RAW"""
        __members__: ClassVar[dict] = ...  # read-only
        ASCII: ClassVar[VtuOutput.WriterFormat] = ...
        BINARY: ClassVar[VtuOutput.WriterFormat] = ...
        COMPRESSED_RAW: ClassVar[VtuOutput.WriterFormat] = ...
        RAW: ClassVar[VtuOutput.WriterFormat] = ...
        __entries: ClassVar[dict] = ...
        def __init__(self, value: int) -> None:
            """__init__(self: Kratos.Future.VtuOutput.WriterFormat, value: int) -> None"""
        def __eq__(self, other: object) -> bool:
            """__eq__(self: object, other: object) -> bool"""
        def __hash__(self) -> int:
            """__hash__(self: object) -> int"""
        def __index__(self) -> int:
            """__index__(self: Kratos.Future.VtuOutput.WriterFormat) -> int"""
        def __int__(self) -> int:
            """__int__(self: Kratos.Future.VtuOutput.WriterFormat) -> int"""
        def __ne__(self, other: object) -> bool:
            """__ne__(self: object, other: object) -> bool"""
        @property
        def name(self) -> str:
            """name(self: object) -> str

            name(self: object) -> str
            """
        @property
        def value(self) -> int:
            """(arg0: Kratos.Future.VtuOutput.WriterFormat) -> int"""
    ASCII: ClassVar[VtuOutput.WriterFormat] = ...
    BINARY: ClassVar[VtuOutput.WriterFormat] = ...
    COMPRESSED_RAW: ClassVar[VtuOutput.WriterFormat] = ...
    RAW: ClassVar[VtuOutput.WriterFormat] = ...
    def __init__(self, model_part: Kratos.ModelPart, configuration: Kratos.Configuration = ..., output_format: VtuOutput.WriterFormat = ..., precision: int = ..., output_sub_model_parts: bool = ..., write_ids: bool = ..., echo_level: int = ...) -> None:
        """__init__(self: Kratos.Future.VtuOutput, model_part: Kratos.ModelPart, configuration: Kratos.Configuration = <Configuration.Initial: 0>, output_format: Kratos.Future.VtuOutput.WriterFormat = <WriterFormat.COMPRESSED_RAW: 3>, precision: int = 9, output_sub_model_parts: bool = False, write_ids: bool = False, echo_level: int = 0) -> None"""
    def AddFlag(self, flag_name: str, flag: Kratos.Flags, data_location: Kratos.Globals.DataLocation) -> None:
        """AddFlag(self: Kratos.Future.VtuOutput, flag_name: str, flag: Kratos.Flags, data_location: Kratos.Globals.DataLocation) -> None"""
    @overload
    def AddIntegrationPointVariable(self, variable: Kratos.IntegerVariable, data_location: Kratos.Globals.DataLocation) -> None:
        """AddIntegrationPointVariable(*args, **kwargs)
        Overloaded function.

        1. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.IntegerVariable, data_location: Kratos.Globals.DataLocation) -> None

        2. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.DoubleVariable, data_location: Kratos.Globals.DataLocation) -> None

        3. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable3, data_location: Kratos.Globals.DataLocation) -> None

        4. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable4, data_location: Kratos.Globals.DataLocation) -> None

        5. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable6, data_location: Kratos.Globals.DataLocation) -> None

        6. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable9, data_location: Kratos.Globals.DataLocation) -> None

        7. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.VectorVariable, data_location: Kratos.Globals.DataLocation) -> None

        8. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.MatrixVariable, data_location: Kratos.Globals.DataLocation) -> None
        """
    @overload
    def AddIntegrationPointVariable(self, variable: Kratos.DoubleVariable, data_location: Kratos.Globals.DataLocation) -> None:
        """AddIntegrationPointVariable(*args, **kwargs)
        Overloaded function.

        1. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.IntegerVariable, data_location: Kratos.Globals.DataLocation) -> None

        2. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.DoubleVariable, data_location: Kratos.Globals.DataLocation) -> None

        3. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable3, data_location: Kratos.Globals.DataLocation) -> None

        4. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable4, data_location: Kratos.Globals.DataLocation) -> None

        5. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable6, data_location: Kratos.Globals.DataLocation) -> None

        6. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable9, data_location: Kratos.Globals.DataLocation) -> None

        7. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.VectorVariable, data_location: Kratos.Globals.DataLocation) -> None

        8. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.MatrixVariable, data_location: Kratos.Globals.DataLocation) -> None
        """
    @overload
    def AddIntegrationPointVariable(self, variable: Kratos.Array1DVariable3, data_location: Kratos.Globals.DataLocation) -> None:
        """AddIntegrationPointVariable(*args, **kwargs)
        Overloaded function.

        1. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.IntegerVariable, data_location: Kratos.Globals.DataLocation) -> None

        2. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.DoubleVariable, data_location: Kratos.Globals.DataLocation) -> None

        3. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable3, data_location: Kratos.Globals.DataLocation) -> None

        4. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable4, data_location: Kratos.Globals.DataLocation) -> None

        5. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable6, data_location: Kratos.Globals.DataLocation) -> None

        6. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable9, data_location: Kratos.Globals.DataLocation) -> None

        7. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.VectorVariable, data_location: Kratos.Globals.DataLocation) -> None

        8. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.MatrixVariable, data_location: Kratos.Globals.DataLocation) -> None
        """
    @overload
    def AddIntegrationPointVariable(self, variable: Kratos.Array1DVariable4, data_location: Kratos.Globals.DataLocation) -> None:
        """AddIntegrationPointVariable(*args, **kwargs)
        Overloaded function.

        1. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.IntegerVariable, data_location: Kratos.Globals.DataLocation) -> None

        2. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.DoubleVariable, data_location: Kratos.Globals.DataLocation) -> None

        3. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable3, data_location: Kratos.Globals.DataLocation) -> None

        4. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable4, data_location: Kratos.Globals.DataLocation) -> None

        5. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable6, data_location: Kratos.Globals.DataLocation) -> None

        6. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable9, data_location: Kratos.Globals.DataLocation) -> None

        7. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.VectorVariable, data_location: Kratos.Globals.DataLocation) -> None

        8. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.MatrixVariable, data_location: Kratos.Globals.DataLocation) -> None
        """
    @overload
    def AddIntegrationPointVariable(self, variable: Kratos.Array1DVariable6, data_location: Kratos.Globals.DataLocation) -> None:
        """AddIntegrationPointVariable(*args, **kwargs)
        Overloaded function.

        1. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.IntegerVariable, data_location: Kratos.Globals.DataLocation) -> None

        2. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.DoubleVariable, data_location: Kratos.Globals.DataLocation) -> None

        3. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable3, data_location: Kratos.Globals.DataLocation) -> None

        4. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable4, data_location: Kratos.Globals.DataLocation) -> None

        5. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable6, data_location: Kratos.Globals.DataLocation) -> None

        6. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable9, data_location: Kratos.Globals.DataLocation) -> None

        7. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.VectorVariable, data_location: Kratos.Globals.DataLocation) -> None

        8. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.MatrixVariable, data_location: Kratos.Globals.DataLocation) -> None
        """
    @overload
    def AddIntegrationPointVariable(self, variable: Kratos.Array1DVariable9, data_location: Kratos.Globals.DataLocation) -> None:
        """AddIntegrationPointVariable(*args, **kwargs)
        Overloaded function.

        1. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.IntegerVariable, data_location: Kratos.Globals.DataLocation) -> None

        2. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.DoubleVariable, data_location: Kratos.Globals.DataLocation) -> None

        3. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable3, data_location: Kratos.Globals.DataLocation) -> None

        4. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable4, data_location: Kratos.Globals.DataLocation) -> None

        5. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable6, data_location: Kratos.Globals.DataLocation) -> None

        6. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable9, data_location: Kratos.Globals.DataLocation) -> None

        7. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.VectorVariable, data_location: Kratos.Globals.DataLocation) -> None

        8. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.MatrixVariable, data_location: Kratos.Globals.DataLocation) -> None
        """
    @overload
    def AddIntegrationPointVariable(self, variable: Kratos.VectorVariable, data_location: Kratos.Globals.DataLocation) -> None:
        """AddIntegrationPointVariable(*args, **kwargs)
        Overloaded function.

        1. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.IntegerVariable, data_location: Kratos.Globals.DataLocation) -> None

        2. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.DoubleVariable, data_location: Kratos.Globals.DataLocation) -> None

        3. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable3, data_location: Kratos.Globals.DataLocation) -> None

        4. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable4, data_location: Kratos.Globals.DataLocation) -> None

        5. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable6, data_location: Kratos.Globals.DataLocation) -> None

        6. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable9, data_location: Kratos.Globals.DataLocation) -> None

        7. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.VectorVariable, data_location: Kratos.Globals.DataLocation) -> None

        8. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.MatrixVariable, data_location: Kratos.Globals.DataLocation) -> None
        """
    @overload
    def AddIntegrationPointVariable(self, variable: Kratos.MatrixVariable, data_location: Kratos.Globals.DataLocation) -> None:
        """AddIntegrationPointVariable(*args, **kwargs)
        Overloaded function.

        1. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.IntegerVariable, data_location: Kratos.Globals.DataLocation) -> None

        2. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.DoubleVariable, data_location: Kratos.Globals.DataLocation) -> None

        3. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable3, data_location: Kratos.Globals.DataLocation) -> None

        4. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable4, data_location: Kratos.Globals.DataLocation) -> None

        5. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable6, data_location: Kratos.Globals.DataLocation) -> None

        6. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable9, data_location: Kratos.Globals.DataLocation) -> None

        7. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.VectorVariable, data_location: Kratos.Globals.DataLocation) -> None

        8. AddIntegrationPointVariable(self: Kratos.Future.VtuOutput, variable: Kratos.MatrixVariable, data_location: Kratos.Globals.DataLocation) -> None
        """
    @overload
    def AddTensorAdaptor(self, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.BoolTensorAdaptor) -> None:
        """AddTensorAdaptor(*args, **kwargs)
        Overloaded function.

        1. AddTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.BoolTensorAdaptor) -> None

        2. AddTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.IntTensorAdaptor) -> None

        3. AddTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor) -> None
        """
    @overload
    def AddTensorAdaptor(self, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.IntTensorAdaptor) -> None:
        """AddTensorAdaptor(*args, **kwargs)
        Overloaded function.

        1. AddTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.BoolTensorAdaptor) -> None

        2. AddTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.IntTensorAdaptor) -> None

        3. AddTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor) -> None
        """
    @overload
    def AddTensorAdaptor(self, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor) -> None:
        """AddTensorAdaptor(*args, **kwargs)
        Overloaded function.

        1. AddTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.BoolTensorAdaptor) -> None

        2. AddTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.IntTensorAdaptor) -> None

        3. AddTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor) -> None
        """
    @overload
    def AddVariable(self, variable: Kratos.IntegerVariable, data_location: Kratos.Globals.DataLocation) -> None:
        """AddVariable(*args, **kwargs)
        Overloaded function.

        1. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.IntegerVariable, data_location: Kratos.Globals.DataLocation) -> None

        2. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.DoubleVariable, data_location: Kratos.Globals.DataLocation) -> None

        3. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable3, data_location: Kratos.Globals.DataLocation) -> None

        4. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable4, data_location: Kratos.Globals.DataLocation) -> None

        5. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable6, data_location: Kratos.Globals.DataLocation) -> None

        6. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable9, data_location: Kratos.Globals.DataLocation) -> None

        7. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.VectorVariable, data_location: Kratos.Globals.DataLocation) -> None

        8. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.MatrixVariable, data_location: Kratos.Globals.DataLocation) -> None
        """
    @overload
    def AddVariable(self, variable: Kratos.DoubleVariable, data_location: Kratos.Globals.DataLocation) -> None:
        """AddVariable(*args, **kwargs)
        Overloaded function.

        1. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.IntegerVariable, data_location: Kratos.Globals.DataLocation) -> None

        2. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.DoubleVariable, data_location: Kratos.Globals.DataLocation) -> None

        3. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable3, data_location: Kratos.Globals.DataLocation) -> None

        4. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable4, data_location: Kratos.Globals.DataLocation) -> None

        5. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable6, data_location: Kratos.Globals.DataLocation) -> None

        6. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable9, data_location: Kratos.Globals.DataLocation) -> None

        7. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.VectorVariable, data_location: Kratos.Globals.DataLocation) -> None

        8. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.MatrixVariable, data_location: Kratos.Globals.DataLocation) -> None
        """
    @overload
    def AddVariable(self, variable: Kratos.Array1DVariable3, data_location: Kratos.Globals.DataLocation) -> None:
        """AddVariable(*args, **kwargs)
        Overloaded function.

        1. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.IntegerVariable, data_location: Kratos.Globals.DataLocation) -> None

        2. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.DoubleVariable, data_location: Kratos.Globals.DataLocation) -> None

        3. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable3, data_location: Kratos.Globals.DataLocation) -> None

        4. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable4, data_location: Kratos.Globals.DataLocation) -> None

        5. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable6, data_location: Kratos.Globals.DataLocation) -> None

        6. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable9, data_location: Kratos.Globals.DataLocation) -> None

        7. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.VectorVariable, data_location: Kratos.Globals.DataLocation) -> None

        8. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.MatrixVariable, data_location: Kratos.Globals.DataLocation) -> None
        """
    @overload
    def AddVariable(self, variable: Kratos.Array1DVariable4, data_location: Kratos.Globals.DataLocation) -> None:
        """AddVariable(*args, **kwargs)
        Overloaded function.

        1. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.IntegerVariable, data_location: Kratos.Globals.DataLocation) -> None

        2. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.DoubleVariable, data_location: Kratos.Globals.DataLocation) -> None

        3. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable3, data_location: Kratos.Globals.DataLocation) -> None

        4. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable4, data_location: Kratos.Globals.DataLocation) -> None

        5. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable6, data_location: Kratos.Globals.DataLocation) -> None

        6. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable9, data_location: Kratos.Globals.DataLocation) -> None

        7. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.VectorVariable, data_location: Kratos.Globals.DataLocation) -> None

        8. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.MatrixVariable, data_location: Kratos.Globals.DataLocation) -> None
        """
    @overload
    def AddVariable(self, variable: Kratos.Array1DVariable6, data_location: Kratos.Globals.DataLocation) -> None:
        """AddVariable(*args, **kwargs)
        Overloaded function.

        1. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.IntegerVariable, data_location: Kratos.Globals.DataLocation) -> None

        2. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.DoubleVariable, data_location: Kratos.Globals.DataLocation) -> None

        3. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable3, data_location: Kratos.Globals.DataLocation) -> None

        4. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable4, data_location: Kratos.Globals.DataLocation) -> None

        5. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable6, data_location: Kratos.Globals.DataLocation) -> None

        6. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable9, data_location: Kratos.Globals.DataLocation) -> None

        7. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.VectorVariable, data_location: Kratos.Globals.DataLocation) -> None

        8. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.MatrixVariable, data_location: Kratos.Globals.DataLocation) -> None
        """
    @overload
    def AddVariable(self, variable: Kratos.Array1DVariable9, data_location: Kratos.Globals.DataLocation) -> None:
        """AddVariable(*args, **kwargs)
        Overloaded function.

        1. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.IntegerVariable, data_location: Kratos.Globals.DataLocation) -> None

        2. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.DoubleVariable, data_location: Kratos.Globals.DataLocation) -> None

        3. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable3, data_location: Kratos.Globals.DataLocation) -> None

        4. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable4, data_location: Kratos.Globals.DataLocation) -> None

        5. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable6, data_location: Kratos.Globals.DataLocation) -> None

        6. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable9, data_location: Kratos.Globals.DataLocation) -> None

        7. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.VectorVariable, data_location: Kratos.Globals.DataLocation) -> None

        8. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.MatrixVariable, data_location: Kratos.Globals.DataLocation) -> None
        """
    @overload
    def AddVariable(self, variable: Kratos.VectorVariable, data_location: Kratos.Globals.DataLocation) -> None:
        """AddVariable(*args, **kwargs)
        Overloaded function.

        1. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.IntegerVariable, data_location: Kratos.Globals.DataLocation) -> None

        2. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.DoubleVariable, data_location: Kratos.Globals.DataLocation) -> None

        3. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable3, data_location: Kratos.Globals.DataLocation) -> None

        4. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable4, data_location: Kratos.Globals.DataLocation) -> None

        5. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable6, data_location: Kratos.Globals.DataLocation) -> None

        6. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable9, data_location: Kratos.Globals.DataLocation) -> None

        7. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.VectorVariable, data_location: Kratos.Globals.DataLocation) -> None

        8. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.MatrixVariable, data_location: Kratos.Globals.DataLocation) -> None
        """
    @overload
    def AddVariable(self, variable: Kratos.MatrixVariable, data_location: Kratos.Globals.DataLocation) -> None:
        """AddVariable(*args, **kwargs)
        Overloaded function.

        1. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.IntegerVariable, data_location: Kratos.Globals.DataLocation) -> None

        2. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.DoubleVariable, data_location: Kratos.Globals.DataLocation) -> None

        3. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable3, data_location: Kratos.Globals.DataLocation) -> None

        4. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable4, data_location: Kratos.Globals.DataLocation) -> None

        5. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable6, data_location: Kratos.Globals.DataLocation) -> None

        6. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.Array1DVariable9, data_location: Kratos.Globals.DataLocation) -> None

        7. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.VectorVariable, data_location: Kratos.Globals.DataLocation) -> None

        8. AddVariable(self: Kratos.Future.VtuOutput, variable: Kratos.MatrixVariable, data_location: Kratos.Globals.DataLocation) -> None
        """
    @overload
    def EmplaceTensorAdaptor(self, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.BoolTensorAdaptor) -> None:
        """EmplaceTensorAdaptor(*args, **kwargs)
        Overloaded function.

        1. EmplaceTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.BoolTensorAdaptor) -> None

        2. EmplaceTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.IntTensorAdaptor) -> None

        3. EmplaceTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor) -> None
        """
    @overload
    def EmplaceTensorAdaptor(self, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.IntTensorAdaptor) -> None:
        """EmplaceTensorAdaptor(*args, **kwargs)
        Overloaded function.

        1. EmplaceTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.BoolTensorAdaptor) -> None

        2. EmplaceTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.IntTensorAdaptor) -> None

        3. EmplaceTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor) -> None
        """
    @overload
    def EmplaceTensorAdaptor(self, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor) -> None:
        """EmplaceTensorAdaptor(*args, **kwargs)
        Overloaded function.

        1. EmplaceTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.BoolTensorAdaptor) -> None

        2. EmplaceTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.IntTensorAdaptor) -> None

        3. EmplaceTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor) -> None
        """
    def GetModelPart(self) -> Kratos.ModelPart:
        """GetModelPart(self: Kratos.Future.VtuOutput) -> Kratos.ModelPart"""
    def GetOutputContainerList(self) -> list[Kratos.NodesArray | Kratos.ConditionsArray | Kratos.ElementsArray]:
        """GetOutputContainerList(self: Kratos.Future.VtuOutput) -> list[Union[Kratos.NodesArray, Kratos.ConditionsArray, Kratos.ElementsArray]]"""
    def PrintOutput(self, output_file_name_prefix: str) -> None:
        """PrintOutput(self: Kratos.Future.VtuOutput, output_file_name_prefix: str) -> None"""
    @overload
    def ReplaceTensorAdaptor(self, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.BoolTensorAdaptor) -> None:
        """ReplaceTensorAdaptor(*args, **kwargs)
        Overloaded function.

        1. ReplaceTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.BoolTensorAdaptor) -> None

        2. ReplaceTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.IntTensorAdaptor) -> None

        3. ReplaceTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor) -> None
        """
    @overload
    def ReplaceTensorAdaptor(self, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.IntTensorAdaptor) -> None:
        """ReplaceTensorAdaptor(*args, **kwargs)
        Overloaded function.

        1. ReplaceTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.BoolTensorAdaptor) -> None

        2. ReplaceTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.IntTensorAdaptor) -> None

        3. ReplaceTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor) -> None
        """
    @overload
    def ReplaceTensorAdaptor(self, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor) -> None:
        """ReplaceTensorAdaptor(*args, **kwargs)
        Overloaded function.

        1. ReplaceTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.BoolTensorAdaptor) -> None

        2. ReplaceTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.IntTensorAdaptor) -> None

        3. ReplaceTensorAdaptor(self: Kratos.Future.VtuOutput, tensor_adaptor_name: str, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor) -> None
        """
