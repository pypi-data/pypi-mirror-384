import Kratos
import numpy
from typing import overload

class BoolCombinedTensorAdaptor(BoolTensorAdaptor):
    @overload
    def __init__(self, list_of_tensor_adaptors: list[BoolTensorAdaptor], perform_collect_data_recursively: bool = ..., perform_store_data_recursively: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.BoolCombinedTensorAdaptor, list_of_tensor_adaptors: list[Kratos.TensorAdaptors.BoolTensorAdaptor], perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True) -> None

        2. __init__(self: Kratos.TensorAdaptors.BoolCombinedTensorAdaptor, list_of_tensor_adaptors: list[Kratos.TensorAdaptors.BoolTensorAdaptor], axis: int, perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True) -> None

        3. __init__(self: Kratos.TensorAdaptors.BoolCombinedTensorAdaptor, list_of_tensor_adaptors: Kratos.TensorAdaptors.BoolCombinedTensorAdaptor, perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True, copy: bool = True) -> None
        """
    @overload
    def __init__(self, list_of_tensor_adaptors: list[BoolTensorAdaptor], axis: int, perform_collect_data_recursively: bool = ..., perform_store_data_recursively: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.BoolCombinedTensorAdaptor, list_of_tensor_adaptors: list[Kratos.TensorAdaptors.BoolTensorAdaptor], perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True) -> None

        2. __init__(self: Kratos.TensorAdaptors.BoolCombinedTensorAdaptor, list_of_tensor_adaptors: list[Kratos.TensorAdaptors.BoolTensorAdaptor], axis: int, perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True) -> None

        3. __init__(self: Kratos.TensorAdaptors.BoolCombinedTensorAdaptor, list_of_tensor_adaptors: Kratos.TensorAdaptors.BoolCombinedTensorAdaptor, perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True, copy: bool = True) -> None
        """
    @overload
    def __init__(self, list_of_tensor_adaptors: BoolCombinedTensorAdaptor, perform_collect_data_recursively: bool = ..., perform_store_data_recursively: bool = ..., copy: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.BoolCombinedTensorAdaptor, list_of_tensor_adaptors: list[Kratos.TensorAdaptors.BoolTensorAdaptor], perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True) -> None

        2. __init__(self: Kratos.TensorAdaptors.BoolCombinedTensorAdaptor, list_of_tensor_adaptors: list[Kratos.TensorAdaptors.BoolTensorAdaptor], axis: int, perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True) -> None

        3. __init__(self: Kratos.TensorAdaptors.BoolCombinedTensorAdaptor, list_of_tensor_adaptors: Kratos.TensorAdaptors.BoolCombinedTensorAdaptor, perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True, copy: bool = True) -> None
        """
    def GetTensorAdaptors(self) -> list[BoolTensorAdaptor]:
        """GetTensorAdaptors(self: Kratos.TensorAdaptors.BoolCombinedTensorAdaptor) -> list[Kratos.TensorAdaptors.BoolTensorAdaptor]"""

class BoolTensorAdaptor:
    data: numpy.ndarray[bool]
    @overload
    def __init__(self, container: Kratos.DofsArrayType | Kratos.NodesArray | Kratos.ConditionsArray | Kratos.ElementsArray | Kratos.PropertiesArray | Kratos.MasterSlaveConstraintsArray | Kratos.GeometryContainerType, nd_data: Kratos.BoolNDData, copy: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.BoolTensorAdaptor, container: Union[Kratos.DofsArrayType, Kratos.NodesArray, Kratos.ConditionsArray, Kratos.ElementsArray, Kratos.PropertiesArray, Kratos.MasterSlaveConstraintsArray, Kratos.GeometryContainerType], nd_data: Kratos.BoolNDData, copy: bool = True) -> None

        2. __init__(self: Kratos.TensorAdaptors.BoolTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.BoolTensorAdaptor, copy: bool = True) -> None
        """
    @overload
    def __init__(self, tensor_adaptor: BoolTensorAdaptor, copy: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.BoolTensorAdaptor, container: Union[Kratos.DofsArrayType, Kratos.NodesArray, Kratos.ConditionsArray, Kratos.ElementsArray, Kratos.PropertiesArray, Kratos.MasterSlaveConstraintsArray, Kratos.GeometryContainerType], nd_data: Kratos.BoolNDData, copy: bool = True) -> None

        2. __init__(self: Kratos.TensorAdaptors.BoolTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.BoolTensorAdaptor, copy: bool = True) -> None
        """
    def Check(self) -> None:
        """Check(self: Kratos.TensorAdaptors.BoolTensorAdaptor) -> None"""
    def CollectData(self) -> None:
        """CollectData(self: Kratos.TensorAdaptors.BoolTensorAdaptor) -> None"""
    def DataShape(self) -> Kratos.DenseVectorUnsignedInt:
        """DataShape(self: Kratos.TensorAdaptors.BoolTensorAdaptor) -> Kratos.DenseVectorUnsignedInt"""
    def GetContainer(self) -> Kratos.DofsArrayType | Kratos.NodesArray | Kratos.ConditionsArray | Kratos.ElementsArray | Kratos.PropertiesArray | Kratos.MasterSlaveConstraintsArray | Kratos.GeometryContainerType:
        """GetContainer(self: Kratos.TensorAdaptors.BoolTensorAdaptor) -> Union[Kratos.DofsArrayType, Kratos.NodesArray, Kratos.ConditionsArray, Kratos.ElementsArray, Kratos.PropertiesArray, Kratos.MasterSlaveConstraintsArray, Kratos.GeometryContainerType]"""
    def HasContainer(self) -> bool:
        """HasContainer(self: Kratos.TensorAdaptors.BoolTensorAdaptor) -> bool"""
    def SetData(self, array: numpy.ndarray) -> None:
        """SetData(self: Kratos.TensorAdaptors.BoolTensorAdaptor, array: numpy.ndarray) -> None"""
    def Shape(self) -> Kratos.DenseVectorUnsignedInt:
        """Shape(self: Kratos.TensorAdaptors.BoolTensorAdaptor) -> Kratos.DenseVectorUnsignedInt"""
    def Size(self) -> int:
        """Size(self: Kratos.TensorAdaptors.BoolTensorAdaptor) -> int"""
    def StoreData(self) -> None:
        """StoreData(self: Kratos.TensorAdaptors.BoolTensorAdaptor) -> None"""
    def ViewData(self) -> numpy.ndarray[bool]:
        """ViewData(self: Kratos.TensorAdaptors.BoolTensorAdaptor) -> numpy.ndarray[bool]"""

class DoubleCombinedTensorAdaptor(DoubleTensorAdaptor):
    @overload
    def __init__(self, list_of_tensor_adaptors: list[DoubleTensorAdaptor], perform_collect_data_recursively: bool = ..., perform_store_data_recursively: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.DoubleCombinedTensorAdaptor, list_of_tensor_adaptors: list[Kratos.TensorAdaptors.DoubleTensorAdaptor], perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True) -> None

        2. __init__(self: Kratos.TensorAdaptors.DoubleCombinedTensorAdaptor, list_of_tensor_adaptors: list[Kratos.TensorAdaptors.DoubleTensorAdaptor], axis: int, perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True) -> None

        3. __init__(self: Kratos.TensorAdaptors.DoubleCombinedTensorAdaptor, list_of_tensor_adaptors: Kratos.TensorAdaptors.DoubleCombinedTensorAdaptor, perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True, copy: bool = True) -> None
        """
    @overload
    def __init__(self, list_of_tensor_adaptors: list[DoubleTensorAdaptor], axis: int, perform_collect_data_recursively: bool = ..., perform_store_data_recursively: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.DoubleCombinedTensorAdaptor, list_of_tensor_adaptors: list[Kratos.TensorAdaptors.DoubleTensorAdaptor], perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True) -> None

        2. __init__(self: Kratos.TensorAdaptors.DoubleCombinedTensorAdaptor, list_of_tensor_adaptors: list[Kratos.TensorAdaptors.DoubleTensorAdaptor], axis: int, perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True) -> None

        3. __init__(self: Kratos.TensorAdaptors.DoubleCombinedTensorAdaptor, list_of_tensor_adaptors: Kratos.TensorAdaptors.DoubleCombinedTensorAdaptor, perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True, copy: bool = True) -> None
        """
    @overload
    def __init__(self, list_of_tensor_adaptors: DoubleCombinedTensorAdaptor, perform_collect_data_recursively: bool = ..., perform_store_data_recursively: bool = ..., copy: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.DoubleCombinedTensorAdaptor, list_of_tensor_adaptors: list[Kratos.TensorAdaptors.DoubleTensorAdaptor], perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True) -> None

        2. __init__(self: Kratos.TensorAdaptors.DoubleCombinedTensorAdaptor, list_of_tensor_adaptors: list[Kratos.TensorAdaptors.DoubleTensorAdaptor], axis: int, perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True) -> None

        3. __init__(self: Kratos.TensorAdaptors.DoubleCombinedTensorAdaptor, list_of_tensor_adaptors: Kratos.TensorAdaptors.DoubleCombinedTensorAdaptor, perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True, copy: bool = True) -> None
        """
    def GetTensorAdaptors(self) -> list[DoubleTensorAdaptor]:
        """GetTensorAdaptors(self: Kratos.TensorAdaptors.DoubleCombinedTensorAdaptor) -> list[Kratos.TensorAdaptors.DoubleTensorAdaptor]"""

