import Kratos.Expression
from typing import overload

@overload
def CalculateForwardProjectionGradient(nodal_expression: Kratos.Expression.NodalExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.NodalExpression:
    """CalculateForwardProjectionGradient(*args, **kwargs)
    Overloaded function.

    1. CalculateForwardProjectionGradient(nodal_expression: Kratos.Expression.NodalExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.NodalExpression

    2. CalculateForwardProjectionGradient(condition_expression: Kratos.Expression.ConditionExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ConditionExpression

    3. CalculateForwardProjectionGradient(element_expression: Kratos.Expression.ElementExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ElementExpression
    """
@overload
def CalculateForwardProjectionGradient(condition_expression: Kratos.Expression.ConditionExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ConditionExpression:
    """CalculateForwardProjectionGradient(*args, **kwargs)
    Overloaded function.

    1. CalculateForwardProjectionGradient(nodal_expression: Kratos.Expression.NodalExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.NodalExpression

    2. CalculateForwardProjectionGradient(condition_expression: Kratos.Expression.ConditionExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ConditionExpression

    3. CalculateForwardProjectionGradient(element_expression: Kratos.Expression.ElementExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ElementExpression
    """
@overload
def CalculateForwardProjectionGradient(element_expression: Kratos.Expression.ElementExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ElementExpression:
    """CalculateForwardProjectionGradient(*args, **kwargs)
    Overloaded function.

    1. CalculateForwardProjectionGradient(nodal_expression: Kratos.Expression.NodalExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.NodalExpression

    2. CalculateForwardProjectionGradient(condition_expression: Kratos.Expression.ConditionExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ConditionExpression

    3. CalculateForwardProjectionGradient(element_expression: Kratos.Expression.ElementExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ElementExpression
    """
@overload
def ProjectBackward(nodal_expression: Kratos.Expression.NodalExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.NodalExpression:
    """ProjectBackward(*args, **kwargs)
    Overloaded function.

    1. ProjectBackward(nodal_expression: Kratos.Expression.NodalExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.NodalExpression

    2. ProjectBackward(condition_expression: Kratos.Expression.ConditionExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ConditionExpression

    3. ProjectBackward(element_expression: Kratos.Expression.ElementExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ElementExpression
    """
@overload
def ProjectBackward(condition_expression: Kratos.Expression.ConditionExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ConditionExpression:
    """ProjectBackward(*args, **kwargs)
    Overloaded function.

    1. ProjectBackward(nodal_expression: Kratos.Expression.NodalExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.NodalExpression

    2. ProjectBackward(condition_expression: Kratos.Expression.ConditionExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ConditionExpression

    3. ProjectBackward(element_expression: Kratos.Expression.ElementExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ElementExpression
    """
@overload
def ProjectBackward(element_expression: Kratos.Expression.ElementExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ElementExpression:
    """ProjectBackward(*args, **kwargs)
    Overloaded function.

    1. ProjectBackward(nodal_expression: Kratos.Expression.NodalExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.NodalExpression

    2. ProjectBackward(condition_expression: Kratos.Expression.ConditionExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ConditionExpression

    3. ProjectBackward(element_expression: Kratos.Expression.ElementExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ElementExpression
    """
@overload
def ProjectForward(nodal_expression: Kratos.Expression.NodalExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.NodalExpression:
    """ProjectForward(*args, **kwargs)
    Overloaded function.

    1. ProjectForward(nodal_expression: Kratos.Expression.NodalExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.NodalExpression

    2. ProjectForward(condition_expression: Kratos.Expression.ConditionExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ConditionExpression

    3. ProjectForward(element_expression: Kratos.Expression.ElementExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ElementExpression
    """
@overload
def ProjectForward(condition_expression: Kratos.Expression.ConditionExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ConditionExpression:
    """ProjectForward(*args, **kwargs)
    Overloaded function.

    1. ProjectForward(nodal_expression: Kratos.Expression.NodalExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.NodalExpression

    2. ProjectForward(condition_expression: Kratos.Expression.ConditionExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ConditionExpression

    3. ProjectForward(element_expression: Kratos.Expression.ElementExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ElementExpression
    """
@overload
def ProjectForward(element_expression: Kratos.Expression.ElementExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ElementExpression:
    """ProjectForward(*args, **kwargs)
    Overloaded function.

    1. ProjectForward(nodal_expression: Kratos.Expression.NodalExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.NodalExpression

    2. ProjectForward(condition_expression: Kratos.Expression.ConditionExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ConditionExpression

    3. ProjectForward(element_expression: Kratos.Expression.ElementExpression, x_values: list[float], y_values: list[float], beta: float, penalty_factor: int) -> Kratos.Expression.ElementExpression
    """
