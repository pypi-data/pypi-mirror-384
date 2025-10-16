import datetime
import inspect
import json
from typing import Any, Dict, List, Union, Callable

import rdflib

from .element import Element
from .error import InvokationException, NotImplementedException, ChildNotFoundException
from .semantics import Namespaces
from .variable import Variable, serialize_time
from .parameter import Parameter
from ..utils import root_logger
from ..utils.constants import HTTP_GET, HTTP_OPTIONS
from ..utils.error import SerialisationException, DeviceException
from ..utils.resources import ResourceType

logger = root_logger.get(__name__)


class Function(Element):

    def __init__(self, uuid: str, name: str, description: str, arguments: List[Variable], returns: List[Variable],
                 implementation: Callable, ontology: str = None, profile: str = None):
        Element.__init__(self, uuid, name, description, ontology, profile)
        if uuid[:3] != 'FUN':
            raise Exception('{}: The UUID must start with FUN!'.format(uuid))
        if not isinstance(arguments, list):
            raise Exception('{}: Given arguments are not a list!'.format(uuid))
        for i in arguments:
            if not isinstance(i, Parameter):
                raise Exception('{}: Given argument is not of type Parameter!'.format(uuid))
        if not isinstance(returns, list):
            raise Exception('{}: Given returns are not a list!'.format(uuid))
        for o in returns:
            if not isinstance(o, Parameter):
                raise Exception('{}: Given return is not of type Parameter!'.format(uuid))

        self._arguments = arguments
        self._returns = returns
        self._implementation = implementation
        signature_arguments = {}
        for arg in self._arguments:
            signature_arguments[arg['uuid']] = f'arg_{arg["uuid"][4:].lower()}'
        self._signature = {'arguments': signature_arguments, 'returns': [ret['uuid'] for ret in self._returns]}
        # self._mqtt_callback = implementation['mqtt_callback'] if 'mqtt_callback' in implementation.keys() else None

    @property
    def publishes(self):
        return inspect.isasyncgenfunction(self._implementation) or inspect.isgeneratorfunction(self._implementation)

    def __getitem__(self, item: Union[str, List[str]], method: int = HTTP_GET) -> Any:
        if item == "arguments":
            return self._arguments
        if item == "returns":
            return self._returns
        if isinstance(item, list):
            if len(item) == 0:
                return self
            everything = self._arguments + self._returns
            for o in everything:
                if o.uuid == item[0]:
                    return o[item[1:]]
            raise Exception(
                "{}: Given uuid {} is not the id of a child of the current component!".format(self.uuid, item))
        return super().__getitem__(item, method)

    def __setitem__(self, key: str, value: Any):
        if key == "arguments":
            if not isinstance(value, list):
                raise Exception('{}: Given arguments are not a list!'.format(self.uuid))
            if len(value) != len(self._arguments):
                raise Exception(
                    '{}: The number of given arguments does not match the number of required arguments!'.format(
                        self.uuid))
            for v in value:
                if not isinstance(v, Variable):
                    raise Exception('{}: Given argument is not of type Figure!'.format(self.uuid))
            self._arguments = value
        elif key == "returns":
            if not isinstance(value, list):
                raise Exception('{}: Given returns are not a list!'.format(self.uuid))
            if len(value) != len(self._returns):
                raise Exception(
                    '{}: The number of given returns does not match the number of required returns!'.format(self.uuid))
            for v in value:
                if not isinstance(v, Variable):
                    raise Exception('{}: Given return is not of type Figure!'.format(self.uuid))
            self._returns = value
        else:
            super().__setitem__(key, value)

    def _prepare_invocation_result(self, result: Any, legacy_mode: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        returns = {"returns": []}
        if result is not None:
            # if only one element is returned encapsulate result with tuple to make for-loop working
            if len(self._signature['returns']) == 1:
                result = (result,)
            if len(result) != len(self._returns):
                raise InvokationException(self._uuid, self._name,
                                          "Internal Server Error. Function with UUID {} should return {} parameters, but invoked method returned {} values!".format(
                                              self.uuid, len(result), len(self._returns)))

            for value, uuid in zip(result, self._signature['returns']):
                var = [x for x in self._returns if x['uuid'] == uuid]
                if len(var) != 1:
                    raise InvokationException(self._uuid, self._name,
                                              "Internal Server Error. UUID {} of returned parameter does not match!".format(
                                                  uuid))
                else:
                    var = var[0]
                    Variable.check_all(var.datatype, var.dimension, var.range, value)
                    ret = self.__getitem__([uuid]).serialize([], legacy_mode, HTTP_OPTIONS)
                    ret['value'] = value
                    ret['timestamp'] = serialize_time(datetime.datetime.now())
                    returns['returns'] += [ret]
        return returns

    async def invoke_generator(self, arguments: List[Variable], legacy_mode: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        args = {}
        if self._implementation is None:
            raise NotImplementedException(self._uuid, self._name)

        for a in arguments:
            var = self.__getitem__([a["uuid"]])
            Variable.check_all(var.datatype, var.dimension, var.range, a["value"])
            args[self._signature['arguments'][a["uuid"]]] = a["value"]

        try:
            if inspect.isasyncgenfunction(self._implementation):
                generator = self._implementation(**args)
                while True:
                    try:
                        result = await anext(generator)
                        yield self._prepare_invocation_result(result, legacy_mode)
                    except StopAsyncIteration as e:
                        raise e
            else:
                assert inspect.isgeneratorfunction(self._implementation)
                generator = self._implementation(**args)
                while True:
                    try:
                        result = next(generator)
                        yield self._prepare_invocation_result(result, legacy_mode)
                    except StopIteration as e:
                        raise e
        except StopIteration or StopAsyncIteration as e:
            raise StopAsyncIteration()
        except Exception as e:
            raise DeviceException(str(e), predecessor=e)


    async def invoke(self, arguments: List[Variable], legacy_mode: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        args = {}
        if self._implementation is None:
            raise NotImplementedException(self._uuid, self._name)

        for a in arguments:
            var = self.__getitem__([a["uuid"]])
            Variable.check_all(var.datatype, var.dimension, var.range, a["value"])
            args[self._signature['arguments'][a["uuid"]]] = a["value"]

        # set up servers
        try:
            if inspect.iscoroutinefunction(self._implementation):
                result = await self._implementation(**args)
            else:
                result = self._implementation(**args)
        except Exception as e:
            raise DeviceException(str(e), predecessor=e)

        return self._prepare_invocation_result(result, legacy_mode)

    def serialize(self, keys: List[str], legacy_mode: bool, method: int = HTTP_GET) -> Dict[str, Any]:
        if not keys or 'all' in keys:
            keys = ['uuid', 'name', 'description', 'arguments', 'returns', 'ontology', 'profile']
        dictionary = super().serialize(keys, legacy_mode)
        if 'arguments' in keys:
            dictionary['arguments'] = list(
                map(lambda x: x.serialize(
                    ['name', 'uuid', 'description', 'datatype', 'value', 'dimension', 'range', 'ontology', 'profile'], legacy_mode,
                    HTTP_OPTIONS),
                    self._arguments))
        if 'returns' in keys:
            dictionary['returns'] = list(
                map(lambda x: x.serialize(['name', 'uuid', 'description', 'datatype', 'dimension', 'ontology', 'profile'],
                                          legacy_mode, HTTP_OPTIONS), self._returns))
        return dictionary

    @staticmethod
    def deserialize(dictionary: Dict[str, Any], implementation=None) -> 'Function':
        if 'uuid' not in dictionary:
            raise SerialisationException('The function can not be deserialized. UUID is missing!')
        uuid = dictionary['uuid']
        if uuid[:3] != 'FUN':
            raise SerialisationException(
                'The Function can not be deserialized. The UUID must start with FUN, but actually starts with {}!'.format(
                    uuid[:3]))
        if 'name' not in dictionary:
            raise SerialisationException('{}: The function can not be deserialized. Name is missing!'.format(uuid))
        if 'description' not in dictionary:
            raise SerialisationException(
                '{}: The function can not be deserialized. Description is missing!'.format(uuid))
        if 'arguments' not in dictionary:
            raise SerialisationException(
                '{}: The function can not be deserialized. List of arguments is missing!'.format(uuid))
        if 'returns' not in dictionary:
            raise SerialisationException(
                '{}: The function can not be deserialized. List of returns is missing!'.format(uuid))

        try:
            arguments = []
            for arg in dictionary['arguments']:
                arguments += [Parameter.deserialize(arg)]
        except Exception as e:
            raise SerialisationException('{}: An argument of the function can not be deserialized. {}'.format(uuid, e))
        try:
            returns = []
            for ret in dictionary['returns']:
                returns += [Parameter.deserialize(ret)]
        except Exception as e:
            raise SerialisationException('{}: A return of the function can not be deserialized. {}'.format(uuid, e))
        try:
            ontology = dictionary['ontology'] if 'ontology' in dictionary else None
            profile = dictionary['profile'] if 'profile' in dictionary else None
            return Function(dictionary['uuid'], dictionary['name'], dictionary['description'], arguments, returns,
                            implementation, ontology, profile)
        except Exception as e:
            raise SerialisationException('{}: The function can not be deserialized. {}'.format(uuid, e))

    def load_semantics(self, profiles_path: str, metadata_path: str, parent_name: str) -> None:
        super().load_semantics(profiles_path, metadata_path, parent_name)

        for child in self._arguments + self._returns:
            child.load_semantics(profiles_path, metadata_path, f"{parent_name}{self.uuid[4:].capitalize()}")

    def serialize_semantics(self, resource_type: ResourceType, recursive=False) -> rdflib.Graph:
        if resource_type == ResourceType.profile:
            if self._metadata is None:
                raise SerialisationException('No metadata profiles have been provided during initialization.')
            result = self._metadata_profile

        elif resource_type == ResourceType.metadata:
            if self._metadata is None:
                raise SerialisationException('No semantic information have been provided during initialization.')

            result = self._metadata
        else:
            raise DeviceException('The provided kind of semantic information cannot be returned.')

        if recursive:
            for child in self._arguments + self._returns:
                result += child.serialize_semantics(resource_type, recursive)

        return result

    def resolve_semantic_path(self, suffix: str) -> (Element, ResourceType):
        try:
            return super().resolve_semantic_path(suffix)
        except ChildNotFoundException:
            # check if the path fits one of the components children
            for child in self._arguments + self._returns:
                try:
                    return child.resolve_semantic_path(suffix)
                except ChildNotFoundException:
                    continue

            raise ChildNotFoundException('Could not resolve the semantic path.')

    @property
    def semantic_name(self) -> str:
        if self._metadata is None:
            return ""
        subject = next(
            self._metadata.subjects(predicate=Namespaces.rdf.type, object=Namespaces.sosa.Procedure))
        return subject.toPython()
