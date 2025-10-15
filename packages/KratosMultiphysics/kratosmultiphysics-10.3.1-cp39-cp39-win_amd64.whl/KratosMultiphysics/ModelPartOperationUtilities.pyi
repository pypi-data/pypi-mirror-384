import Kratos

def CheckValidityOfModelPartsForOperations(main_model_part: Kratos.ModelPart, list_of_checking_model_parts: list[Kratos.ModelPart], thow_error: bool) -> bool:
    """CheckValidityOfModelPartsForOperations(main_model_part: Kratos.ModelPart, list_of_checking_model_parts: list[Kratos.ModelPart], thow_error: bool) -> bool"""
def HasIntersection(model_parts_to_intersect: list[Kratos.ModelPart]) -> bool:
    """HasIntersection(model_parts_to_intersect: list[Kratos.ModelPart]) -> bool"""
def Intersect(output_sub_model_part: Kratos.ModelPart, main_model_part: Kratos.ModelPart, model_parts_to_intersect: list[Kratos.ModelPart], add_neighbours: bool) -> None:
    """Intersect(output_sub_model_part: Kratos.ModelPart, main_model_part: Kratos.ModelPart, model_parts_to_intersect: list[Kratos.ModelPart], add_neighbours: bool) -> None"""
def Substract(output_sub_model_part: Kratos.ModelPart, main_model_part: Kratos.ModelPart, model_parts_to_substract: list[Kratos.ModelPart], add_neighbours: bool) -> None:
    """Substract(output_sub_model_part: Kratos.ModelPart, main_model_part: Kratos.ModelPart, model_parts_to_substract: list[Kratos.ModelPart], add_neighbours: bool) -> None"""
def Union(output_sub_model_part: Kratos.ModelPart, main_model_part: Kratos.ModelPart, model_parts_to_merge: list[Kratos.ModelPart], add_neighbours: bool) -> None:
    """Union(output_sub_model_part: Kratos.ModelPart, main_model_part: Kratos.ModelPart, model_parts_to_merge: list[Kratos.ModelPart], add_neighbours: bool) -> None"""
