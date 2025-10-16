import Kratos
import Kratos.Expression
import numpy
from . import CollectiveExpressionIO as CollectiveExpressionIO, ControlUtils as ControlUtils, ExpressionUtils as ExpressionUtils, ImplicitFilterUtils as ImplicitFilterUtils, OptAppModelPartUtils as OptAppModelPartUtils, OptimizationUtils as OptimizationUtils, PropertiesVariableExpressionIO as PropertiesVariableExpressionIO, ResponseUtils as ResponseUtils
from typing import overload

class CollectiveExpression:
    @overload
    def __init__(self) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosOptimizationApplication.CollectiveExpression) -> None

        2. __init__(self: KratosOptimizationApplication.CollectiveExpression, arg0: list[Union[Kratos.Expression.NodalExpression, Kratos.Expression.ConditionExpression, Kratos.Expression.ElementExpression]]) -> None
        """
    @overload
    def __init__(self, arg0: list[Kratos.Expression.NodalExpression | Kratos.Expression.ConditionExpression | Kratos.Expression.ElementExpression]) -> None:
        """__init__(*args, **kwargs)
        Overloaded function.

        1. __init__(self: KratosOptimizationApplication.CollectiveExpression) -> None

        2. __init__(self: KratosOptimizationApplication.CollectiveExpression, arg0: list[Union[Kratos.Expression.NodalExpression, Kratos.Expression.ConditionExpression, Kratos.Expression.ElementExpression]]) -> None
        """
    @overload
    def Add(self, arg0: Kratos.Expression.NodalExpression | Kratos.Expression.ConditionExpression | Kratos.Expression.ElementExpression) -> None:
        """Add(*args, **kwargs)
        Overloaded function.

        1. Add(self: KratosOptimizationApplication.CollectiveExpression, arg0: Union[Kratos.Expression.NodalExpression, Kratos.Expression.ConditionExpression, Kratos.Expression.ElementExpression]) -> None

        2. Add(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> None
        """
    @overload
    def Add(self, arg0: CollectiveExpression) -> None:
        """Add(*args, **kwargs)
        Overloaded function.

        1. Add(self: KratosOptimizationApplication.CollectiveExpression, arg0: Union[Kratos.Expression.NodalExpression, Kratos.Expression.ConditionExpression, Kratos.Expression.ElementExpression]) -> None

        2. Add(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> None
        """
    def Clear(self) -> None:
        """Clear(self: KratosOptimizationApplication.CollectiveExpression) -> None"""
    def Clone(self) -> CollectiveExpression:
        """Clone(self: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression"""
    def Evaluate(self) -> numpy.ndarray[numpy.float64]:
        """Evaluate(self: KratosOptimizationApplication.CollectiveExpression) -> numpy.ndarray[numpy.float64]"""
    def GetCollectiveFlattenedDataSize(self) -> int:
        """GetCollectiveFlattenedDataSize(self: KratosOptimizationApplication.CollectiveExpression) -> int"""
    def GetContainerExpressions(self) -> list[Kratos.Expression.NodalExpression | Kratos.Expression.ConditionExpression | Kratos.Expression.ElementExpression]:
        """GetContainerExpressions(self: KratosOptimizationApplication.CollectiveExpression) -> list[Union[Kratos.Expression.NodalExpression, Kratos.Expression.ConditionExpression, Kratos.Expression.ElementExpression]]"""
    def IsCompatibleWith(self, arg0: CollectiveExpression) -> bool:
        """IsCompatibleWith(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> bool"""
    @overload
    def __add__(self, arg0: CollectiveExpression) -> CollectiveExpression:
        """__add__(*args, **kwargs)
        Overloaded function.

        1. __add__(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression

        2. __add__(self: KratosOptimizationApplication.CollectiveExpression, arg0: float) -> KratosOptimizationApplication.CollectiveExpression
        """
    @overload
    def __add__(self, arg0: float) -> CollectiveExpression:
        """__add__(*args, **kwargs)
        Overloaded function.

        1. __add__(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression

        2. __add__(self: KratosOptimizationApplication.CollectiveExpression, arg0: float) -> KratosOptimizationApplication.CollectiveExpression
        """
    @overload
    def __iadd__(self, arg0: CollectiveExpression) -> CollectiveExpression:
        """__iadd__(*args, **kwargs)
        Overloaded function.

        1. __iadd__(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression

        2. __iadd__(self: KratosOptimizationApplication.CollectiveExpression, arg0: float) -> KratosOptimizationApplication.CollectiveExpression
        """
    @overload
    def __iadd__(self, arg0: float) -> CollectiveExpression:
        """__iadd__(*args, **kwargs)
        Overloaded function.

        1. __iadd__(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression

        2. __iadd__(self: KratosOptimizationApplication.CollectiveExpression, arg0: float) -> KratosOptimizationApplication.CollectiveExpression
        """
    @overload
    def __imul__(self, arg0: CollectiveExpression) -> CollectiveExpression:
        """__imul__(*args, **kwargs)
        Overloaded function.

        1. __imul__(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression

        2. __imul__(self: KratosOptimizationApplication.CollectiveExpression, arg0: float) -> KratosOptimizationApplication.CollectiveExpression
        """
    @overload
    def __imul__(self, arg0: float) -> CollectiveExpression:
        """__imul__(*args, **kwargs)
        Overloaded function.

        1. __imul__(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression

        2. __imul__(self: KratosOptimizationApplication.CollectiveExpression, arg0: float) -> KratosOptimizationApplication.CollectiveExpression
        """
    @overload
    def __ipow__(self, arg0: CollectiveExpression) -> CollectiveExpression:
        """__ipow__(*args, **kwargs)
        Overloaded function.

        1. __ipow__(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression

        2. __ipow__(self: KratosOptimizationApplication.CollectiveExpression, arg0: float) -> KratosOptimizationApplication.CollectiveExpression
        """
    @overload
    def __ipow__(self, arg0: float) -> CollectiveExpression:
        """__ipow__(*args, **kwargs)
        Overloaded function.

        1. __ipow__(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression

        2. __ipow__(self: KratosOptimizationApplication.CollectiveExpression, arg0: float) -> KratosOptimizationApplication.CollectiveExpression
        """
    @overload
    def __isub__(self, arg0: CollectiveExpression) -> CollectiveExpression:
        """__isub__(*args, **kwargs)
        Overloaded function.

        1. __isub__(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression

        2. __isub__(self: KratosOptimizationApplication.CollectiveExpression, arg0: float) -> KratosOptimizationApplication.CollectiveExpression
        """
    @overload
    def __isub__(self, arg0: float) -> CollectiveExpression:
        """__isub__(*args, **kwargs)
        Overloaded function.

        1. __isub__(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression

        2. __isub__(self: KratosOptimizationApplication.CollectiveExpression, arg0: float) -> KratosOptimizationApplication.CollectiveExpression
        """
    @overload
    def __itruediv__(self, arg0: CollectiveExpression) -> CollectiveExpression:
        """__itruediv__(*args, **kwargs)
        Overloaded function.

        1. __itruediv__(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression

        2. __itruediv__(self: KratosOptimizationApplication.CollectiveExpression, arg0: float) -> KratosOptimizationApplication.CollectiveExpression
        """
    @overload
    def __itruediv__(self, arg0: float) -> CollectiveExpression:
        """__itruediv__(*args, **kwargs)
        Overloaded function.

        1. __itruediv__(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression

        2. __itruediv__(self: KratosOptimizationApplication.CollectiveExpression, arg0: float) -> KratosOptimizationApplication.CollectiveExpression
        """
    @overload
    def __mul__(self, arg0: CollectiveExpression) -> CollectiveExpression:
        """__mul__(*args, **kwargs)
        Overloaded function.

        1. __mul__(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression

        2. __mul__(self: KratosOptimizationApplication.CollectiveExpression, arg0: float) -> KratosOptimizationApplication.CollectiveExpression
        """
    @overload
    def __mul__(self, arg0: float) -> CollectiveExpression:
        """__mul__(*args, **kwargs)
        Overloaded function.

        1. __mul__(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression

        2. __mul__(self: KratosOptimizationApplication.CollectiveExpression, arg0: float) -> KratosOptimizationApplication.CollectiveExpression
        """
    def __neg__(self) -> CollectiveExpression:
        """__neg__(self: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression"""
    @overload
    def __pow__(self, arg0: CollectiveExpression) -> CollectiveExpression:
        """__pow__(*args, **kwargs)
        Overloaded function.

        1. __pow__(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression

        2. __pow__(self: KratosOptimizationApplication.CollectiveExpression, arg0: float) -> KratosOptimizationApplication.CollectiveExpression
        """
    @overload
    def __pow__(self, arg0: float) -> CollectiveExpression:
        """__pow__(*args, **kwargs)
        Overloaded function.

        1. __pow__(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression

        2. __pow__(self: KratosOptimizationApplication.CollectiveExpression, arg0: float) -> KratosOptimizationApplication.CollectiveExpression
        """
    @overload
    def __sub__(self, arg0: CollectiveExpression) -> CollectiveExpression:
        """__sub__(*args, **kwargs)
        Overloaded function.

        1. __sub__(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression

        2. __sub__(self: KratosOptimizationApplication.CollectiveExpression, arg0: float) -> KratosOptimizationApplication.CollectiveExpression
        """
    @overload
    def __sub__(self, arg0: float) -> CollectiveExpression:
        """__sub__(*args, **kwargs)
        Overloaded function.

        1. __sub__(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression

        2. __sub__(self: KratosOptimizationApplication.CollectiveExpression, arg0: float) -> KratosOptimizationApplication.CollectiveExpression
        """
    @overload
    def __truediv__(self, arg0: CollectiveExpression) -> CollectiveExpression:
        """__truediv__(*args, **kwargs)
        Overloaded function.

        1. __truediv__(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression

        2. __truediv__(self: KratosOptimizationApplication.CollectiveExpression, arg0: float) -> KratosOptimizationApplication.CollectiveExpression
        """
    @overload
    def __truediv__(self, arg0: float) -> CollectiveExpression:
        """__truediv__(*args, **kwargs)
        Overloaded function.

        1. __truediv__(self: KratosOptimizationApplication.CollectiveExpression, arg0: KratosOptimizationApplication.CollectiveExpression) -> KratosOptimizationApplication.CollectiveExpression

        2. __truediv__(self: KratosOptimizationApplication.CollectiveExpression, arg0: float) -> KratosOptimizationApplication.CollectiveExpression
        """

class ConditionExplicitDamping:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def CalculateMatrix(self, output_matrix: Kratos.Matrix, component_index: int) -> None:
        """CalculateMatrix(self: KratosOptimizationApplication.ConditionExplicitDamping, output_matrix: Kratos.Matrix, component_index: int) -> None"""
    def GetDampedModelParts(self) -> list[list[Kratos.ModelPart]]:
        """GetDampedModelParts(self: KratosOptimizationApplication.ConditionExplicitDamping) -> list[list[Kratos.ModelPart]]"""
    def GetRadius(self) -> Kratos.Expression.ConditionExpression:
        """GetRadius(self: KratosOptimizationApplication.ConditionExplicitDamping) -> Kratos.Expression.ConditionExpression"""
    def GetStride(self) -> int:
        """GetStride(self: KratosOptimizationApplication.ConditionExplicitDamping) -> int"""
    def SetRadius(self, radius_expression: Kratos.Expression.ConditionExpression) -> None:
        """SetRadius(self: KratosOptimizationApplication.ConditionExplicitDamping, radius_expression: Kratos.Expression.ConditionExpression) -> None"""
    def Update(self) -> None:
        """Update(self: KratosOptimizationApplication.ConditionExplicitDamping) -> None"""

class ConditionExplicitFilterUtils:
    def __init__(self, model_part: Kratos.ModelPart, kernel_function_type: str, max_number_of_neighbours: int, echo_level: int) -> None:
        """__init__(self: KratosOptimizationApplication.ConditionExplicitFilterUtils, model_part: Kratos.ModelPart, kernel_function_type: str, max_number_of_neighbours: int, echo_level: int) -> None"""
    def BackwardFilterField(self, physical_space_mesh_independent_gradient: Kratos.Expression.ConditionExpression) -> Kratos.Expression.ConditionExpression:
        """BackwardFilterField(self: KratosOptimizationApplication.ConditionExplicitFilterUtils, physical_space_mesh_independent_gradient: Kratos.Expression.ConditionExpression) -> Kratos.Expression.ConditionExpression"""
    def BackwardFilterIntegratedField(self, physical_space_mesh_dependent_gradient: Kratos.Expression.ConditionExpression) -> Kratos.Expression.ConditionExpression:
        """BackwardFilterIntegratedField(self: KratosOptimizationApplication.ConditionExplicitFilterUtils, physical_space_mesh_dependent_gradient: Kratos.Expression.ConditionExpression) -> Kratos.Expression.ConditionExpression"""
    def CalculateMatrix(self, output_filtering_matrix: Kratos.Matrix) -> None:
        """CalculateMatrix(self: KratosOptimizationApplication.ConditionExplicitFilterUtils, output_filtering_matrix: Kratos.Matrix) -> None"""
    def ForwardFilterField(self, mesh_independent_control_space_field: Kratos.Expression.ConditionExpression) -> Kratos.Expression.ConditionExpression:
        """ForwardFilterField(self: KratosOptimizationApplication.ConditionExplicitFilterUtils, mesh_independent_control_space_field: Kratos.Expression.ConditionExpression) -> Kratos.Expression.ConditionExpression"""
    def GetIntegrationWeights(self, integration_weight_field: Kratos.Expression.ConditionExpression) -> None:
        """GetIntegrationWeights(self: KratosOptimizationApplication.ConditionExplicitFilterUtils, integration_weight_field: Kratos.Expression.ConditionExpression) -> None"""
    def GetRadius(self) -> Kratos.Expression.ConditionExpression:
        """GetRadius(self: KratosOptimizationApplication.ConditionExplicitFilterUtils) -> Kratos.Expression.ConditionExpression"""
    def SetDamping(self, damping: ConditionExplicitDamping) -> None:
        """SetDamping(self: KratosOptimizationApplication.ConditionExplicitFilterUtils, damping: KratosOptimizationApplication.ConditionExplicitDamping) -> None"""
    def SetRadius(self, filter_radius: Kratos.Expression.ConditionExpression) -> None:
        """SetRadius(self: KratosOptimizationApplication.ConditionExplicitFilterUtils, filter_radius: Kratos.Expression.ConditionExpression) -> None"""
    def Update(self) -> None:
        """Update(self: KratosOptimizationApplication.ConditionExplicitFilterUtils) -> None"""

class ElementExplicitDamping:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def CalculateMatrix(self, output_matrix: Kratos.Matrix, component_index: int) -> None:
        """CalculateMatrix(self: KratosOptimizationApplication.ElementExplicitDamping, output_matrix: Kratos.Matrix, component_index: int) -> None"""
    def GetDampedModelParts(self) -> list[list[Kratos.ModelPart]]:
        """GetDampedModelParts(self: KratosOptimizationApplication.ElementExplicitDamping) -> list[list[Kratos.ModelPart]]"""
    def GetRadius(self) -> Kratos.Expression.ElementExpression:
        """GetRadius(self: KratosOptimizationApplication.ElementExplicitDamping) -> Kratos.Expression.ElementExpression"""
    def GetStride(self) -> int:
        """GetStride(self: KratosOptimizationApplication.ElementExplicitDamping) -> int"""
    def SetRadius(self, radius_expression: Kratos.Expression.ElementExpression) -> None:
        """SetRadius(self: KratosOptimizationApplication.ElementExplicitDamping, radius_expression: Kratos.Expression.ElementExpression) -> None"""
    def Update(self) -> None:
        """Update(self: KratosOptimizationApplication.ElementExplicitDamping) -> None"""

class ElementExplicitFilterUtils:
    def __init__(self, model_part: Kratos.ModelPart, kernel_function_type: str, max_number_of_neighbours: int, echo_level: int) -> None:
        """__init__(self: KratosOptimizationApplication.ElementExplicitFilterUtils, model_part: Kratos.ModelPart, kernel_function_type: str, max_number_of_neighbours: int, echo_level: int) -> None"""
    def BackwardFilterField(self, physical_space_mesh_independent_gradient: Kratos.Expression.ElementExpression) -> Kratos.Expression.ElementExpression:
        """BackwardFilterField(self: KratosOptimizationApplication.ElementExplicitFilterUtils, physical_space_mesh_independent_gradient: Kratos.Expression.ElementExpression) -> Kratos.Expression.ElementExpression"""
    def BackwardFilterIntegratedField(self, physical_space_mesh_dependent_gradient: Kratos.Expression.ElementExpression) -> Kratos.Expression.ElementExpression:
        """BackwardFilterIntegratedField(self: KratosOptimizationApplication.ElementExplicitFilterUtils, physical_space_mesh_dependent_gradient: Kratos.Expression.ElementExpression) -> Kratos.Expression.ElementExpression"""
    def CalculateMatrix(self, output_filtering_matrix: Kratos.Matrix) -> None:
        """CalculateMatrix(self: KratosOptimizationApplication.ElementExplicitFilterUtils, output_filtering_matrix: Kratos.Matrix) -> None"""
    def ForwardFilterField(self, mesh_independent_control_space_field: Kratos.Expression.ElementExpression) -> Kratos.Expression.ElementExpression:
        """ForwardFilterField(self: KratosOptimizationApplication.ElementExplicitFilterUtils, mesh_independent_control_space_field: Kratos.Expression.ElementExpression) -> Kratos.Expression.ElementExpression"""
    def GetIntegrationWeights(self, integration_weight_field: Kratos.Expression.ElementExpression) -> None:
        """GetIntegrationWeights(self: KratosOptimizationApplication.ElementExplicitFilterUtils, integration_weight_field: Kratos.Expression.ElementExpression) -> None"""
    def GetRadius(self) -> Kratos.Expression.ElementExpression:
        """GetRadius(self: KratosOptimizationApplication.ElementExplicitFilterUtils) -> Kratos.Expression.ElementExpression"""
    def SetDamping(self, damping: ElementExplicitDamping) -> None:
        """SetDamping(self: KratosOptimizationApplication.ElementExplicitFilterUtils, damping: KratosOptimizationApplication.ElementExplicitDamping) -> None"""
    def SetRadius(self, filter_radius: Kratos.Expression.ElementExpression) -> None:
        """SetRadius(self: KratosOptimizationApplication.ElementExplicitFilterUtils, filter_radius: Kratos.Expression.ElementExpression) -> None"""
    def Update(self) -> None:
        """Update(self: KratosOptimizationApplication.ElementExplicitFilterUtils) -> None"""

class HelmholtzJacobianStiffened3DLaw(Kratos.ConstitutiveLaw):
    def __init__(self) -> None:
        """__init__(self: KratosOptimizationApplication.HelmholtzJacobianStiffened3DLaw) -> None"""

class IntegratedNearestConditionExplicitDamping(ConditionExplicitDamping):
    def __init__(self, model: Kratos.Model, parameters: Kratos.Parameters, stride: int) -> None:
        """__init__(self: KratosOptimizationApplication.IntegratedNearestConditionExplicitDamping, model: Kratos.Model, parameters: Kratos.Parameters, stride: int) -> None"""

class IntegratedNearestElementExplicitDamping(ElementExplicitDamping):
    def __init__(self, model: Kratos.Model, parameters: Kratos.Parameters, stride: int) -> None:
        """__init__(self: KratosOptimizationApplication.IntegratedNearestElementExplicitDamping, model: Kratos.Model, parameters: Kratos.Parameters, stride: int) -> None"""

class IntegratedNearestNodeExplicitDamping(NodeExplicitDamping):
    def __init__(self, model: Kratos.Model, parameters: Kratos.Parameters, stride: int) -> None:
        """__init__(self: KratosOptimizationApplication.IntegratedNearestNodeExplicitDamping, model: Kratos.Model, parameters: Kratos.Parameters, stride: int) -> None"""

class InterfaceOptResponse:
    def __init__(self, arg0: str, arg1: Kratos.Model, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosOptimizationApplication.InterfaceOptResponse, arg0: str, arg1: Kratos.Model, arg2: Kratos.Parameters) -> None"""
    def CalculateGradient(self) -> None:
        """CalculateGradient(self: KratosOptimizationApplication.InterfaceOptResponse) -> None"""
    def CalculateValue(self) -> float:
        """CalculateValue(self: KratosOptimizationApplication.InterfaceOptResponse) -> float"""
    def Initialize(self) -> None:
        """Initialize(self: KratosOptimizationApplication.InterfaceOptResponse) -> None"""

class KratosOptimizationApplication(Kratos.KratosApplication):
    def __init__(self) -> None:
        """__init__(self: KratosOptimizationApplication.KratosOptimizationApplication) -> None"""

class LinearStrainEnergyOptResponse:
    def __init__(self, arg0: str, arg1: Kratos.Model, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosOptimizationApplication.LinearStrainEnergyOptResponse, arg0: str, arg1: Kratos.Model, arg2: Kratos.Parameters) -> None"""
    def CalculateGradient(self) -> None:
        """CalculateGradient(self: KratosOptimizationApplication.LinearStrainEnergyOptResponse) -> None"""
    def CalculateValue(self) -> float:
        """CalculateValue(self: KratosOptimizationApplication.LinearStrainEnergyOptResponse) -> float"""
    def Initialize(self) -> None:
        """Initialize(self: KratosOptimizationApplication.LinearStrainEnergyOptResponse) -> None"""

class MassOptResponse:
    def __init__(self, arg0: str, arg1: Kratos.Model, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosOptimizationApplication.MassOptResponse, arg0: str, arg1: Kratos.Model, arg2: Kratos.Parameters) -> None"""
    def CalculateGradient(self) -> None:
        """CalculateGradient(self: KratosOptimizationApplication.MassOptResponse) -> None"""
    def CalculateValue(self) -> float:
        """CalculateValue(self: KratosOptimizationApplication.MassOptResponse) -> float"""
    def Initialize(self) -> None:
        """Initialize(self: KratosOptimizationApplication.MassOptResponse) -> None"""

class NearestConditionExplicitDamping(ConditionExplicitDamping):
    def __init__(self, model: Kratos.Model, parameters: Kratos.Parameters, stride: int) -> None:
        """__init__(self: KratosOptimizationApplication.NearestConditionExplicitDamping, model: Kratos.Model, parameters: Kratos.Parameters, stride: int) -> None"""

class NearestElementExplicitDamping(ElementExplicitDamping):
    def __init__(self, model: Kratos.Model, parameters: Kratos.Parameters, stride: int) -> None:
        """__init__(self: KratosOptimizationApplication.NearestElementExplicitDamping, model: Kratos.Model, parameters: Kratos.Parameters, stride: int) -> None"""

class NearestNodeExplicitDamping(NodeExplicitDamping):
    def __init__(self, model: Kratos.Model, parameters: Kratos.Parameters, stride: int) -> None:
        """__init__(self: KratosOptimizationApplication.NearestNodeExplicitDamping, model: Kratos.Model, parameters: Kratos.Parameters, stride: int) -> None"""

class NodeExplicitDamping:
    def __init__(self, *args, **kwargs) -> None:
        """Initialize self.  See help(type(self)) for accurate signature."""
    def CalculateMatrix(self, output_matrix: Kratos.Matrix, component_index: int) -> None:
        """CalculateMatrix(self: KratosOptimizationApplication.NodeExplicitDamping, output_matrix: Kratos.Matrix, component_index: int) -> None"""
    def GetDampedModelParts(self) -> list[list[Kratos.ModelPart]]:
        """GetDampedModelParts(self: KratosOptimizationApplication.NodeExplicitDamping) -> list[list[Kratos.ModelPart]]"""
    def GetRadius(self) -> Kratos.Expression.NodalExpression:
        """GetRadius(self: KratosOptimizationApplication.NodeExplicitDamping) -> Kratos.Expression.NodalExpression"""
    def GetStride(self) -> int:
        """GetStride(self: KratosOptimizationApplication.NodeExplicitDamping) -> int"""
    def SetRadius(self, radius_expression: Kratos.Expression.NodalExpression) -> None:
        """SetRadius(self: KratosOptimizationApplication.NodeExplicitDamping, radius_expression: Kratos.Expression.NodalExpression) -> None"""
    def Update(self) -> None:
        """Update(self: KratosOptimizationApplication.NodeExplicitDamping) -> None"""

class NodeExplicitFilterUtils:
    def __init__(self, model_part: Kratos.ModelPart, kernel_function_type: str, max_number_of_neighbours: int, echo_level: int) -> None:
        """__init__(self: KratosOptimizationApplication.NodeExplicitFilterUtils, model_part: Kratos.ModelPart, kernel_function_type: str, max_number_of_neighbours: int, echo_level: int) -> None"""
    def BackwardFilterField(self, physical_space_mesh_independent_gradient: Kratos.Expression.NodalExpression) -> Kratos.Expression.NodalExpression:
        """BackwardFilterField(self: KratosOptimizationApplication.NodeExplicitFilterUtils, physical_space_mesh_independent_gradient: Kratos.Expression.NodalExpression) -> Kratos.Expression.NodalExpression"""
    def BackwardFilterIntegratedField(self, physical_space_mesh_dependent_gradient: Kratos.Expression.NodalExpression) -> Kratos.Expression.NodalExpression:
        """BackwardFilterIntegratedField(self: KratosOptimizationApplication.NodeExplicitFilterUtils, physical_space_mesh_dependent_gradient: Kratos.Expression.NodalExpression) -> Kratos.Expression.NodalExpression"""
    def CalculateMatrix(self, output_filtering_matrix: Kratos.Matrix) -> None:
        """CalculateMatrix(self: KratosOptimizationApplication.NodeExplicitFilterUtils, output_filtering_matrix: Kratos.Matrix) -> None"""
    def ForwardFilterField(self, mesh_independent_control_space_field: Kratos.Expression.NodalExpression) -> Kratos.Expression.NodalExpression:
        """ForwardFilterField(self: KratosOptimizationApplication.NodeExplicitFilterUtils, mesh_independent_control_space_field: Kratos.Expression.NodalExpression) -> Kratos.Expression.NodalExpression"""
    def GetIntegrationWeights(self, integration_weight_field: Kratos.Expression.NodalExpression) -> None:
        """GetIntegrationWeights(self: KratosOptimizationApplication.NodeExplicitFilterUtils, integration_weight_field: Kratos.Expression.NodalExpression) -> None"""
    def GetRadius(self) -> Kratos.Expression.NodalExpression:
        """GetRadius(self: KratosOptimizationApplication.NodeExplicitFilterUtils) -> Kratos.Expression.NodalExpression"""
    def SetDamping(self, damping: NodeExplicitDamping) -> None:
        """SetDamping(self: KratosOptimizationApplication.NodeExplicitFilterUtils, damping: KratosOptimizationApplication.NodeExplicitDamping) -> None"""
    def SetRadius(self, filter_radius: Kratos.Expression.NodalExpression) -> None:
        """SetRadius(self: KratosOptimizationApplication.NodeExplicitFilterUtils, filter_radius: Kratos.Expression.NodalExpression) -> None"""
    def Update(self) -> None:
        """Update(self: KratosOptimizationApplication.NodeExplicitFilterUtils) -> None"""

class PartitionInterfaceStressOptResponse:
    def __init__(self, arg0: str, arg1: Kratos.Model, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosOptimizationApplication.PartitionInterfaceStressOptResponse, arg0: str, arg1: Kratos.Model, arg2: Kratos.Parameters) -> None"""
    def CalculateGradient(self) -> None:
        """CalculateGradient(self: KratosOptimizationApplication.PartitionInterfaceStressOptResponse) -> None"""
    def CalculateValue(self) -> float:
        """CalculateValue(self: KratosOptimizationApplication.PartitionInterfaceStressOptResponse) -> float"""
    def Initialize(self) -> None:
        """Initialize(self: KratosOptimizationApplication.PartitionInterfaceStressOptResponse) -> None"""

class PartitionMassOptResponse:
    def __init__(self, arg0: str, arg1: Kratos.Model, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosOptimizationApplication.PartitionMassOptResponse, arg0: str, arg1: Kratos.Model, arg2: Kratos.Parameters) -> None"""
    def CalculateGradient(self) -> None:
        """CalculateGradient(self: KratosOptimizationApplication.PartitionMassOptResponse) -> None"""
    def CalculateValue(self) -> float:
        """CalculateValue(self: KratosOptimizationApplication.PartitionMassOptResponse) -> float"""
    def Initialize(self) -> None:
        """Initialize(self: KratosOptimizationApplication.PartitionMassOptResponse) -> None"""

class StressOptResponse:
    def __init__(self, arg0: str, arg1: Kratos.Model, arg2: Kratos.Parameters, arg3: list[Kratos.LinearSolver]) -> None:
        """__init__(self: KratosOptimizationApplication.StressOptResponse, arg0: str, arg1: Kratos.Model, arg2: Kratos.Parameters, arg3: list[Kratos.LinearSolver]) -> None"""
    def CalculateGradient(self) -> None:
        """CalculateGradient(self: KratosOptimizationApplication.StressOptResponse) -> None"""
    def CalculateValue(self) -> float:
        """CalculateValue(self: KratosOptimizationApplication.StressOptResponse) -> float"""
    def Initialize(self) -> None:
        """Initialize(self: KratosOptimizationApplication.StressOptResponse) -> None"""

class SymmetryUtility:
    def __init__(self, arg0: str, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None:
        """__init__(self: KratosOptimizationApplication.SymmetryUtility, arg0: str, arg1: Kratos.ModelPart, arg2: Kratos.Parameters) -> None"""
    def ApplyOnScalarField(self, arg0: Kratos.DoubleVariable) -> None:
        """ApplyOnScalarField(self: KratosOptimizationApplication.SymmetryUtility, arg0: Kratos.DoubleVariable) -> None"""
    def ApplyOnVectorField(self, arg0: Kratos.Array1DVariable3) -> None:
        """ApplyOnVectorField(self: KratosOptimizationApplication.SymmetryUtility, arg0: Kratos.Array1DVariable3) -> None"""
    def Initialize(self) -> None:
        """Initialize(self: KratosOptimizationApplication.SymmetryUtility) -> None"""
    def Update(self) -> None:
        """Update(self: KratosOptimizationApplication.SymmetryUtility) -> None"""
