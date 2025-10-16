import enum
from typing import List


class ResourceType(enum.Enum):
    element = 0
    profile = 1         # IRI -> <element name>Profile
    metadata = 2        # IRI -> <element name>
    data = 3            # IRI -> <measurement name>MeasurementResult
    range = 4           # IRI -> <parameter/measurement/argument/return name>Range
    observation = 5     # IRI -> <measurement name>Measurement
    uncertainty = 6     # IRI -> <measurement name>MeasurementUncertainty

    def __str__(self) -> str:
        return self.name

    @classmethod
    def from_string(cls, value: str) -> 'ResourceType':
        return cls.__members__[value]

    @classmethod
    @property
    def semantic_resources(cls) -> List[str]:
        return [str(ResourceType.profile), str(ResourceType.metadata), str(ResourceType.data), str(ResourceType.range),
                str(ResourceType.observation), str(ResourceType.uncertainty)]

    def is_semantic(self) -> bool:
        return self.value in range(1, 7)