class DoubleTensorAdaptor:
    data: numpy.ndarray[numpy.float64]
    @overload
    def __init__(self, container: Kratos.DofsArrayType | Kratos.NodesArray | Kratos.ConditionsArray | Kratos.ElementsArray | Kratos.PropertiesArray | Kratos.MasterSlaveConstraintsArray | Kratos.GeometryContainerType, nd_data: Kratos.DoubleNDData, copy: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.DoubleTensorAdaptor, container: Union[Kratos.DofsArrayType, Kratos.NodesArray, Kratos.ConditionsArray, Kratos.ElementsArray, Kratos.PropertiesArray, Kratos.MasterSlaveConstraintsArray, Kratos.GeometryContainerType], nd_data: Kratos.DoubleNDData, copy: bool = True) -> None

        2. __init__(self: Kratos.TensorAdaptors.DoubleTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, copy: bool = True) -> None
        """
    @overload
    def __init__(self, tensor_adaptor: DoubleTensorAdaptor, copy: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.DoubleTensorAdaptor, container: Union[Kratos.DofsArrayType, Kratos.NodesArray, Kratos.ConditionsArray, Kratos.ElementsArray, Kratos.PropertiesArray, Kratos.MasterSlaveConstraintsArray, Kratos.GeometryContainerType], nd_data: Kratos.DoubleNDData, copy: bool = True) -> None

        2. __init__(self: Kratos.TensorAdaptors.DoubleTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, copy: bool = True) -> None
        """
    def Check(self) -> None:
        """Check(self: Kratos.TensorAdaptors.DoubleTensorAdaptor) -> None"""
    def CollectData(self) -> None:
        """CollectData(self: Kratos.TensorAdaptors.DoubleTensorAdaptor) -> None"""
    def DataShape(self) -> Kratos.DenseVectorUnsignedInt:
        """DataShape(self: Kratos.TensorAdaptors.DoubleTensorAdaptor) -> Kratos.DenseVectorUnsignedInt"""
    def GetContainer(self) -> Kratos.DofsArrayType | Kratos.NodesArray | Kratos.ConditionsArray | Kratos.ElementsArray | Kratos.PropertiesArray | Kratos.MasterSlaveConstraintsArray | Kratos.GeometryContainerType:
        """GetContainer(self: Kratos.TensorAdaptors.DoubleTensorAdaptor) -> Union[Kratos.DofsArrayType, Kratos.NodesArray, Kratos.ConditionsArray, Kratos.ElementsArray, Kratos.PropertiesArray, Kratos.MasterSlaveConstraintsArray, Kratos.GeometryContainerType]"""
    def HasContainer(self) -> bool:
        """HasContainer(self: Kratos.TensorAdaptors.DoubleTensorAdaptor) -> bool"""
    def SetData(self, array: numpy.ndarray) -> None:
        """SetData(self: Kratos.TensorAdaptors.DoubleTensorAdaptor, array: numpy.ndarray) -> None"""
    def Shape(self) -> Kratos.DenseVectorUnsignedInt:
        """Shape(self: Kratos.TensorAdaptors.DoubleTensorAdaptor) -> Kratos.DenseVectorUnsignedInt"""
    def Size(self) -> int:
        """Size(self: Kratos.TensorAdaptors.DoubleTensorAdaptor) -> int"""
    def StoreData(self) -> None:
        """StoreData(self: Kratos.TensorAdaptors.DoubleTensorAdaptor) -> None"""
    def ViewData(self) -> numpy.ndarray[numpy.float64]:
        """ViewData(self: Kratos.TensorAdaptors.DoubleTensorAdaptor) -> numpy.ndarray[numpy.float64]"""

