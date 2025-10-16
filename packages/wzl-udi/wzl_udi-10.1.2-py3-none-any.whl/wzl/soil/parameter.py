import asyncio
import copy
import inspect
from typing import Dict, Callable, Any, List

import rdflib

from .datatype import Datatype
from .error import ReadOnlyException, NotImplementedException
from .semantics import Semantics, Namespaces
from .variable import Variable
from ..utils import root_logger
from ..utils.constants import HTTP_GET
from ..utils.error import DeviceException, SerialisationException
from ..utils.resources import ResourceType

logger = root_logger.get(__name__)


class Parameter(Variable):

    def __init__(self, uuid: str, name: str, description: str, datatype: Datatype, dimension: List[int], range: List,
                 value: Any, getter: Callable = None, setter: Callable = None, ontology: str = None,
                 profile: str = None):
        Variable.__init__(self, uuid, name, description, datatype, dimension, range, value, getter, ontology, profile)
        if uuid[:3] not in ['PAR', 'ARG', 'RET']:
            raise Exception('{}: The UUID must start with PAR, ARG or RET!'.format(uuid))
        if setter is not None and not callable(setter):
            raise TypeError("{}: The setter of the variable must be callable!".format(uuid))
        self._setter = setter

    def __setitem__(self, key: str, value):
        """
        Setter - Method
        If key is "value" datatype, dimension and range is checked for correctness.
        :param key: sets the value of the attribute with name 'item' to the provided value.
        :param value: value to be set
        """
        if key == "value":
            Variable.check_all(self._datatype, self._dimension, self._range, value)
            # self._timestamp, value = self._implementation()
            try:
                if inspect.iscoroutinefunction(self.set):
                    try:
                        loop = asyncio.get_running_loop()
                    except:
                        loop = asyncio.get_event_loop()
                    loop.run_until_complete(self.set(value))
                    self._value = value
                else:
                    self.set(value)
                    self._value = value
            except Exception as e:
                raise DeviceException(str(e), predecessor=e)
        else:
            super().__setitem__(key, value)

    def __getitem__(self, item: str, method=HTTP_GET):
        """
        Getter-Method.
        According to the given key the method returns the value of the corresponding attribute.
        :param item: name of the attribute. Provided as string without leading underscores.
        :param method: ???
        :return: the value of the attribute indicated by 'item'.
        """
        if item == "constant":
            return self._setter is None and self.uuid[:3] == 'PAR'
        return super().__getitem__(item, method)

    def serialize(self, keys: [str], legacy_mode: bool, method=HTTP_GET):
        """
        Seriealizes an object of type Figure into a JSON-like dictionary.
        :param keys: All attributes given in the "keys" array are serialized.
        :param method: ???
        :return: a dictionary having all "keys" as keys and the values of the corresponding attributes as value.
        """
        # list is empty provide all attributes of the default-serialization
        if not keys:
            keys = ['uuid', 'name', 'description', 'datatype', 'value', 'dimension', 'range', 'constant', 'ontology']
        # get all attribute values
        dictionary = {}
        for key in keys:
            value = self.__getitem__(key, method)
            if key == "datatype":
                dictionary[key] = value.to_string(legacy_mode)
            else:
                dictionary[key] = value
        return dictionary

    @staticmethod
    def deserialize(dictionary: Dict, implementation: Dict = None):
        """
        Takes a JSON-like dictionary, parses it, performs a complete correctness check and returns an object of type Figure with the
         values provided in the dictionary, if dictionary is a valid serialization of a Figure.
        :param dictionary: serialized variable
        :param implementation: implementation wrapper object,
        :return: an object of type Figure
        """
        # check if all required attributes are present
        if 'uuid' not in dictionary:
            raise SerialisationException('The parameter can not be deserialized. UUID is missing!')
        uuid = dictionary['uuid']
        if uuid[:3] not in ['PAR', 'ARG', 'RET']:
            raise SerialisationException(
                'The Parameter can not be deserialized. The UUID must start with PAR, ARG or RET, but actually starts with {}!'.format(
                    uuid[:3]))
        if 'name' not in dictionary:
            raise SerialisationException('{}: The parameter can not be deserialized. Name is missing!'.format(uuid))
        if 'description' not in dictionary:
            raise SerialisationException(
                '{}: The parameter can not be deserialized. Description is missing!'.format(uuid))
        if 'datatype' not in dictionary:
            raise SerialisationException('{}: The parameter can not be deserialized. Datatype is missing!'.format(uuid))
        if 'dimension' not in dictionary:
            raise SerialisationException(
                '{}: The parameter can not be deserialized. Dimension is missing!'.format(uuid))
        if 'value' not in dictionary:
            raise SerialisationException('{}: The parameter can not be deserialized. Value is missing!'.format(uuid))
        if 'range' not in dictionary:
            raise SerialisationException('{}: The parameter can not be deserialized. Range is missing!'.format(uuid))
        try:
            # create Parameter
            getter = implementation['getter'] if implementation is not None else None
            setter = implementation['setter'] if implementation is not None else None
            ontology = dictionary['ontology'] if 'ontology' in dictionary else None
            profile = dictionary['profile'] if 'profile' in dictionary else None
            return Parameter(dictionary['uuid'], dictionary['name'], dictionary['description'],
                             Datatype.from_string(dictionary['datatype']), dictionary['dimension'],
                             dictionary['range'], dictionary['value'], getter, setter, ontology, profile)
        except Exception as e:
            raise SerialisationException('{}: The variable can not be deserialized. {}'.format(uuid, e))

    @property
    def set(self):
        if self._setter is not None:
            return self._setter
        else:
            raise ReadOnlyException(self._uuid, self._name)

    def serialize_semantics(self, resource_type: ResourceType, recursive=False) -> rdflib.Graph:
        if resource_type == ResourceType.profile:
            if self._metadata_profile is None:
                raise SerialisationException('No metadata profiles have been provided during initialization.')
            return self._metadata_profile

        elif resource_type == ResourceType.range:
            range_graph = copy.deepcopy(self._metadata)
            subjects = range_graph.subjects()
            for subject in subjects:
                if subject != Semantics.namespace[f'{self._semantic_name}Range']:
                    range_graph.remove((subject, None, None))
            range_graph.add((Semantics.namespace[f'{self._semantic_name}Range'], Namespaces.schema.license,
                        Semantics.metadata_license))
            return range_graph
        elif resource_type == ResourceType.metadata:
            result = copy.deepcopy(self._metadata)

            triples = list(result.triples((None, Namespaces.qudt['value'], None)))
            if len(triples) > 0:
                assert (len(triples) == 1)
                result.remove(triples[0])

            try:
                rdf_value = self.serialize_value(result, self.__getitem__('value', 0))
                result.add((Semantics.namespace[self._semantic_name], Namespaces.qudt['value'], rdf_value))
                result.add((Semantics.namespace[f'{self._semantic_name}Range'], Namespaces.schema.license,
                            Semantics.metadata_license))
            except DeviceException as e:
                if isinstance(e._predecessor, NotImplementedException):
                    pass
                else:
                    raise e

            return result
        else:
            raise DeviceException('The provided kind of semantic information cannot be returned.')

    @property
    def semantic_name(self) -> str:
        if self._metadata is None:
            return ""
        if self.uuid[:3] == 'PAR':
            subject = next(self._metadata.subjects(predicate=Namespaces.rdf.type, object=Namespaces.ssn.Property))
        elif self.uuid[:3] == 'ARG':
            subject = next(self._metadata.subjects(predicate=Namespaces.rdf.type, object=Namespaces.ssn.Input))
        else:
            assert self.uuid[:3] == 'RET'
            subject = next(self._metadata.subjects(predicate=Namespaces.rdf.type, object=Namespaces.ssn.Output))
        return subject.toPython()
