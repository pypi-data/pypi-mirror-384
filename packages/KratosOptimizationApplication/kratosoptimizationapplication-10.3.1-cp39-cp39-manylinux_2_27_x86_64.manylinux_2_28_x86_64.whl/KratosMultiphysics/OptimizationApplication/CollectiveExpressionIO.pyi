import Kratos
import KratosOptimizationApplication
import numpy
from typing import overload

class HistoricalVariable:
    def __init__(self, variable: Kratos.IntegerVariable | Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable) -> None:
        """__init__(self: KratosOptimizationApplication.CollectiveExpressionIO.HistoricalVariable, variable: Union[Kratos.IntegerVariable, Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None"""

class NonHistoricalVariable:
    def __init__(self, variable: Kratos.IntegerVariable | Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable) -> None:
        """__init__(self: KratosOptimizationApplication.CollectiveExpressionIO.NonHistoricalVariable, variable: Union[Kratos.IntegerVariable, Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None"""

class PropertiesVariable:
    def __init__(self, variable: Kratos.IntegerVariable | Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable) -> None:
        """__init__(self: KratosOptimizationApplication.CollectiveExpressionIO.PropertiesVariable, variable: Union[Kratos.IntegerVariable, Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None"""

@overload
def Move(collective_expression: KratosOptimizationApplication.CollectiveExpression, numpy_data_array: numpy.ndarray[numpy.float64]) -> None:
    """Move(*args, **kwargs)
    Overloaded function.

    1. Move(collective_expression: KratosOptimizationApplication.CollectiveExpression, numpy_data_array: numpy.ndarray[numpy.float64]) -> None

    2. Move(collective_expression: KratosOptimizationApplication.CollectiveExpression, numpy_data_array: numpy.ndarray[numpy.float64], list_of_shapes: list[list[int]]) -> None
    """
@overload
def Move(collective_expression: KratosOptimizationApplication.CollectiveExpression, numpy_data_array: numpy.ndarray[numpy.float64], list_of_shapes: list[list[int]]) -> None:
    """Move(*args, **kwargs)
    Overloaded function.

    1. Move(collective_expression: KratosOptimizationApplication.CollectiveExpression, numpy_data_array: numpy.ndarray[numpy.float64]) -> None

    2. Move(collective_expression: KratosOptimizationApplication.CollectiveExpression, numpy_data_array: numpy.ndarray[numpy.float64], list_of_shapes: list[list[int]]) -> None
    """
@overload
def Read(collective_expression: KratosOptimizationApplication.CollectiveExpression, variable_container: HistoricalVariable | NonHistoricalVariable | PropertiesVariable) -> None:
    """Read(*args, **kwargs)
    Overloaded function.

    1. Read(collective_expression: KratosOptimizationApplication.CollectiveExpression, variable_container: Union[KratosOptimizationApplication.CollectiveExpressionIO.HistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.NonHistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.PropertiesVariable]) -> None

    2. Read(collective_expression: KratosOptimizationApplication.CollectiveExpression, list_of_variable_containers: list[Union[KratosOptimizationApplication.CollectiveExpressionIO.HistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.NonHistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.PropertiesVariable]]) -> None

    3. Read(collective_expression: KratosOptimizationApplication.CollectiveExpression, numpy_data_array: numpy.ndarray[numpy.float64]) -> None

    4. Read(collective_expression: KratosOptimizationApplication.CollectiveExpression, numpy_data_array: numpy.ndarray[numpy.float64], list_of_shapes: list[list[int]]) -> None
    """
@overload
def Read(collective_expression: KratosOptimizationApplication.CollectiveExpression, list_of_variable_containers: list[HistoricalVariable | NonHistoricalVariable | PropertiesVariable]) -> None:
    """Read(*args, **kwargs)
    Overloaded function.

    1. Read(collective_expression: KratosOptimizationApplication.CollectiveExpression, variable_container: Union[KratosOptimizationApplication.CollectiveExpressionIO.HistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.NonHistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.PropertiesVariable]) -> None

    2. Read(collective_expression: KratosOptimizationApplication.CollectiveExpression, list_of_variable_containers: list[Union[KratosOptimizationApplication.CollectiveExpressionIO.HistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.NonHistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.PropertiesVariable]]) -> None

    3. Read(collective_expression: KratosOptimizationApplication.CollectiveExpression, numpy_data_array: numpy.ndarray[numpy.float64]) -> None

    4. Read(collective_expression: KratosOptimizationApplication.CollectiveExpression, numpy_data_array: numpy.ndarray[numpy.float64], list_of_shapes: list[list[int]]) -> None
    """