class EquationIdsTensorAdaptor(IntTensorAdaptor):
    @overload
    def __init__(self, container: Kratos.ConditionsArray, process_info: Kratos.ProcessInfo) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.EquationIdsTensorAdaptor, container: Kratos.ConditionsArray, process_info: Kratos.ProcessInfo) -> None

        2. __init__(self: Kratos.TensorAdaptors.EquationIdsTensorAdaptor, container: Kratos.ElementsArray, process_info: Kratos.ProcessInfo) -> None

        3. __init__(self: Kratos.TensorAdaptors.EquationIdsTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.IntTensorAdaptor, process_info: Kratos.ProcessInfo, copy: bool = True) -> None
        """
    @overload
    def __init__(self, container: Kratos.ElementsArray, process_info: Kratos.ProcessInfo) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.EquationIdsTensorAdaptor, container: Kratos.ConditionsArray, process_info: Kratos.ProcessInfo) -> None

        2. __init__(self: Kratos.TensorAdaptors.EquationIdsTensorAdaptor, container: Kratos.ElementsArray, process_info: Kratos.ProcessInfo) -> None

        3. __init__(self: Kratos.TensorAdaptors.EquationIdsTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.IntTensorAdaptor, process_info: Kratos.ProcessInfo, copy: bool = True) -> None
        """
    @overload
    def __init__(self, tensor_adaptor: IntTensorAdaptor, process_info: Kratos.ProcessInfo, copy: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.EquationIdsTensorAdaptor, container: Kratos.ConditionsArray, process_info: Kratos.ProcessInfo) -> None

        2. __init__(self: Kratos.TensorAdaptors.EquationIdsTensorAdaptor, container: Kratos.ElementsArray, process_info: Kratos.ProcessInfo) -> None

        3. __init__(self: Kratos.TensorAdaptors.EquationIdsTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.IntTensorAdaptor, process_info: Kratos.ProcessInfo, copy: bool = True) -> None
        """

class FlagsTensorAdaptor(IntTensorAdaptor):
    @overload
    def __init__(self, container: Kratos.NodesArray, flag: Kratos.Flags) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.FlagsTensorAdaptor, container: Kratos.NodesArray, flag: Kratos.Flags) -> None

        2. __init__(self: Kratos.TensorAdaptors.FlagsTensorAdaptor, container: Kratos.ConditionsArray, flag: Kratos.Flags) -> None

        3. __init__(self: Kratos.TensorAdaptors.FlagsTensorAdaptor, container: Kratos.ElementsArray, flag: Kratos.Flags) -> None

        4. __init__(self: Kratos.TensorAdaptors.FlagsTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.IntTensorAdaptor, flag: Kratos.Flags, copy: bool = True) -> None
        """
    @overload
    def __init__(self, container: Kratos.ConditionsArray, flag: Kratos.Flags) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.FlagsTensorAdaptor, container: Kratos.NodesArray, flag: Kratos.Flags) -> None

        2. __init__(self: Kratos.TensorAdaptors.FlagsTensorAdaptor, container: Kratos.ConditionsArray, flag: Kratos.Flags) -> None

        3. __init__(self: Kratos.TensorAdaptors.FlagsTensorAdaptor, container: Kratos.ElementsArray, flag: Kratos.Flags) -> None

        4. __init__(self: Kratos.TensorAdaptors.FlagsTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.IntTensorAdaptor, flag: Kratos.Flags, copy: bool = True) -> None
        """
    @overload
    def __init__(self, container: Kratos.ElementsArray, flag: Kratos.Flags) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.FlagsTensorAdaptor, container: Kratos.NodesArray, flag: Kratos.Flags) -> None

        2. __init__(self: Kratos.TensorAdaptors.FlagsTensorAdaptor, container: Kratos.ConditionsArray, flag: Kratos.Flags) -> None

        3. __init__(self: Kratos.TensorAdaptors.FlagsTensorAdaptor, container: Kratos.ElementsArray, flag: Kratos.Flags) -> None

        4. __init__(self: Kratos.TensorAdaptors.FlagsTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.IntTensorAdaptor, flag: Kratos.Flags, copy: bool = True) -> None
        """
    @overload
    def __init__(self, tensor_adaptor: IntTensorAdaptor, flag: Kratos.Flags, copy: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.FlagsTensorAdaptor, container: Kratos.NodesArray, flag: Kratos.Flags) -> None

        2. __init__(self: Kratos.TensorAdaptors.FlagsTensorAdaptor, container: Kratos.ConditionsArray, flag: Kratos.Flags) -> None

        3. __init__(self: Kratos.TensorAdaptors.FlagsTensorAdaptor, container: Kratos.ElementsArray, flag: Kratos.Flags) -> None

        4. __init__(self: Kratos.TensorAdaptors.FlagsTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.IntTensorAdaptor, flag: Kratos.Flags, copy: bool = True) -> None
        """

class GaussPointVariableTensorAdaptor(DoubleTensorAdaptor):
    @overload
    def __init__(self, container: Kratos.ConditionsArray, variable: Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable, process_info: Kratos.ProcessInfo) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.GaussPointVariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], process_info: Kratos.ProcessInfo) -> None

        2. __init__(self: Kratos.TensorAdaptors.GaussPointVariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], process_info: Kratos.ProcessInfo) -> None

        3. __init__(self: Kratos.TensorAdaptors.GaussPointVariableTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], process_info: Kratos.ProcessInfo, copy: bool = True) -> None
        """
    @overload
    def __init__(self, container: Kratos.ElementsArray, variable: Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable, process_info: Kratos.ProcessInfo) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.GaussPointVariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], process_info: Kratos.ProcessInfo) -> None

        2. __init__(self: Kratos.TensorAdaptors.GaussPointVariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], process_info: Kratos.ProcessInfo) -> None

        3. __init__(self: Kratos.TensorAdaptors.GaussPointVariableTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], process_info: Kratos.ProcessInfo, copy: bool = True) -> None
        """
    @overload
    def __init__(self, tensor_adaptor: DoubleTensorAdaptor, variable: Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable, process_info: Kratos.ProcessInfo, copy: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.GaussPointVariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], process_info: Kratos.ProcessInfo) -> None

        2. __init__(self: Kratos.TensorAdaptors.GaussPointVariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], process_info: Kratos.ProcessInfo) -> None

        3. __init__(self: Kratos.TensorAdaptors.GaussPointVariableTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], process_info: Kratos.ProcessInfo, copy: bool = True) -> None
        """

