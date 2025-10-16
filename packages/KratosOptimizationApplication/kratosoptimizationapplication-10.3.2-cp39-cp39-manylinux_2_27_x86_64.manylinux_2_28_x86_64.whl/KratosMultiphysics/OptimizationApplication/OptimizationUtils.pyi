import Kratos
from typing import overload

@overload
def AreAllEntitiesOfSameGeometryType(arg0: Kratos.ConditionsArray, arg1: Kratos.DataCommunicator) -> bool:
    """AreAllEntitiesOfSameGeometryType(*args, **kwargs)
    Overloaded function.

    1. AreAllEntitiesOfSameGeometryType(arg0: Kratos.ConditionsArray, arg1: Kratos.DataCommunicator) -> bool

    2. AreAllEntitiesOfSameGeometryType(arg0: Kratos.ElementsArray, arg1: Kratos.DataCommunicator) -> bool
    """
@overload
def AreAllEntitiesOfSameGeometryType(arg0: Kratos.ElementsArray, arg1: Kratos.DataCommunicator) -> bool:
    """AreAllEntitiesOfSameGeometryType(*args, **kwargs)
    Overloaded function.

    1. AreAllEntitiesOfSameGeometryType(arg0: Kratos.ConditionsArray, arg1: Kratos.DataCommunicator) -> bool

    2. AreAllEntitiesOfSameGeometryType(arg0: Kratos.ElementsArray, arg1: Kratos.DataCommunicator) -> bool
    """
@overload
def CreateEntitySpecificPropertiesForContainer(model_part: Kratos.ModelPart, container: Kratos.ConditionsArray, is_recursive: bool) -> None:
    """CreateEntitySpecificPropertiesForContainer(*args, **kwargs)
    Overloaded function.

    1. CreateEntitySpecificPropertiesForContainer(model_part: Kratos.ModelPart, container: Kratos.ConditionsArray, is_recursive: bool) -> None

    2. CreateEntitySpecificPropertiesForContainer(model_part: Kratos.ModelPart, container: Kratos.ElementsArray, is_recursive: bool) -> None
    """
@overload
def CreateEntitySpecificPropertiesForContainer(model_part: Kratos.ModelPart, container: Kratos.ElementsArray, is_recursive: bool) -> None:
    """CreateEntitySpecificPropertiesForContainer(*args, **kwargs)
    Overloaded function.

    1. CreateEntitySpecificPropertiesForContainer(model_part: Kratos.ModelPart, container: Kratos.ConditionsArray, is_recursive: bool) -> None

    2. CreateEntitySpecificPropertiesForContainer(model_part: Kratos.ModelPart, container: Kratos.ElementsArray, is_recursive: bool) -> None
    """
def GetComponentWiseModelParts(model: Kratos.Model, parameters: Kratos.Parameters) -> list[list[Kratos.ModelPart]]:
    """GetComponentWiseModelParts(model: Kratos.Model, parameters: Kratos.Parameters) -> list[list[Kratos.ModelPart]]"""
def GetSolutionStepVariableNamesList(model_part: Kratos.ModelPart) -> list[str]:
    """GetSolutionStepVariableNamesList(model_part: Kratos.ModelPart) -> list[str]"""
@overload
def GetVariableDimension(arg0: Kratos.DoubleVariable, arg1: int) -> int:
    """GetVariableDimension(*args, **kwargs)
    Overloaded function.

    1. GetVariableDimension(arg0: Kratos.DoubleVariable, arg1: int) -> int

    2. GetVariableDimension(arg0: Kratos.Array1DVariable3, arg1: int) -> int
    """
@overload
def GetVariableDimension(arg0: Kratos.Array1DVariable3, arg1: int) -> int:
    """GetVariableDimension(*args, **kwargs)
    Overloaded function.

    1. GetVariableDimension(arg0: Kratos.DoubleVariable, arg1: int) -> int

    2. GetVariableDimension(arg0: Kratos.Array1DVariable3, arg1: int) -> int
    """
def IsSolutionStepVariablesListASubSet(main_set_model_part: Kratos.ModelPart, sub_set_model_part: Kratos.ModelPart) -> bool:
    """IsSolutionStepVariablesListASubSet(main_set_model_part: Kratos.ModelPart, sub_set_model_part: Kratos.ModelPart) -> bool"""
@overload
def IsVariableExistsInAllContainerProperties(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: Kratos.DataCommunicator) -> bool:
    """IsVariableExistsInAllContainerProperties(*args, **kwargs)
    Overloaded function.

    1. IsVariableExistsInAllContainerProperties(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: Kratos.DataCommunicator) -> bool

    2. IsVariableExistsInAllContainerProperties(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: Kratos.DataCommunicator) -> bool

    3. IsVariableExistsInAllContainerProperties(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: Kratos.DataCommunicator) -> bool

    4. IsVariableExistsInAllContainerProperties(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: Kratos.DataCommunicator) -> bool
    """
@overload
def IsVariableExistsInAllContainerProperties(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: Kratos.DataCommunicator) -> bool:
    """IsVariableExistsInAllContainerProperties(*args, **kwargs)
    Overloaded function.

    1. IsVariableExistsInAllContainerProperties(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: Kratos.DataCommunicator) -> bool

    2. IsVariableExistsInAllContainerProperties(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: Kratos.DataCommunicator) -> bool

    3. IsVariableExistsInAllContainerProperties(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: Kratos.DataCommunicator) -> bool

    4. IsVariableExistsInAllContainerProperties(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: Kratos.DataCommunicator) -> bool
    """
