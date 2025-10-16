import Kratos

def CheckModelPartStatus(model_part: Kratos.ModelPart, status_to_check: str) -> bool:
    """CheckModelPartStatus(model_part: Kratos.ModelPart, status_to_check: str) -> bool"""
def GenerateModelPart(conditions_container: Kratos.ConditionsArray, destination_model_part: Kratos.ModelPart, element_name: str) -> None:
    """GenerateModelPart(conditions_container: Kratos.ConditionsArray, destination_model_part: Kratos.ModelPart, element_name: str) -> None"""
def GetModelPartStatusLog(model_part: Kratos.ModelPart) -> list[str]:
    """GetModelPartStatusLog(model_part: Kratos.ModelPart) -> list[str]"""
def GetModelPartsWithCommonReferenceEntities(examined_model_parts_list: list[Kratos.ModelPart], reference_model_parts: list[Kratos.ModelPart], are_nodes_considered: bool, are_conditions_considered: bool, are_elements_considered: bool, are_parents_considered: bool, echo_level: int = ...) -> list:
    """GetModelPartsWithCommonReferenceEntities(examined_model_parts_list: list[Kratos.ModelPart], reference_model_parts: list[Kratos.ModelPart], are_nodes_considered: bool, are_conditions_considered: bool, are_elements_considered: bool, are_parents_considered: bool, echo_level: int = 0) -> list"""
def LogModelPartStatus(model_part: Kratos.ModelPart, status_to_log: str) -> None:
    """LogModelPartStatus(model_part: Kratos.ModelPart, status_to_log: str) -> None"""
def RemoveModelPartsWithCommonReferenceEntitiesBetweenReferenceListAndExaminedList(model_parts_list: list[Kratos.ModelPart]) -> None:
    """RemoveModelPartsWithCommonReferenceEntitiesBetweenReferenceListAndExaminedList(model_parts_list: list[Kratos.ModelPart]) -> None"""
