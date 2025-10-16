'''Provides the Component class being the structuring element of the UDI, i.e. the underlying SOIL Model.

Components are structural elements of a SOIL-model.
A component contains an arbitrary number of children elements such that the overall model has tree-like shape.
Children elements can be components, functions, parameters or measurements.

'''

# from __future__ import annotations
import json
import os
import sys
from typing import List, Any, Union, Dict

import rdflib

from .element import Element
from .error import ChildNotFoundException
from .function import Function
from .measurement import Measurement
from .parameter import Parameter
from .semantics import Namespaces, Semantics
from ..utils import root_logger
from ..utils.constants import HTTP_GET
from ..utils.error import SerialisationException, DeviceException, UserException
from ..utils.resources import ResourceType

logger = root_logger.get(__name__)


class Component(Element):

    def __init__(self, uuid: str, name: str, description: str, functions: List[Function],
                 measurements: List[Measurement],
                 parameters: List[Parameter], components: List['Component'], implementation: Any, ontology: str = None,
                 profile: str = None):
        """

        Args:
            uuid: Locally unique identifier of the component. Must start with 'COM-'.
                For the sake if simplicity, it is suggested to use the name and simply prepend 'COM-' to obtain the UUID.
            name: Human readable name of the component.
            description: Human readable description of the purpose of the component.
            functions: List of all children functions.
            measurements: List of all children measurements.
            parameters: List of all children parameters.
            components: List of all children components. Might contain dynamic-components.
            implementation: The class of the sensor layer implementing this component.
            ontology: Optional field containing the reference to a semantic definition of the components name or purpose.
            profile: Optional field containing the name of the shape defining the restrictions of this component using semantic web technologies.

        Raises:
            ValueError: The UUID does not start with 'COM'.
            AmbiguousUUIDException: There are at least two children having the same UUID.
            InvalidModelException: One of the lists containing the components' children is not a list or contains elements which are not of the correct type.
            InvalidMappingException: If something is wrong with the provided mapping.
        """
        Element.__init__(self, uuid, name, description, ontology, profile)
        if uuid[:3] != 'COM':
            raise Exception('{}: The UUID must start with COM!'.format(uuid))
        if not isinstance(functions, list):
            raise Exception('{}: Given functions are not a list!'.format(uuid))
        for f in functions:
            if not isinstance(f, Function):
                raise Exception('{}: Given function is not of type Function!'.format(uuid))
        if not isinstance(measurements, list):
            raise Exception('{}: Given measurements are not a list!'.format(uuid))
        for v in measurements:
            if not isinstance(v, Measurement):
                raise Exception('{}: Given measurement is not of type Variables!'.format(uuid))
        if not isinstance(parameters, list):
            raise Exception('{}: Given measurements are not a list!'.format(uuid))
        for p in parameters:
            if not isinstance(p, Parameter):
                raise Exception('{}: Given measurement is not of type Variables!'.format(uuid))
        if not isinstance(components, list):
            raise Exception('{}: Given components are not a list!'.format(uuid))
        for o in components:
            if not isinstance(o, Component):
                raise Exception('{}: Given component is not of type Components!'.format(uuid))

        self._functions = functions
        self._measurements = measurements
        self._components = components
        self._parameters = parameters
        self._implementation = implementation
        self._profile_path: str = None

    @property
    def children(self) -> List[Element]:
        return self._functions + self._measurements + self._components + self._parameters

    def __getitem__(self, item: Union[str, List[str]], method: int = HTTP_GET) -> Any:
        """Returns the value of the specified item.

        Args:
            item: Either a string or a list of uuids. Possible string
            values are 'functions', 'measurements', 'parameters', 'components'
            and 'children'. The returned value is the list of the specified
            elements.
            If a list of UUIDs is given, the __getitem__ method of the child of
            which its UUID is equal to first UUID in the list is called with
            item[1:].

            method:

        Returns: Either a list of (specific) children or, if a list of UUIDs is
        given, an Element.

        Raises
            ChildNotFoundException: The child identified by the list of uuids could not been found.
        """

        if item == 'functions':
            return self._functions
        if item == 'measurements':
            return self._measurements
        if item == 'parameters':
            return self._measurements
        if item == 'components':
            return self._components
        if item == 'children':
            ret = []
            everything = self._components + self._measurements + self._parameters + self._functions
            for o in everything:
                ret += [o.uuid]
            return ret
        # if the item is a list, the list contains the uuid of the descendants
        if isinstance(item, list):
            if len(item) > 0 and super().__getitem__('uuid', method) == item[0]:
                item = item[1:]
            if len(item) == 0:
                return self
            everything = self._components + self._measurements + self._parameters + self._functions
            for child in everything:
                if child.uuid == item[0]:
                    if len(item) == 1:
                        return child
                    else:
                        return child.__getitem__(item[1:], method)
            raise ChildNotFoundException(
                f'{self.uuid}: Given uuid {item} is not the id of a child of the current component!')
        return super().__getitem__(item, method)

    def __setitem__(self, key: str, value: Any):
        if key == 'functions':
            if not isinstance(value, list):
                raise Exception('{}: Given functions are not a list!'.format(self.uuid))
            for f in value:
                if not isinstance(f, Function):
                    raise Exception('{}: Given function is not of type Function!'.format(self.uuid))
            self._functions = value
        elif key == 'measurements':
            if not isinstance(value, list):
                raise Exception('{}: Given measurements are not a list!'.format(self.uuid))
            for v in value:
                if not isinstance(v, Measurement):
                    raise Exception('{}: Given measurement is not of type Variable!'.format(self.uuid))
            self._measurements = value
        elif key == 'parameters':
            if not isinstance(value, list):
                raise Exception('{}: Given parameters are not a list!'.format(self.uuid))
            for v in value:
                if not isinstance(v, Parameter):
                    raise Exception('{}: Given parameter is not of type Parameter!'.format(self.uuid))
            self._measurements = value
        elif key == 'components':
            if not isinstance(value, list):
                raise Exception('{}: Given components are not a list!'.format(self.uuid))
            for o in value:
                if not isinstance(o, Component):
                    raise Exception('{}: Given component is not of type Component!'.format(self.uuid))
            self._components = value
        else:
            super().__setitem__(key, value)

    def serialize(self, keys: List[Any] = None, legacy_mode: bool = False, method: int = HTTP_GET) -> Dict[str, Any]:
        """Serializes the component and all of it's data to a dictionary.

        Calls the serialize method from all children recursively.
        Which attributes and data of the component are serialized can be specified by giving a list of keys.

        Args:
            keys: Determines which data is serialized. Possible keys are "uuid", "name", "description", "children", "ontology" and "all".
                If no list, an empty list or "all" is given, the data of all attributes is serialized, i.e., it's equivelent to setting all keys.
            method: Specifies which HTTP method has been used to query the data. Possible values are HTTP_GET (=0) or HTTP_OPTIONS (=1). Only relevant if the children are serialized, to0.

        Returns:
            A dictionary containing the serialized data of the component.
        """
        keys = [] if keys is None else keys

        if not keys:  # list is empty
            keys = ['uuid', 'name', 'description', 'children', 'ontology', 'profile']

        if 'all' in keys:  # serialize complete tree recursively (overrides all other keys)
            dictionary = super().serialize([], legacy_mode)
            dictionary['measurements'] = list(map(lambda x: x.serialize([], legacy_mode), self._measurements))
            dictionary['functions'] = list(map(lambda x: x.serialize(['all'], legacy_mode), self._functions))
            dictionary['components'] = list(map(lambda x: x.serialize(['all'], legacy_mode), self._components))
            dictionary['parameters'] = list(map(lambda x: x.serialize([], legacy_mode), self._parameters))
            return dictionary

        dictionary = super().serialize(keys, legacy_mode, method)
        if 'children' in keys:
            everything = self._components + self._measurements + self._parameters + self._functions
            dictionary['children'] = list(map(lambda x: x.serialize(['name', 'uuid'], legacy_mode), everything))
        return dictionary

    @staticmethod
    def deserialize(dictionary, implementation=None):
        if 'uuid' not in dictionary:
            raise SerialisationException('The component can not be deserialized. UUID is missing!')
        uuid = dictionary['uuid']
        if uuid[:3] != 'COM':
            raise SerialisationException(
                'The component can not be deserialized. The UUID must start with COM, but actually starts with {}!'.format(
                    uuid[:3]))
        if 'name' not in dictionary:
            raise SerialisationException('{}: The component can not be deserialized. Name is missing!'.format(uuid))
        if 'description' not in dictionary:
            raise SerialisationException(
                '{}: The component can not be deserialized. Description is missing!'.format(uuid))
        if 'measurements' not in dictionary:
            raise SerialisationException(
                '{}: The component can not be deserialized. List of measurements is missing!'.format(uuid))
        if 'parameters' not in dictionary:
            raise SerialisationException(
                '{}: The component can not be deserialized. List of parameters is missing!'.format(uuid))
        if 'functions' not in dictionary:
            raise SerialisationException(
                '{}: The component can not be deserialized. List of functions is missing!'.format(uuid))
        if 'components' not in dictionary:
            raise SerialisationException(
                '{}: The component can not be deserialized. List of components is missing!'.format(uuid))

        try:
            measurements = []
            for var in dictionary['measurements']:
                if implementation is not None:
                    getter = getattr(implementation, f'get_mea_{var["uuid"][4:].lower()}')
                    measurements += [Measurement.deserialize(var, getter)]
                else:
                    measurements += [Measurement.deserialize(var)]
        except Exception as e:
            raise SerialisationException(
                '{}: A measurement of the component can not be deserialized. {}'.format(uuid, e))
        try:
            parameters = []
            for par in dictionary['parameters']:
                if implementation is not None:
                    getter = getattr(implementation, f'get_par_{par["uuid"][4:].lower()}')
                    setter = None if par['constant'] else getattr(implementation, f'set_par_{par["uuid"][4:].lower()}')
                    parameters += [Parameter.deserialize(par, {'getter': getter, 'setter': setter})]
                else:
                    parameters += [Parameter.deserialize(par)]
        except Exception as e:
            raise SerialisationException('{}: A parameter of the component can not be deserialized. {}'.format(uuid, e))
        try:
            functions = []
            for func in dictionary['functions']:
                if implementation is not None:
                    method = getattr(implementation, f'fun_{func["uuid"][4:].lower()}')
                    functions += [Function.deserialize(func, method)]
                else:
                    functions += [Function.deserialize(func)]
        except Exception as e:
            raise SerialisationException('{}: A function of the component can not be deserialized. {}'.format(uuid, e))
        try:
            components = []
            for obj in dictionary['components']:
                if implementation is not None:
                    child_implementation = None
                    attributes = list(filter(lambda attr: attr[:5] == '_com_', dir(implementation)))
                    if f'_com_{obj["uuid"][4:].lower()}' in attributes and not isinstance(
                            getattr(implementation, f'_com_{obj["uuid"][4:].lower()}'), dict):
                        child_implementation = getattr(implementation, f'_com_{obj["uuid"][4:].lower()}')
                    else:
                        for attr in attributes:
                            attribute = getattr(implementation, attr)
                            if isinstance(attribute, dict) and obj['uuid'] in attribute:
                                child_implementation = attribute[obj['uuid']]
                                break
                    components += [Component.deserialize(obj, child_implementation)]
                else:
                    components += [Component.deserialize(obj)]
        except Exception as e:
            raise SerialisationException(
                '{}: An component of the component can not be deserialized. {}'.format(uuid, e))
        try:
            ontology = dictionary['ontology'] if 'ontology' in dictionary else None
            profile = dictionary['profile'] if 'profile' in dictionary else None
            return Component(dictionary['uuid'], dictionary['name'], dictionary['description'], functions, measurements,
                             parameters, components, implementation, ontology, profile)
        except Exception as e:
            raise SerialisationException('{}: The component can not be deserialized. {}'.format(uuid, e))

    def write(self, filename: str):
        """Serializes the component (including all data) and stores the result in the JSON format in a file with the given name.

        Args:
            filename: Absolute or relative path (incl. filename) to a JSON file, in which the serialized component should be stored.
                File ending must be ".json".

        Raises:
            Exception: If the file ending is not ".json"
        """
        if filename[-5:] != '.json':
            raise Exception('{} is not a json file!'.format(filename))

        model_dict = self.serialize(['all'])

        f = open(filename, 'w')
        f.write(json.dumps(model_dict))
        f.close()

    def update(self, element: Union['Component', Function, Measurement, Parameter]):
        if isinstance(element, Component):
            for i, o in enumerate(self._components):
                if o.uuid == element.uuid:
                    self._components[i] = element
                    return
            # self._components.append(element)
        else:
            raise Exception('Wrong type updating element on existing model!')

    def add(self, uuid: str, class_name: str, data: Dict, *args, **kwargs):
        if uuid[:3] == 'COM':
            if uuid not in [o.uuid for o in self._components]:
                if uuid == data['uuid']:
                    try:
                        module_name = f'{class_name[:3].lower()}_{class_name[3:].lower()}'
                        try:
                            __import__(module_name)
                            implementation = getattr(sys.modules[module_name], class_name)(self._implementation._device,
                                                                                           *args, **kwargs)
                        except (AttributeError, ModuleNotFoundError) as e:
                            module_name = f'hwc.{module_name}'
                            __import__(module_name)
                            implementation = getattr(sys.modules[module_name], class_name)(self._implementation._device,
                                                                                           *args, **kwargs)
                        self._components += [Component.load(data, implementation)]
                        getattr(self._implementation, 'add')(uuid, implementation)
                        return implementation
                    except Exception as e:
                        raise DeviceException('Can not add component with UUID {}. {}'.format(uuid, e), predecessor=e)
                else:
                    raise UserException(
                        'The UUID of the component given in the model file ({}) does not match UUID in the requested URL ({}).'.format(
                            data['uuid'], uuid))
            else:
                raise UserException('Component has already a child with UUID {}.'.format(uuid))
        else:
            raise UserException('UUID {} is not of the UUID of an component.'.format(uuid))

    def remove(self, uuid: str) -> str:
        for o in self._components:
            if o.uuid == uuid:
                try:
                    getattr(self._implementation, 'remove')(uuid)
                except Exception as e:
                    raise DeviceException(str(e), predecessor=e)
                self._components.remove(o)
                return o.__class__.__name__
        raise ChildNotFoundException('{}: Child {} not found!'.format(self.uuid, uuid))

    @staticmethod
    def load(file: Union[str, dict], implementation: Any) -> 'Component':
        if isinstance(file, str):
            if not os.path.isfile(file):
                raise Exception('There is no file named {}!'.format(file))
            if file[-5:] != '.json':
                raise Exception('{} is not a json file!'.format(file))
            with open(file, 'r') as f:
                model_dict = json.load(f)
            return Component.deserialize(model_dict, implementation)
        elif isinstance(file, dict):
            return Component.deserialize(file, implementation)
        else:
            raise Exception('Given file is not a name of a json-file nor a json-like dictionary.')

    def load_semantics(self, profiles_path: str, metadata_path: str, parent_name: str) -> None:
        super().load_semantics(profiles_path, metadata_path, parent_name)
        self._profile_path = profiles_path

        for child in self.children:
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
            for child in self.children:
                result += child.serialize_semantics(resource_type, recursive)

        return result

    def _is_semantic_path_of_base_profile(self, profile: rdflib.Graph, suffix: str) -> bool:
        imported_profiles = list(profile.objects(predicate=Namespaces.owl.imports))
        for imported_profile in imported_profiles:
            if Semantics.namespace not in imported_profile:
                continue
            imported_profile_name = imported_profile.toPython().replace(Semantics.namespace, '')
            if imported_profile_name == suffix:
                return True
            else:
                base_shape_filename = os.path.join(self._profile_path, f'{imported_profile_name.replace("Shape", "")}.shacl.ttl')
                base_graph = rdflib.Graph().parse(base_shape_filename)
                if self._is_semantic_path_of_base_profile(base_graph, suffix):
                    return True
        return False

    def resolve_semantic_path(self, suffix: str) -> (Element, ResourceType):
        try:
            return super().resolve_semantic_path(suffix)
        except ChildNotFoundException:
            # check if the path fits one of the components children
            for child in self.children:
                try:
                    return child.resolve_semantic_path(suffix)
                except ChildNotFoundException:
                    continue

            raise ChildNotFoundException('Could not resolve the semantic path.')

    @property
    def semantic_name(self) -> str:
        if self._metadata is None:
            return ""
        subject = next(self._metadata.subjects(predicate=Namespaces.rdf.type, object=Namespaces.ssn.System))
        return subject.toPython()