@overload
def Read(collective_expression: KratosOptimizationApplication.CollectiveExpression, numpy_data_array: numpy.ndarray[numpy.float64]) -> None:
    """Read(*args, **kwargs)
    Overloaded function.

    1. Read(collective_expression: KratosOptimizationApplication.CollectiveExpression, variable_container: Union[KratosOptimizationApplication.CollectiveExpressionIO.HistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.NonHistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.PropertiesVariable]) -> None

    2. Read(collective_expression: KratosOptimizationApplication.CollectiveExpression, list_of_variable_containers: list[Union[KratosOptimizationApplication.CollectiveExpressionIO.HistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.NonHistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.PropertiesVariable]]) -> None

    3. Read(collective_expression: KratosOptimizationApplication.CollectiveExpression, numpy_data_array: numpy.ndarray[numpy.float64]) -> None

    4. Read(collective_expression: KratosOptimizationApplication.CollectiveExpression, numpy_data_array: numpy.ndarray[numpy.float64], list_of_shapes: list[list[int]]) -> None
    """
@overload
def Read(collective_expression: KratosOptimizationApplication.CollectiveExpression, numpy_data_array: numpy.ndarray[numpy.float64], list_of_shapes: list[list[int]]) -> None:
    """Read(*args, **kwargs)
    Overloaded function.

    1. Read(collective_expression: KratosOptimizationApplication.CollectiveExpression, variable_container: Union[KratosOptimizationApplication.CollectiveExpressionIO.HistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.NonHistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.PropertiesVariable]) -> None

    2. Read(collective_expression: KratosOptimizationApplication.CollectiveExpression, list_of_variable_containers: list[Union[KratosOptimizationApplication.CollectiveExpressionIO.HistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.NonHistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.PropertiesVariable]]) -> None

    3. Read(collective_expression: KratosOptimizationApplication.CollectiveExpression, numpy_data_array: numpy.ndarray[numpy.float64]) -> None

    4. Read(collective_expression: KratosOptimizationApplication.CollectiveExpression, numpy_data_array: numpy.ndarray[numpy.float64], list_of_shapes: list[list[int]]) -> None
    """
@overload
def Write(collective_expression: KratosOptimizationApplication.CollectiveExpression, variable_container: HistoricalVariable | NonHistoricalVariable | PropertiesVariable) -> None:
    """Write(*args, **kwargs)
    Overloaded function.

    1. Write(collective_expression: KratosOptimizationApplication.CollectiveExpression, variable_container: Union[KratosOptimizationApplication.CollectiveExpressionIO.HistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.NonHistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.PropertiesVariable]) -> None

    2. Write(collective_expression: KratosOptimizationApplication.CollectiveExpression, list_of_variable_containers: list[Union[KratosOptimizationApplication.CollectiveExpressionIO.HistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.NonHistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.PropertiesVariable]]) -> None
    """
@overload
def Write(collective_expression: KratosOptimizationApplication.CollectiveExpression, list_of_variable_containers: list[HistoricalVariable | NonHistoricalVariable | PropertiesVariable]) -> None:
    """Write(*args, **kwargs)
    Overloaded function.

    1. Write(collective_expression: KratosOptimizationApplication.CollectiveExpression, variable_container: Union[KratosOptimizationApplication.CollectiveExpressionIO.HistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.NonHistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.PropertiesVariable]) -> None

    2. Write(collective_expression: KratosOptimizationApplication.CollectiveExpression, list_of_variable_containers: list[Union[KratosOptimizationApplication.CollectiveExpressionIO.HistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.NonHistoricalVariable, KratosOptimizationApplication.CollectiveExpressionIO.PropertiesVariable]]) -> None
    """
