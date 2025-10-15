import json
from dataclasses import asdict

from ..common.unmeshed_constants import StepType, StepStatus, ProcessType, ProcessStatus, ProcessTriggerType


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (StepType, StepStatus, ProcessType, ProcessStatus, ProcessTriggerType)):
            return o.name  # Serialize enums as their names
        return super().default(o)

class JSONSerializable:
    def to_json(self):
        # noinspection PyTypeChecker,PyDataclass
        return json.dumps(asdict(self), indent=2, cls=CustomJSONEncoder)

    @classmethod
    def from_json(cls, json_str: str):
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict):
        # noinspection PyArgumentList
        return cls(**data)