class HistoricalVariableTensorAdaptor(DoubleTensorAdaptor):
    @overload
    def __init__(self, container: Kratos.NodesArray, variable: Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable, step_index: int = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.HistoricalVariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], step_index: int = 0) -> None

        2. __init__(self: Kratos.TensorAdaptors.HistoricalVariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int], step_index: int = 0) -> None

        3. __init__(self: Kratos.TensorAdaptors.HistoricalVariableTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], step_index: int = 0, copy: bool = True) -> None
        """
    @overload
    def __init__(self, container: Kratos.NodesArray, variable: Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable, data_shape: list[int], step_index: int = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.HistoricalVariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], step_index: int = 0) -> None

        2. __init__(self: Kratos.TensorAdaptors.HistoricalVariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int], step_index: int = 0) -> None

        3. __init__(self: Kratos.TensorAdaptors.HistoricalVariableTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], step_index: int = 0, copy: bool = True) -> None
        """
    @overload
    def __init__(self, tensor_adaptor: DoubleTensorAdaptor, variable: Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable, step_index: int = ..., copy: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.HistoricalVariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], step_index: int = 0) -> None

        2. __init__(self: Kratos.TensorAdaptors.HistoricalVariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int], step_index: int = 0) -> None

        3. __init__(self: Kratos.TensorAdaptors.HistoricalVariableTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], step_index: int = 0, copy: bool = True) -> None
        """

class IntCombinedTensorAdaptor(IntTensorAdaptor):
    @overload
    def __init__(self, list_of_tensor_adaptors: list[IntTensorAdaptor], perform_collect_data_recursively: bool = ..., perform_store_data_recursively: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.IntCombinedTensorAdaptor, list_of_tensor_adaptors: list[Kratos.TensorAdaptors.IntTensorAdaptor], perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True) -> None

        2. __init__(self: Kratos.TensorAdaptors.IntCombinedTensorAdaptor, list_of_tensor_adaptors: list[Kratos.TensorAdaptors.IntTensorAdaptor], axis: int, perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True) -> None

        3. __init__(self: Kratos.TensorAdaptors.IntCombinedTensorAdaptor, list_of_tensor_adaptors: Kratos.TensorAdaptors.IntCombinedTensorAdaptor, perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True, copy: bool = True) -> None
        """
    @overload
    def __init__(self, list_of_tensor_adaptors: list[IntTensorAdaptor], axis: int, perform_collect_data_recursively: bool = ..., perform_store_data_recursively: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.IntCombinedTensorAdaptor, list_of_tensor_adaptors: list[Kratos.TensorAdaptors.IntTensorAdaptor], perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True) -> None

        2. __init__(self: Kratos.TensorAdaptors.IntCombinedTensorAdaptor, list_of_tensor_adaptors: list[Kratos.TensorAdaptors.IntTensorAdaptor], axis: int, perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True) -> None

        3. __init__(self: Kratos.TensorAdaptors.IntCombinedTensorAdaptor, list_of_tensor_adaptors: Kratos.TensorAdaptors.IntCombinedTensorAdaptor, perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True, copy: bool = True) -> None
        """
    @overload
    def __init__(self, list_of_tensor_adaptors: IntCombinedTensorAdaptor, perform_collect_data_recursively: bool = ..., perform_store_data_recursively: bool = ..., copy: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.IntCombinedTensorAdaptor, list_of_tensor_adaptors: list[Kratos.TensorAdaptors.IntTensorAdaptor], perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True) -> None

        2. __init__(self: Kratos.TensorAdaptors.IntCombinedTensorAdaptor, list_of_tensor_adaptors: list[Kratos.TensorAdaptors.IntTensorAdaptor], axis: int, perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True) -> None

        3. __init__(self: Kratos.TensorAdaptors.IntCombinedTensorAdaptor, list_of_tensor_adaptors: Kratos.TensorAdaptors.IntCombinedTensorAdaptor, perform_collect_data_recursively: bool = True, perform_store_data_recursively: bool = True, copy: bool = True) -> None
        """
    def GetTensorAdaptors(self) -> list[IntTensorAdaptor]:
        """GetTensorAdaptors(self: Kratos.TensorAdaptors.IntCombinedTensorAdaptor) -> list[Kratos.TensorAdaptors.IntTensorAdaptor]"""

