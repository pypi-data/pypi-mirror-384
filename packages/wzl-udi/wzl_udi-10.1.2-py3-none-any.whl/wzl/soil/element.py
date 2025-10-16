import os
import re
from abc import abstractmethod, ABC
from typing import Any, Dict, List

import rdflib

from .error import ChildNotFoundException
from .semantics import Namespaces, Semantics
from ..utils.constants import BASE_UUID_PATTERN, HTTP_GET
from ..utils.error import SerialisationException
from ..utils.resources import ResourceType


class Element(ABC):
    """Base class of all SOIL elements.



    """
    UUID_PATTERN = re.compile(BASE_UUID_PATTERN)

    def __init__(self, uuid: str, name: str, description: str, ontology: str = None, profile: str = None):
        if not isinstance(name, str) or name == '':
            raise Exception('{}: Name is no string or the empty string!'.format(uuid))
        if not isinstance(description, str) or description == '':
            raise Exception('{}: Description is no string or the empty string!'.format(uuid))
        if ontology is not None and not isinstance(ontology, str):
            raise Exception('{}: Onthology is no string!'.format(uuid))
        if profile is not None and not isinstance(profile, str):
            raise Exception('{}: Shape is no string!'.format(uuid))
        if not isinstance(uuid, str) or not Element.UUID_PATTERN.match(uuid):
            raise Exception('Cannot use uuid {}. Wrong format!'.format(uuid))
        else:
            self._uuid: str = uuid
        self._name: str = name
        self._description: str = description
        self._ontology: str = ontology
        self._profilename: str = profile
        self._metadata_profile: rdflib.Graph = None
        self._metadata: rdflib.Graph = None
        self._semantic_name: str = None

    @property
    def uuid(self):
        return self._uuid

    def __getitem__(self, item: str, method: int = HTTP_GET) -> Any:
        if item == "uuid":
            return self._uuid
        if item == "name":
            return self._name
        if item == "description":
            return self._description
        if item == "ontology":
            return self._ontology
        if item == "profile":
            return self._profilename
        raise KeyError("{}: Key error. No attribute is named '{}'".format(self.uuid, item))

    def __setitem__(self, key: str, value: Any):
        if key == "name":
            if not isinstance(value, str) or value == '':
                raise Exception('{}: Name is no string or the empty string!'.format(self.uuid))
            self._name = value
        elif key == "description":
            if not isinstance(value, str) or value == '':
                raise Exception('{}: Description is no string or the empty string!'.format(self.uuid))
            self._description = value
        elif key == "ontology":
            if value is not None and not isinstance(value, str):
                raise Exception('{}: Ontology is no string!'.format(self.uuid))
            self._ontology = value
        elif key == "profile":
            if value is not None and not isinstance(value, str):
                raise Exception('{}: Profile is no string!'.format(self.uuid))
            self._profilename = value
        else:
            raise KeyError(
                "{}: Key error. No attribute is named '{}' or it should not be changed".format(self.uuid, key))

    def serialize(self, keys: List[str], legacy_mode: bool, method: int = HTTP_GET) -> Dict:
        res = {'uuid': self._uuid}
        for key in keys:
            res[key] = self.__getitem__(key, method)
        if not keys:  # list is empty => serialize complete component
            res['name'] = self._name
            res['description'] = self._description
            res['ontology'] = self._ontology
            res['profile'] = self._profilename
        return res

    @staticmethod
    @abstractmethod
    def deserialize(dictionary: Dict):
        ...

    def load_semantics(self, profiles_path: str, metadata_path: str, parent_name: str) -> None:
        if self._profilename is None:
            raise SerialisationException("Can not load semantic definition, shape attribute is not defined!")

        # load shapes
        shape_filename = os.path.join(profiles_path, f"{self._profilename}.shacl.ttl")
        self._metadata_profile = rdflib.Graph()
        self._metadata_profile.parse(shape_filename)
        self._metadata_profile.add((rdflib.URIRef(Semantics.namespace[f'{self._profilename}Profile']), Namespaces.dcterms.license,
                                    Semantics.profile_license))

        # load metadata
        self._semantic_name = f'{parent_name}{self.uuid[4:].capitalize()}'
        metadata_filename = os.path.join(metadata_path, f"{self._semantic_name}.ttl")
        self._metadata = rdflib.Graph()
        self._metadata.parse(metadata_filename)
        self._metadata.add((rdflib.URIRef(self.semantic_name), Namespaces.schema.license, Semantics.metadata_license))

    @abstractmethod
    def serialize_semantics(self, resource_type: ResourceType, recursive: bool = False) -> rdflib.Graph:
        ...

    def resolve_semantic_path(self, suffix: str) -> ('Element', ResourceType):
        if suffix == self.semantic_name.split('/')[-1]:
            return self, ResourceType.metadata

        raise ChildNotFoundException('Could not resolve the semantic path.')

    @property
    @abstractmethod
    def semantic_name(self) -> str:
        ...
