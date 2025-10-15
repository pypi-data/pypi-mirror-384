import Kratos
import Kratos.Expression

def CalculateGradient(list_of_gradient_variables: Kratos.DoubleVariable | Kratos.Array1DVariable3, list_of_gradient_required_model_parts: Kratos.ModelPart, list_of_gradient_computed_model_parts: Kratos.ModelPart, list_of_container_expressions: list[Kratos.Expression.NodalExpression | Kratos.Expression.ConditionExpression | Kratos.Expression.ElementExpression], perturbation_size: float) -> None:
    """CalculateGradient(list_of_gradient_variables: Union[Kratos.DoubleVariable, Kratos.Array1DVariable3], list_of_gradient_required_model_parts: Kratos.ModelPart, list_of_gradient_computed_model_parts: Kratos.ModelPart, list_of_container_expressions: list[Union[Kratos.Expression.NodalExpression, Kratos.Expression.ConditionExpression, Kratos.Expression.ElementExpression]], perturbation_size: float) -> None"""
def CalculateValue(arg0: Kratos.ModelPart) -> float:
    """CalculateValue(arg0: Kratos.ModelPart) -> float"""
def Check(arg0: Kratos.ModelPart) -> None:
    """Check(arg0: Kratos.ModelPart) -> None"""