class IntTensorAdaptor:
    data: numpy.ndarray[numpy.int32]
    @overload
    def __init__(self, container: Kratos.DofsArrayType | Kratos.NodesArray | Kratos.ConditionsArray | Kratos.ElementsArray | Kratos.PropertiesArray | Kratos.MasterSlaveConstraintsArray | Kratos.GeometryContainerType, nd_data: Kratos.IntNDData, copy: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.IntTensorAdaptor, container: Union[Kratos.DofsArrayType, Kratos.NodesArray, Kratos.ConditionsArray, Kratos.ElementsArray, Kratos.PropertiesArray, Kratos.MasterSlaveConstraintsArray, Kratos.GeometryContainerType], nd_data: Kratos.IntNDData, copy: bool = True) -> None

        2. __init__(self: Kratos.TensorAdaptors.IntTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.IntTensorAdaptor, copy: bool = True) -> None
        """
    @overload
    def __init__(self, tensor_adaptor: IntTensorAdaptor, copy: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.IntTensorAdaptor, container: Union[Kratos.DofsArrayType, Kratos.NodesArray, Kratos.ConditionsArray, Kratos.ElementsArray, Kratos.PropertiesArray, Kratos.MasterSlaveConstraintsArray, Kratos.GeometryContainerType], nd_data: Kratos.IntNDData, copy: bool = True) -> None

        2. __init__(self: Kratos.TensorAdaptors.IntTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.IntTensorAdaptor, copy: bool = True) -> None
        """
    def Check(self) -> None:
        """Check(self: Kratos.TensorAdaptors.IntTensorAdaptor) -> None"""
    def CollectData(self) -> None:
        """CollectData(self: Kratos.TensorAdaptors.IntTensorAdaptor) -> None"""
    def DataShape(self) -> Kratos.DenseVectorUnsignedInt:
        """DataShape(self: Kratos.TensorAdaptors.IntTensorAdaptor) -> Kratos.DenseVectorUnsignedInt"""
    def GetContainer(self) -> Kratos.DofsArrayType | Kratos.NodesArray | Kratos.ConditionsArray | Kratos.ElementsArray | Kratos.PropertiesArray | Kratos.MasterSlaveConstraintsArray | Kratos.GeometryContainerType:
        """GetContainer(self: Kratos.TensorAdaptors.IntTensorAdaptor) -> Union[Kratos.DofsArrayType, Kratos.NodesArray, Kratos.ConditionsArray, Kratos.ElementsArray, Kratos.PropertiesArray, Kratos.MasterSlaveConstraintsArray, Kratos.GeometryContainerType]"""
    def HasContainer(self) -> bool:
        """HasContainer(self: Kratos.TensorAdaptors.IntTensorAdaptor) -> bool"""
    def SetData(self, array: numpy.ndarray) -> None:
        """SetData(self: Kratos.TensorAdaptors.IntTensorAdaptor, array: numpy.ndarray) -> None"""
    def Shape(self) -> Kratos.DenseVectorUnsignedInt:
        """Shape(self: Kratos.TensorAdaptors.IntTensorAdaptor) -> Kratos.DenseVectorUnsignedInt"""
    def Size(self) -> int:
        """Size(self: Kratos.TensorAdaptors.IntTensorAdaptor) -> int"""
    def StoreData(self) -> None:
        """StoreData(self: Kratos.TensorAdaptors.IntTensorAdaptor) -> None"""
    def ViewData(self) -> numpy.ndarray[numpy.int32]:
        """ViewData(self: Kratos.TensorAdaptors.IntTensorAdaptor) -> numpy.ndarray[numpy.int32]"""

