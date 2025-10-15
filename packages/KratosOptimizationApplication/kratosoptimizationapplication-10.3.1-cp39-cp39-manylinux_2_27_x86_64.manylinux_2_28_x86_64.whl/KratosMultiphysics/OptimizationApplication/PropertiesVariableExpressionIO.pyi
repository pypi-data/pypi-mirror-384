import Kratos
import Kratos.Expression
import Kratos.Expression.VariableExpressionIO
import Kratos.Globals
from typing import overload

class Input(Kratos.Expression.VariableExpressionIO.ExpressionInput):
    def __init__(self, model_part: Kratos.ModelPart, variable: Kratos.IntegerVariable | Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable, data_location: Kratos.Globals.DataLocation) -> None:
        """__init__(self: KratosOptimizationApplication.PropertiesVariableExpressionIO.Input, model_part: Kratos.ModelPart, variable: Union[Kratos.IntegerVariable, Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_location: Kratos.Globals.DataLocation) -> None"""

class Output(Kratos.Expression.VariableExpressionIO.ExpressionOutput):
    def __init__(self, model_part: Kratos.ModelPart, variable: Kratos.IntegerVariable | Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable, data_location: Kratos.Globals.DataLocation) -> None:
        """__init__(self: KratosOptimizationApplication.PropertiesVariableExpressionIO.Output, model_part: Kratos.ModelPart, variable: Union[Kratos.IntegerVariable, Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable], data_location: Kratos.Globals.DataLocation) -> None"""

@overload
def Check(condition_container_expression: Kratos.Expression.ConditionExpression, variable: Kratos.IntegerVariable | Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable) -> None:
    """Check(*args, **kwargs)
    Overloaded function.

    1. Check(condition_container_expression: Kratos.Expression.ConditionExpression, variable: Union[Kratos.IntegerVariable, Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

    2. Check(element_container_expression: Kratos.Expression.ElementExpression, variable: Union[Kratos.IntegerVariable, Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None
    """
@overload
def Check(element_container_expression: Kratos.Expression.ElementExpression, variable: Kratos.IntegerVariable | Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable) -> None:
    """Check(*args, **kwargs)
    Overloaded function.

    1. Check(condition_container_expression: Kratos.Expression.ConditionExpression, variable: Union[Kratos.IntegerVariable, Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

    2. Check(element_container_expression: Kratos.Expression.ElementExpression, variable: Union[Kratos.IntegerVariable, Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None
    """
@overload
def Read(condition_container_expression: Kratos.Expression.ConditionExpression, variable: Kratos.IntegerVariable | Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable) -> None:
    """Read(*args, **kwargs)
    Overloaded function.

    1. Read(condition_container_expression: Kratos.Expression.ConditionExpression, variable: Union[Kratos.IntegerVariable, Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

    2. Read(element_container_expression: Kratos.Expression.ElementExpression, variable: Union[Kratos.IntegerVariable, Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None
    """
@overload
def Read(element_container_expression: Kratos.Expression.ElementExpression, variable: Kratos.IntegerVariable | Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable) -> None:
    """Read(*args, **kwargs)
    Overloaded function.

    1. Read(condition_container_expression: Kratos.Expression.ConditionExpression, variable: Union[Kratos.IntegerVariable, Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

    2. Read(element_container_expression: Kratos.Expression.ElementExpression, variable: Union[Kratos.IntegerVariable, Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None
    """
@overload
def Write(condition_container_expression: Kratos.Expression.ConditionExpression, variable: Kratos.IntegerVariable | Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable) -> None:
    """Write(*args, **kwargs)
    Overloaded function.

    1. Write(condition_container_expression: Kratos.Expression.ConditionExpression, variable: Union[Kratos.IntegerVariable, Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

    2. Write(element_container_expression: Kratos.Expression.ElementExpression, variable: Union[Kratos.IntegerVariable, Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None
    """
@overload
def Write(element_container_expression: Kratos.Expression.ElementExpression, variable: Kratos.IntegerVariable | Kratos.DoubleVariable | Kratos.Array1DVariable3 | Kratos.Array1DVariable4 | Kratos.Array1DVariable6 | Kratos.Array1DVariable9 | Kratos.VectorVariable | Kratos.MatrixVariable) -> None:
    """Write(*args, **kwargs)
    Overloaded function.

    1. Write(condition_container_expression: Kratos.Expression.ConditionExpression, variable: Union[Kratos.IntegerVariable, Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None

    2. Write(element_container_expression: Kratos.Expression.ElementExpression, variable: Union[Kratos.IntegerVariable, Kratos.DoubleVariable, Kratos.Array1DVariable3, Kratos.Array1DVariable4, Kratos.Array1DVariable6, Kratos.Array1DVariable9, Kratos.VectorVariable, Kratos.MatrixVariable]) -> None
    """
