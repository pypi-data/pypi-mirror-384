import json
from actionstreamer.Model.PatchOperation import PatchOperation
from actionstreamer.Model import PatchOperation


def add_patch_operation(operations: list, field_name: str, value: str | int) -> list:
    operations.append(PatchOperation(field_name=field_name, value=value))


def generate_patch_json(operations: list) -> str:
    operations_str = [op.to_dict() for op in operations]
    return json.dumps(operations_str)