class NodePositionTensorAdaptor(DoubleTensorAdaptor):
    @overload
    def __init__(self, container: Kratos.NodesArray, configuration: Kratos.Configuration) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.NodePositionTensorAdaptor, container: Kratos.NodesArray, configuration: Kratos.Configuration) -> None

        2. __init__(self: Kratos.TensorAdaptors.NodePositionTensorAdaptor, container: Kratos.NodesArray, configuration: Kratos.Configuration, data_shape: list[int]) -> None

        3. __init__(self: Kratos.TensorAdaptors.NodePositionTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, configuration: Kratos.Configuration, copy: bool = True) -> None
        """
    @overload
    def __init__(self, container: Kratos.NodesArray, configuration: Kratos.Configuration, data_shape: list[int]) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.NodePositionTensorAdaptor, container: Kratos.NodesArray, configuration: Kratos.Configuration) -> None

        2. __init__(self: Kratos.TensorAdaptors.NodePositionTensorAdaptor, container: Kratos.NodesArray, configuration: Kratos.Configuration, data_shape: list[int]) -> None

        3. __init__(self: Kratos.TensorAdaptors.NodePositionTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, configuration: Kratos.Configuration, copy: bool = True) -> None
        """
    @overload
    def __init__(self, tensor_adaptor: DoubleTensorAdaptor, configuration: Kratos.Configuration, copy: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.NodePositionTensorAdaptor, container: Kratos.NodesArray, configuration: Kratos.Configuration) -> None

        2. __init__(self: Kratos.TensorAdaptors.NodePositionTensorAdaptor, container: Kratos.NodesArray, configuration: Kratos.Configuration, data_shape: list[int]) -> None

        3. __init__(self: Kratos.TensorAdaptors.NodePositionTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, configuration: Kratos.Configuration, copy: bool = True) -> None
        """

class VariableTensorAdaptor(DoubleTensorAdaptor):
    @overload
    def __init__(self, container: Kratos.NodesArray, variable: Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        2. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        3. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        4. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        5. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        6. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        7. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        8. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        9. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        10. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        11. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        12. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        13. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], copy: bool = True) -> None
        """
    @overload
    def __init__(self, container: Kratos.NodesArray, variable: Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable, data_shape: list[int]) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        2. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        3. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        4. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        5. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        6. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        7. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        8. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        9. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        10. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        11. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        12. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        13. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], copy: bool = True) -> None
        """
    @overload
    def __init__(self, container: Kratos.ConditionsArray, variable: Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        2. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        3. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        4. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        5. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        6. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        7. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        8. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        9. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        10. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        11. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        12. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        13. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], copy: bool = True) -> None
        """
    @overload
    def __init__(self, container: Kratos.ConditionsArray, variable: Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable, data_shape: list[int]) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        2. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        3. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        4. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        5. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        6. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        7. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        8. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        9. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        10. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        11. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        12. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        13. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], copy: bool = True) -> None
        """
    @overload
    def __init__(self, container: Kratos.ElementsArray, variable: Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        2. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        3. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        4. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        5. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        6. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        7. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        8. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        9. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        10. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        11. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        12. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        13. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], copy: bool = True) -> None
        """
    @overload
    def __init__(self, container: Kratos.ElementsArray, variable: Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable, data_shape: list[int]) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        2. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        3. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        4. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        5. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        6. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        7. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        8. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        9. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        10. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        11. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        12. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        13. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], copy: bool = True) -> None
        """
    @overload
    def __init__(self, container: Kratos.PropertiesArray, variable: Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        2. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        3. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        4. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        5. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        6. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        7. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        8. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        9. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        10. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        11. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        12. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        13. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], copy: bool = True) -> None
        """
    @overload
    def __init__(self, container: Kratos.PropertiesArray, variable: Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable, data_shape: list[int]) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        2. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        3. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        4. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        5. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        6. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        7. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        8. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        9. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        10. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        11. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        12. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        13. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], copy: bool = True) -> None
        """
    @overload
    def __init__(self, container: Kratos.GeometryContainerType, variable: Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        2. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        3. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        4. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        5. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        6. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        7. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        8. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        9. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        10. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        11. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        12. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        13. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], copy: bool = True) -> None
        """
    @overload
    def __init__(self, container: Kratos.GeometryContainerType, variable: Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable, data_shape: list[int]) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        2. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        3. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        4. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        5. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        6. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        7. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        8. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        9. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        10. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        11. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        12. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        13. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], copy: bool = True) -> None
        """
    @overload
    def __init__(self, container: Kratos.MasterSlaveConstraintsArray, variable: Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        2. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        3. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        4. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        5. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        6. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        7. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        8. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        9. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        10. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        11. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        12. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        13. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], copy: bool = True) -> None
        """
    @overload
    def __init__(self, container: Kratos.MasterSlaveConstraintsArray, variable: Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable, data_shape: list[int]) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        2. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        3. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        4. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        5. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        6. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        7. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        8. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        9. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        10. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        11. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        12. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        13. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], copy: bool = True) -> None
        """
    @overload
    def __init__(self, tensor_adaptor: DoubleTensorAdaptor, variable: Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable, copy: bool = ...) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        2. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.NodesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        3. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        4. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ConditionsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        5. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        6. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.ElementsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        7. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        8. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.PropertiesArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        9. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        10. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.GeometryContainerType, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        11. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

        12. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, container: Kratos.MasterSlaveConstraintsArray, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_shape: list[int]) -> None

        13. __init__(self: Kratos.TensorAdaptors.VariableTensorAdaptor, tensor_adaptor: Kratos.TensorAdaptors.DoubleTensorAdaptor, variable: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], copy: bool = True) -> None
        """