@overload
def IsVariableExistsInAllContainerProperties(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: Kratos.DataCommunicator) -> bool:
    """IsVariableExistsInAllContainerProperties(*args, **kwargs)
    Overloaded function.

    1. IsVariableExistsInAllContainerProperties(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: Kratos.DataCommunicator) -> bool

    2. IsVariableExistsInAllContainerProperties(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: Kratos.DataCommunicator) -> bool

    3. IsVariableExistsInAllContainerProperties(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: Kratos.DataCommunicator) -> bool

    4. IsVariableExistsInAllContainerProperties(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: Kratos.DataCommunicator) -> bool
    """
@overload
def IsVariableExistsInAllContainerProperties(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: Kratos.DataCommunicator) -> bool:
    """IsVariableExistsInAllContainerProperties(*args, **kwargs)
    Overloaded function.

    1. IsVariableExistsInAllContainerProperties(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: Kratos.DataCommunicator) -> bool

    2. IsVariableExistsInAllContainerProperties(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: Kratos.DataCommunicator) -> bool

    3. IsVariableExistsInAllContainerProperties(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: Kratos.DataCommunicator) -> bool

    4. IsVariableExistsInAllContainerProperties(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: Kratos.DataCommunicator) -> bool
    """
@overload
def IsVariableExistsInAtLeastOneContainerProperties(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: Kratos.DataCommunicator) -> bool:
    """IsVariableExistsInAtLeastOneContainerProperties(*args, **kwargs)
    Overloaded function.

    1. IsVariableExistsInAtLeastOneContainerProperties(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: Kratos.DataCommunicator) -> bool

    2. IsVariableExistsInAtLeastOneContainerProperties(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: Kratos.DataCommunicator) -> bool

    3. IsVariableExistsInAtLeastOneContainerProperties(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: Kratos.DataCommunicator) -> bool

    4. IsVariableExistsInAtLeastOneContainerProperties(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: Kratos.DataCommunicator) -> bool
    """
@overload
def IsVariableExistsInAtLeastOneContainerProperties(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: Kratos.DataCommunicator) -> bool:
    """IsVariableExistsInAtLeastOneContainerProperties(*args, **kwargs)
    Overloaded function.

    1. IsVariableExistsInAtLeastOneContainerProperties(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: Kratos.DataCommunicator) -> bool

    2. IsVariableExistsInAtLeastOneContainerProperties(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: Kratos.DataCommunicator) -> bool

    3. IsVariableExistsInAtLeastOneContainerProperties(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: Kratos.DataCommunicator) -> bool

    4. IsVariableExistsInAtLeastOneContainerProperties(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: Kratos.DataCommunicator) -> bool
    """
@overload
def IsVariableExistsInAtLeastOneContainerProperties(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: Kratos.DataCommunicator) -> bool:
    """IsVariableExistsInAtLeastOneContainerProperties(*args, **kwargs)
    Overloaded function.

    1. IsVariableExistsInAtLeastOneContainerProperties(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: Kratos.DataCommunicator) -> bool

    2. IsVariableExistsInAtLeastOneContainerProperties(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: Kratos.DataCommunicator) -> bool

    3. IsVariableExistsInAtLeastOneContainerProperties(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: Kratos.DataCommunicator) -> bool

    4. IsVariableExistsInAtLeastOneContainerProperties(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: Kratos.DataCommunicator) -> bool
    """
@overload
def IsVariableExistsInAtLeastOneContainerProperties(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: Kratos.DataCommunicator) -> bool:
    """IsVariableExistsInAtLeastOneContainerProperties(*args, **kwargs)
    Overloaded function.

    1. IsVariableExistsInAtLeastOneContainerProperties(arg0: Kratos.ConditionsArray, arg1: Kratos.DoubleVariable, arg2: Kratos.DataCommunicator) -> bool

    2. IsVariableExistsInAtLeastOneContainerProperties(arg0: Kratos.ElementsArray, arg1: Kratos.DoubleVariable, arg2: Kratos.DataCommunicator) -> bool

    3. IsVariableExistsInAtLeastOneContainerProperties(arg0: Kratos.ConditionsArray, arg1: Kratos.Array1DVariable3, arg2: Kratos.DataCommunicator) -> bool

    4. IsVariableExistsInAtLeastOneContainerProperties(arg0: Kratos.ElementsArray, arg1: Kratos.Array1DVariable3, arg2: Kratos.DataCommunicator) -> bool
    """
def SetSolutionStepVariablesList(destination_model_part: Kratos.ModelPart, origin_model_part: Kratos.ModelPart) -> None:
    """SetSolutionStepVariablesList(destination_model_part: Kratos.ModelPart, origin_model_part: Kratos.ModelPart) -> None"""
@overload
def UpdatePropertiesVariableWithRootValueRecursively(container: Kratos.ConditionsArray, variable: Kratos.DoubleVariable) -> None:
    """UpdatePropertiesVariableWithRootValueRecursively(*args, **kwargs)
    Overloaded function.

    1. UpdatePropertiesVariableWithRootValueRecursively(container: Kratos.ConditionsArray, variable: Kratos.DoubleVariable) -> None

    2. UpdatePropertiesVariableWithRootValueRecursively(container: Kratos.ElementsArray, variable: Kratos.DoubleVariable) -> None
    """
@overload
def UpdatePropertiesVariableWithRootValueRecursively(container: Kratos.ElementsArray, variable: Kratos.DoubleVariable) -> None:
    """UpdatePropertiesVariableWithRootValueRecursively(*args, **kwargs)
    Overloaded function.

    1. UpdatePropertiesVariableWithRootValueRecursively(container: Kratos.ConditionsArray, variable: Kratos.DoubleVariable) -> None

    2. UpdatePropertiesVariableWithRootValueRecursively(container: Kratos.ElementsArray, variable: Kratos.DoubleVariable) -> None
    """
