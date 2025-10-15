import Kratos
import Kratos.Expression
import KratosOptimizationApplication
from typing import overload

def Abs(collective_expressions: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression:
    """Abs(collective_expressions: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression"""
def Collapse(collective_expressions: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression:
    """Collapse(collective_expressions: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression"""
@overload
def ComputeNodalVariableProductWithEntityMatrix(output_nodal_container_expression: Kratos.Expression.NodalExpression, input_nodal_values_container_expression: Kratos.Expression.NodalExpression, matrix_variable: Kratos.MatrixVariable, entities: Kratos.ConditionsArray) -> None:
    """ComputeNodalVariableProductWithEntityMatrix(*args, **kwargs)
    Overloaded function.

    1. ComputeNodalVariableProductWithEntityMatrix(output_nodal_container_expression: Kratos.Expression.NodalExpression, input_nodal_values_container_expression: Kratos.Expression.NodalExpression, matrix_variable: Kratos.MatrixVariable, entities: Kratos.ConditionsArray) -> None

    2. ComputeNodalVariableProductWithEntityMatrix(output_nodal_container_expression: Kratos.Expression.NodalExpression, input_nodal_values_container_expression: Kratos.Expression.NodalExpression, matrix_variable: Kratos.MatrixVariable, entities: Kratos.ElementsArray) -> None
    """
@overload
def ComputeNodalVariableProductWithEntityMatrix(output_nodal_container_expression: Kratos.Expression.NodalExpression, input_nodal_values_container_expression: Kratos.Expression.NodalExpression, matrix_variable: Kratos.MatrixVariable, entities: Kratos.ElementsArray) -> None:
    """ComputeNodalVariableProductWithEntityMatrix(*args, **kwargs)
    Overloaded function.

    1. ComputeNodalVariableProductWithEntityMatrix(output_nodal_container_expression: Kratos.Expression.NodalExpression, input_nodal_values_container_expression: Kratos.Expression.NodalExpression, matrix_variable: Kratos.MatrixVariable, entities: Kratos.ConditionsArray) -> None

    2. ComputeNodalVariableProductWithEntityMatrix(output_nodal_container_expression: Kratos.Expression.NodalExpression, input_nodal_values_container_expression: Kratos.Expression.NodalExpression, matrix_variable: Kratos.MatrixVariable, entities: Kratos.ElementsArray) -> None
    """
def ComputeNumberOfNeighbourConditions(output_nodal_container_expression: Kratos.Expression.NodalExpression) -> None:
    """ComputeNumberOfNeighbourConditions(output_nodal_container_expression: Kratos.Expression.NodalExpression) -> None"""
def ComputeNumberOfNeighbourElements(output_nodal_container_expression: Kratos.Expression.NodalExpression) -> None:
    """ComputeNumberOfNeighbourElements(output_nodal_container_expression: Kratos.Expression.NodalExpression) -> None"""
def EntityMax(collective_expressions: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression:
    """EntityMax(collective_expressions: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression"""
@overload
def EntityMaxNormL2(container_expression: Kratos.Expression.NodalExpression) -> float:
    """EntityMaxNormL2(*args, **kwargs)
    Overloaded function.

    1. EntityMaxNormL2(container_expression: Kratos.Expression.NodalExpression) -> float

    2. EntityMaxNormL2(container_expression: Kratos.Expression.ConditionExpression) -> float

    3. EntityMaxNormL2(container_expression: Kratos.Expression.ElementExpression) -> float
    """
@overload
def EntityMaxNormL2(container_expression: Kratos.Expression.ConditionExpression) -> float:
    """EntityMaxNormL2(*args, **kwargs)
    Overloaded function.

    1. EntityMaxNormL2(container_expression: Kratos.Expression.NodalExpression) -> float

    2. EntityMaxNormL2(container_expression: Kratos.Expression.ConditionExpression) -> float

    3. EntityMaxNormL2(container_expression: Kratos.Expression.ElementExpression) -> float
    """
@overload
def EntityMaxNormL2(container_expression: Kratos.Expression.ElementExpression) -> float:
    """EntityMaxNormL2(*args, **kwargs)
    Overloaded function.

    1. EntityMaxNormL2(container_expression: Kratos.Expression.NodalExpression) -> float

    2. EntityMaxNormL2(container_expression: Kratos.Expression.ConditionExpression) -> float

    3. EntityMaxNormL2(container_expression: Kratos.Expression.ElementExpression) -> float
    """
def EntityMin(collective_expressions: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression:
    """EntityMin(collective_expressions: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression"""
def EntitySum(collective_expressions: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression:
    """EntitySum(collective_expressions: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression"""
@overload
def ExtractData(input_nodal_expression: Kratos.Expression.NodalExpression, model_part_domain_to_extract: Kratos.ModelPart) -> Kratos.Expression.NodalExpression:
    """ExtractData(*args, **kwargs)
    Overloaded function.

    1. ExtractData(input_nodal_expression: Kratos.Expression.NodalExpression, model_part_domain_to_extract: Kratos.ModelPart) -> Kratos.Expression.NodalExpression

    2. ExtractData(input_condition_expression: Kratos.Expression.ConditionExpression, model_part_domain_to_extract: Kratos.ModelPart) -> Kratos.Expression.ConditionExpression

    3. ExtractData(input_element_expression: Kratos.Expression.ElementExpression, model_part_domain_to_extract: Kratos.ModelPart) -> Kratos.Expression.ElementExpression
    """
@overload
def ExtractData(input_condition_expression: Kratos.Expression.ConditionExpression, model_part_domain_to_extract: Kratos.ModelPart) -> Kratos.Expression.ConditionExpression:
    """ExtractData(*args, **kwargs)
    Overloaded function.

    1. ExtractData(input_nodal_expression: Kratos.Expression.NodalExpression, model_part_domain_to_extract: Kratos.ModelPart) -> Kratos.Expression.NodalExpression

    2. ExtractData(input_condition_expression: Kratos.Expression.ConditionExpression, model_part_domain_to_extract: Kratos.ModelPart) -> Kratos.Expression.ConditionExpression

    3. ExtractData(input_element_expression: Kratos.Expression.ElementExpression, model_part_domain_to_extract: Kratos.ModelPart) -> Kratos.Expression.ElementExpression
    """
@overload
def ExtractData(input_element_expression: Kratos.Expression.ElementExpression, model_part_domain_to_extract: Kratos.ModelPart) -> Kratos.Expression.ElementExpression:
    """ExtractData(*args, **kwargs)
    Overloaded function.

    1. ExtractData(input_nodal_expression: Kratos.Expression.NodalExpression, model_part_domain_to_extract: Kratos.ModelPart) -> Kratos.Expression.NodalExpression

    2. ExtractData(input_condition_expression: Kratos.Expression.ConditionExpression, model_part_domain_to_extract: Kratos.ModelPart) -> Kratos.Expression.ConditionExpression

    3. ExtractData(input_element_expression: Kratos.Expression.ElementExpression, model_part_domain_to_extract: Kratos.ModelPart) -> Kratos.Expression.ElementExpression
    """
def InnerProduct(collective_expressions_1: KratosOptimizationApplication.CollectiveExpression, collective_expressions_2: KratosOptimizationApplication.CollectiveExpression) -> float:
    """InnerProduct(collective_expressions_1: KratosOptimizationApplication.CollectiveExpression, collective_expressions_2: KratosOptimizationApplication.CollectiveExpression) -> float"""
@overload
def MapContainerVariableToNodalVariable(output_nodal_container_expression: Kratos.Expression.NodalExpression, input_container_expression_to_map: Kratos.Expression.ConditionExpression, neighbour_container_for_nodes: Kratos.Expression.NodalExpression) -> None:
    """MapContainerVariableToNodalVariable(*args, **kwargs)
    Overloaded function.

    1. MapContainerVariableToNodalVariable(output_nodal_container_expression: Kratos.Expression.NodalExpression, input_container_expression_to_map: Kratos.Expression.ConditionExpression, neighbour_container_for_nodes: Kratos.Expression.NodalExpression) -> None

    2. MapContainerVariableToNodalVariable(output_nodal_container_expression: Kratos.Expression.NodalExpression, input_container_expression_to_map: Kratos.Expression.ElementExpression, neighbour_container_for_nodes: Kratos.Expression.NodalExpression) -> None
    """
@overload
def MapContainerVariableToNodalVariable(output_nodal_container_expression: Kratos.Expression.NodalExpression, input_container_expression_to_map: Kratos.Expression.ElementExpression, neighbour_container_for_nodes: Kratos.Expression.NodalExpression) -> None:
    """MapContainerVariableToNodalVariable(*args, **kwargs)
    Overloaded function.

    1. MapContainerVariableToNodalVariable(output_nodal_container_expression: Kratos.Expression.NodalExpression, input_container_expression_to_map: Kratos.Expression.ConditionExpression, neighbour_container_for_nodes: Kratos.Expression.NodalExpression) -> None

    2. MapContainerVariableToNodalVariable(output_nodal_container_expression: Kratos.Expression.NodalExpression, input_container_expression_to_map: Kratos.Expression.ElementExpression, neighbour_container_for_nodes: Kratos.Expression.NodalExpression) -> None
    """
@overload
def MapNodalVariableToContainerVariable(output_container_expression: Kratos.Expression.ConditionExpression, input_nodal_container_expression_to_map: Kratos.Expression.NodalExpression) -> None:
    """MapNodalVariableToContainerVariable(*args, **kwargs)
    Overloaded function.

    1. MapNodalVariableToContainerVariable(output_container_expression: Kratos.Expression.ConditionExpression, input_nodal_container_expression_to_map: Kratos.Expression.NodalExpression) -> None

    2. MapNodalVariableToContainerVariable(output_container_expression: Kratos.Expression.ElementExpression, input_nodal_container_expression_to_map: Kratos.Expression.NodalExpression) -> None
    """
@overload
def MapNodalVariableToContainerVariable(output_container_expression: Kratos.Expression.ElementExpression, input_nodal_container_expression_to_map: Kratos.Expression.NodalExpression) -> None:
    """MapNodalVariableToContainerVariable(*args, **kwargs)
    Overloaded function.

    1. MapNodalVariableToContainerVariable(output_container_expression: Kratos.Expression.ConditionExpression, input_nodal_container_expression_to_map: Kratos.Expression.NodalExpression) -> None

    2. MapNodalVariableToContainerVariable(output_container_expression: Kratos.Expression.ElementExpression, input_nodal_container_expression_to_map: Kratos.Expression.NodalExpression) -> None
    """
def NormInf(collective_expressions: KratosOptimizationApplication.CollectiveExpression) -> float:
    """NormInf(collective_expressions: KratosOptimizationApplication.CollectiveExpression) -> float"""
def NormL2(collective_expressions: KratosOptimizationApplication.CollectiveExpression) -> float:
    """NormL2(collective_expressions: KratosOptimizationApplication.CollectiveExpression) -> float"""
@overload
def Pow(collective_expression: KratosOptimizationApplication.CollectiveExpression, power_coeff: float) -> KratosOptimizationApplication.CollectiveExpression:
    """Pow(*args, **kwargs)
    Overloaded function.

    1. Pow(collective_expression: KratosOptimizationApplication.CollectiveExpression, power_coeff: float) -> KratosOptimizationApplication.CollectiveExpression

    2. Pow(collective_expression: KratosOptimizationApplication.CollectiveExpression, power_coeff_collective_expression: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression
    """
@overload
def Pow(collective_expression: KratosOptimizationApplication.CollectiveExpression, power_coeff_collective_expression: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression:
    """Pow(*args, **kwargs)
    Overloaded function.

    1. Pow(collective_expression: KratosOptimizationApplication.CollectiveExpression, power_coeff: float) -> KratosOptimizationApplication.CollectiveExpression

    2. Pow(collective_expression: KratosOptimizationApplication.CollectiveExpression, power_coeff_collective_expression: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression
    """
@overload
def ProductWithEntityMatrix(output_container_expression: Kratos.Expression.NodalExpression, matrix_with_entity_size: Kratos.Matrix, input_container_expression_for_multiplication: Kratos.Expression.NodalExpression) -> None:
    """ProductWithEntityMatrix(*args, **kwargs)
    Overloaded function.

    1. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.NodalExpression, matrix_with_entity_size: Kratos.Matrix, input_container_expression_for_multiplication: Kratos.Expression.NodalExpression) -> None

    2. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ConditionExpression, matrix_with_entity_size: Kratos.Matrix, input_container_expression_for_multiplication: Kratos.Expression.ConditionExpression) -> None

    3. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ElementExpression, matrix_with_entity_size: Kratos.Matrix, input_container_expression_for_multiplication: Kratos.Expression.ElementExpression) -> None

    4. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.NodalExpression, matrix_with_entity_size: Kratos.CompressedMatrix, input_container_expression_for_multiplication: Kratos.Expression.NodalExpression) -> None

    5. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ConditionExpression, matrix_with_entity_size: Kratos.CompressedMatrix, input_container_expression_for_multiplication: Kratos.Expression.ConditionExpression) -> None

    6. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ElementExpression, matrix_with_entity_size: Kratos.CompressedMatrix, input_container_expression_for_multiplication: Kratos.Expression.ElementExpression) -> None
    """
@overload
def ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ConditionExpression, matrix_with_entity_size: Kratos.Matrix, input_container_expression_for_multiplication: Kratos.Expression.ConditionExpression) -> None:
    """ProductWithEntityMatrix(*args, **kwargs)
    Overloaded function.

    1. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.NodalExpression, matrix_with_entity_size: Kratos.Matrix, input_container_expression_for_multiplication: Kratos.Expression.NodalExpression) -> None

    2. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ConditionExpression, matrix_with_entity_size: Kratos.Matrix, input_container_expression_for_multiplication: Kratos.Expression.ConditionExpression) -> None

    3. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ElementExpression, matrix_with_entity_size: Kratos.Matrix, input_container_expression_for_multiplication: Kratos.Expression.ElementExpression) -> None

    4. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.NodalExpression, matrix_with_entity_size: Kratos.CompressedMatrix, input_container_expression_for_multiplication: Kratos.Expression.NodalExpression) -> None

    5. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ConditionExpression, matrix_with_entity_size: Kratos.CompressedMatrix, input_container_expression_for_multiplication: Kratos.Expression.ConditionExpression) -> None

    6. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ElementExpression, matrix_with_entity_size: Kratos.CompressedMatrix, input_container_expression_for_multiplication: Kratos.Expression.ElementExpression) -> None
    """
@overload
def ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ElementExpression, matrix_with_entity_size: Kratos.Matrix, input_container_expression_for_multiplication: Kratos.Expression.ElementExpression) -> None:
    """ProductWithEntityMatrix(*args, **kwargs)
    Overloaded function.

    1. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.NodalExpression, matrix_with_entity_size: Kratos.Matrix, input_container_expression_for_multiplication: Kratos.Expression.NodalExpression) -> None

    2. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ConditionExpression, matrix_with_entity_size: Kratos.Matrix, input_container_expression_for_multiplication: Kratos.Expression.ConditionExpression) -> None

    3. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ElementExpression, matrix_with_entity_size: Kratos.Matrix, input_container_expression_for_multiplication: Kratos.Expression.ElementExpression) -> None

    4. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.NodalExpression, matrix_with_entity_size: Kratos.CompressedMatrix, input_container_expression_for_multiplication: Kratos.Expression.NodalExpression) -> None

    5. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ConditionExpression, matrix_with_entity_size: Kratos.CompressedMatrix, input_container_expression_for_multiplication: Kratos.Expression.ConditionExpression) -> None

    6. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ElementExpression, matrix_with_entity_size: Kratos.CompressedMatrix, input_container_expression_for_multiplication: Kratos.Expression.ElementExpression) -> None
    """
@overload
def ProductWithEntityMatrix(output_container_expression: Kratos.Expression.NodalExpression, matrix_with_entity_size: Kratos.CompressedMatrix, input_container_expression_for_multiplication: Kratos.Expression.NodalExpression) -> None:
    """ProductWithEntityMatrix(*args, **kwargs)
    Overloaded function.

    1. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.NodalExpression, matrix_with_entity_size: Kratos.Matrix, input_container_expression_for_multiplication: Kratos.Expression.NodalExpression) -> None

    2. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ConditionExpression, matrix_with_entity_size: Kratos.Matrix, input_container_expression_for_multiplication: Kratos.Expression.ConditionExpression) -> None

    3. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ElementExpression, matrix_with_entity_size: Kratos.Matrix, input_container_expression_for_multiplication: Kratos.Expression.ElementExpression) -> None

    4. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.NodalExpression, matrix_with_entity_size: Kratos.CompressedMatrix, input_container_expression_for_multiplication: Kratos.Expression.NodalExpression) -> None

    5. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ConditionExpression, matrix_with_entity_size: Kratos.CompressedMatrix, input_container_expression_for_multiplication: Kratos.Expression.ConditionExpression) -> None

    6. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ElementExpression, matrix_with_entity_size: Kratos.CompressedMatrix, input_container_expression_for_multiplication: Kratos.Expression.ElementExpression) -> None
    """
@overload
def ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ConditionExpression, matrix_with_entity_size: Kratos.CompressedMatrix, input_container_expression_for_multiplication: Kratos.Expression.ConditionExpression) -> None:
    """ProductWithEntityMatrix(*args, **kwargs)
    Overloaded function.

    1. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.NodalExpression, matrix_with_entity_size: Kratos.Matrix, input_container_expression_for_multiplication: Kratos.Expression.NodalExpression) -> None

    2. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ConditionExpression, matrix_with_entity_size: Kratos.Matrix, input_container_expression_for_multiplication: Kratos.Expression.ConditionExpression) -> None

    3. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ElementExpression, matrix_with_entity_size: Kratos.Matrix, input_container_expression_for_multiplication: Kratos.Expression.ElementExpression) -> None

    4. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.NodalExpression, matrix_with_entity_size: Kratos.CompressedMatrix, input_container_expression_for_multiplication: Kratos.Expression.NodalExpression) -> None

    5. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ConditionExpression, matrix_with_entity_size: Kratos.CompressedMatrix, input_container_expression_for_multiplication: Kratos.Expression.ConditionExpression) -> None

    6. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ElementExpression, matrix_with_entity_size: Kratos.CompressedMatrix, input_container_expression_for_multiplication: Kratos.Expression.ElementExpression) -> None
    """
@overload
def ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ElementExpression, matrix_with_entity_size: Kratos.CompressedMatrix, input_container_expression_for_multiplication: Kratos.Expression.ElementExpression) -> None:
    """ProductWithEntityMatrix(*args, **kwargs)
    Overloaded function.

    1. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.NodalExpression, matrix_with_entity_size: Kratos.Matrix, input_container_expression_for_multiplication: Kratos.Expression.NodalExpression) -> None

    2. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ConditionExpression, matrix_with_entity_size: Kratos.Matrix, input_container_expression_for_multiplication: Kratos.Expression.ConditionExpression) -> None

    3. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ElementExpression, matrix_with_entity_size: Kratos.Matrix, input_container_expression_for_multiplication: Kratos.Expression.ElementExpression) -> None

    4. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.NodalExpression, matrix_with_entity_size: Kratos.CompressedMatrix, input_container_expression_for_multiplication: Kratos.Expression.NodalExpression) -> None

    5. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ConditionExpression, matrix_with_entity_size: Kratos.CompressedMatrix, input_container_expression_for_multiplication: Kratos.Expression.ConditionExpression) -> None

    6. ProductWithEntityMatrix(output_container_expression: Kratos.Expression.ElementExpression, matrix_with_entity_size: Kratos.CompressedMatrix, input_container_expression_for_multiplication: Kratos.Expression.ElementExpression) -> None
    """
@overload
def Scale(collective_expression: KratosOptimizationApplication.CollectiveExpression, scaling_coeff: float) -> KratosOptimizationApplication.CollectiveExpression:
    """Scale(*args, **kwargs)
    Overloaded function.

    1. Scale(collective_expression: KratosOptimizationApplication.CollectiveExpression, scaling_coeff: float) -> KratosOptimizationApplication.CollectiveExpression

    2. Scale(collective_expression: KratosOptimizationApplication.CollectiveExpression, scaling_coeff_collective_expression: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression
    """
@overload
def Scale(collective_expression: KratosOptimizationApplication.CollectiveExpression, scaling_coeff_collective_expression: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression:
    """Scale(*args, **kwargs)
    Overloaded function.

    1. Scale(collective_expression: KratosOptimizationApplication.CollectiveExpression, scaling_coeff: float) -> KratosOptimizationApplication.CollectiveExpression

    2. Scale(collective_expression: KratosOptimizationApplication.CollectiveExpression, scaling_coeff_collective_expression: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression
    """
def Sum(collective_expressions: KratosOptimizationApplication.CollectiveExpression) -> float:
    """Sum(collective_expressions: KratosOptimizationApplication.CollectiveExpression) -> float"""
@overload
def Transpose(output_matrix: Kratos.CompressedMatrix, input_matrix: Kratos.CompressedMatrix) -> None:
    """Transpose(*args, **kwargs)
    Overloaded function.

    1. Transpose(output_matrix: Kratos.CompressedMatrix, input_matrix: Kratos.CompressedMatrix) -> None

    2. Transpose(output_matrix: Kratos.Matrix, input_matrix: Kratos.Matrix) -> None
    """
@overload
def Transpose(output_matrix: Kratos.Matrix, input_matrix: Kratos.Matrix) -> None:
    """Transpose(*args, **kwargs)
    Overloaded function.

    1. Transpose(output_matrix: Kratos.CompressedMatrix, input_matrix: Kratos.CompressedMatrix) -> None

    2. Transpose(output_matrix: Kratos.Matrix, input_matrix: Kratos.Matrix) -> None
    """
