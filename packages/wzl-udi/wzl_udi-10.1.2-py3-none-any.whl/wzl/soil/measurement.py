import asyncio
import copy
import datetime
import inspect
import warnings
from typing import Dict, Callable, List

import rdflib
from deprecated import deprecated

from .datatype import Datatype
from .error import ChildNotFoundException
from .variable import Variable, serialize_time
from .semantics import Semantics, Namespaces
from ..utils import root_logger
from ..utils.constants import HTTP_GET, HTTP_OPTIONS
from ..utils.error import SerialisationException, DeviceException
from ..utils.resources import ResourceType

logger = root_logger.get(__name__)


class Measurement(Variable):

    def __init__(self, uuid: str, name: str, description: str, datatype: Datatype, dimension: List[int], range: List,
                 getter: Callable, unit: str, label=None, ontology: str = None, profile: str = None):
        Variable.__init__(self, uuid, name, description, datatype, dimension, range, None, getter, ontology, profile)
        if uuid[:3] != 'MEA':
            raise Exception('{}: The UUID must start with MEA!'.format(uuid))
        self._unit = unit
        self._covariance = None
        # self._uncertainty = None
        self._timestamp = None
        self._label = label

    @property
    def unit(self):
        return self._unit

    @property
    def covariance(self):
        return self._covariance

    # @property
    # def uncertainty(self):
    #     return self._uncertainty

    @property
    def timestamp(self):
        return self._timestamp

    @property
    @deprecated(version='6.3.0',
                reason='"Nonce" has been renamed to "label".')
    def nonce(self):
        return self._label

    @property
    def label(self):
        return self._label

    def __getitem__(self, item: str, method=HTTP_GET):
        """
        Getter-Method.
        According to the given key the method returns the value of the corresponding attribute.
        :param item: name of the attribute. Provided as string without leading underscores.
        :param method: ???
        :return: the value of the attribute indicated by 'item'.
        """
        if item == "unit":
            return self._unit
        if item == 'nonce':
            warnings.warn(
                'Usage of the keyword "nonce" is deprecated and will be removed in future versions. Use "label" instead.',
                DeprecationWarning)
            return self._label
        if item == 'label':
            return self._label
        if item == "value":
            if method != HTTP_OPTIONS:
                try:
                    if inspect.iscoroutinefunction(self.get):
                        loop = asyncio.get_event_loop()
                        value, covariance = loop.run_until_complete(asyncio.gather(self.get()))[0]
                    else:
                        value, covariance = self.get()

                    if self._datatype == Datatype.TIME:
                        value = serialize_time(value)
                        if covariance is not None:
                            covariance = serialize_time(value)
                    elif self._datatype == Datatype.ENUM:
                        value = str(value)

                except Exception as e:
                    raise DeviceException(
                        'Could not provide value of Measurement/Parameter {}: {}'.format(self.uuid, str(e)),
                        predecessor=e)

                Variable.check_all(self._datatype, self._dimension, self._range, value)
                self._value = value
                self._covariance = covariance
                return value
            else:
                return self._value
        if item == 'covariance':
            return self._covariance
        # if item == 'uncertainty':
        #     return self._uncertainty
        if item == 'timestamp':
            return self._timestamp
        if item == []:
            return self
        return super().__getitem__(item, method)

    def __setitem__(self, key: str, value):
        """
        Setter - Method
        If key is "value" datatype, dimension and range is checked for correctness.
        :param key: sets the value of the attribute with name 'item' to the provided value.
        :param value: value to be set
        """
        if key in ['value', 'timestamp', 'covariance']:
            raise KeyError('The {} attribute of a measurement can not be set manually!'.format(key))
        elif key == "nonce":
            warnings.warn(
                'Usage of the keyword "nonce" is deprecated and will be removed in future versions. Use "label" instead.',
                DeprecationWarning)
            self._label = self._label
        elif key == "label":
            self._label = self._label
        elif key == 'unit':
            self._unit = self._unit
        else:
            super().__setitem__(key, value)

    def serialize(self, keys: [str], legacy_mode: bool, method=HTTP_GET):
        """
        Serializes an object of type Measurement into a JSON-like dictionary.
        :param keys: All attributes given in the "keys" array are serialized.
        :param method: ???
        :return: a dictionary having all "keys" as keys and the values of the corresponding attributes as value.
        """
        # list is empty provide all attributes of the default-serialization
        if not keys:
            keys = ['uuid', 'name', 'description', 'datatype', 'value', 'dimension', 'range', 'timestamp', 'label',
                    'covariance', 'unit']  # , 'ontology']
        if 'value' in keys and 'timestamp' not in keys:
            keys += ['timestamp']
        dictionary = {}
        # get all attribute values
        for key in keys:
            value = self.__getitem__(key, method)
            # in case of timestamp convert into RFC3339 string
            if key == 'timestamp':
                value = value.isoformat() + 'Z' if value is not None else datetime.datetime.now(
                    datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
            if key == 'value' and self._datatype == 'time':
                value = value.isoformat() + 'Z' if value is not None else ""
            if key == "datatype":
                dictionary[key] = value.to_string(legacy_mode)
            else:
                dictionary[key] = value

        return dictionary

    @staticmethod
    def deserialize(dictionary: Dict, implementation=None):
        """
        Takes a JSON-like dictionary, parses it, performs a complete correctness check and returns an object of type Figure with the
         values provided in the dictionary, if dictionary is a valid serialization of a Figure.
        :param dictionary: serialized measurement
        :param implementation: implementation wrapper object,
        :return: an object of type Figure
        """
        # check if all required attributes are present
        if 'uuid' not in dictionary:
            raise SerialisationException('The measurement can not be deserialized. UUID is missing!')
        uuid = dictionary['uuid']
        if uuid[:3] != 'MEA':
            raise SerialisationException(
                'The Measurement can not be deserialized. The UUID must start with MEA, but actually starts with {}!'.format(
                    uuid[:3]))
        if 'name' not in dictionary:
            raise SerialisationException('{}: The measurement can not be deserialized. Name is missing!'.format(uuid))
        if 'description' not in dictionary:
            raise SerialisationException(
                '{}: The measurement can not be deserialized. Description is missing!'.format(uuid))
        if 'datatype' not in dictionary:
            raise SerialisationException(
                '{}: The measurement can not be deserialized. Datatype is missing!'.format(uuid))
        if 'dimension' not in dictionary:
            raise SerialisationException(
                '{}: The measurement can not be deserialized. Dimension is missing!'.format(uuid))
        if 'value' not in dictionary:
            raise SerialisationException('{}: The measurement can not be deserialized. Value is missing!'.format(uuid))
        if 'range' not in dictionary:
            raise SerialisationException('{}: The measurement can not be deserialized. Range is missing!'.format(uuid))
        if 'unit' not in dictionary:
            raise SerialisationException('{}: The measurement can not be deserialized. Unit is missing!'.format(uuid))
        try:
            ontology = dictionary['ontology'] if 'ontology' in dictionary else None
            profile = dictionary['profile'] if 'profile' in dictionary else None
            return Measurement(dictionary['uuid'], dictionary['name'], dictionary['description'],
                               Datatype.from_string(dictionary['datatype']), dictionary['dimension'],
                               dictionary['range'], implementation, dictionary['unit'], None, ontology, profile)
        except Exception as e:
            raise SerialisationException('{}: The measurement can not be deserialized. {}'.format(uuid, e))

    def serialize_semantics(self, resource_type: ResourceType, recursive=False) -> rdflib.Graph:
        if resource_type == ResourceType.profile:
            if self._metadata_profile is None:
                raise SerialisationException('No metadata profiles have been provided during initialization.')
            result = self._metadata_profile

        elif resource_type == ResourceType.metadata:
            result = self._metadata
            result.add((Semantics.namespace[f'{self._semantic_name}Range'], Namespaces.schema.license,
                        Semantics.metadata_license))

        elif resource_type == ResourceType.range:
            result = copy.deepcopy(self._metadata)
            subjects = result.subjects()
            for subject in subjects:
                if subject != Semantics.namespace[f'{self._semantic_name}Range']:
                    result.remove((subject, None, None))
            result.add((Semantics.namespace[f'{self._semantic_name}Range'], Namespaces.schema.license,
                        Semantics.metadata_license))

        elif resource_type == ResourceType.data:
            data_graph = rdflib.Graph()
            data_graph.bind('sosa', Namespaces.sosa)
            data_graph.bind(Semantics.prefix, Semantics.namespace)
            data_graph.bind('soil', Namespaces.soil)
            data_graph.bind('qudt', Namespaces.qudt)
            data_graph.bind('unit', Namespaces.unit)
            data_graph.bind('earl', Namespaces.earl)
            measurement_subject = Semantics.namespace[f'{self._semantic_name}Measurement']
            result_subject = Semantics.namespace[f'{self._semantic_name}MeasurementResult']
            uncertainty_subject = Semantics.namespace[f'{self._semantic_name}MeasurementUncertainty']

            # create result node
            unit_triples = list(self._metadata.triples((None, Namespaces.qudt.applicableUnit, None)))
            assert self.datatype in [Datatype.STRING, Datatype.ENUM, Datatype.BOOLEAN, Datatype.TIME] or len(unit_triples) == 1

            data_graph.add((result_subject, Namespaces.rdf.type, rdflib.URIRef(Namespaces.sosa.Result)))
            data_graph.add((result_subject, Namespaces.sosa.isResultOf, measurement_subject))
            if len(unit_triples) == 1:
                data_graph.add((result_subject, Namespaces.qudt.unit, unit_triples[0][2]))
            data_graph.add((result_subject, Namespaces.schema.license, Semantics.data_license))

            rdf_value = self.serialize_value(data_graph, self.__getitem__('value', 0))
            data_graph.add((result_subject, Namespaces.qudt.value, rdf_value))
            data_graph.add((result_subject, Namespaces.m4i.hasUncertaintyDeclaration, uncertainty_subject))

            data_graph.add((result_subject, Namespaces.schema.dateCreated,
                            rdflib.Literal(datetime.datetime.now().astimezone())))

            result = data_graph

        elif resource_type == ResourceType.uncertainty:
            data_graph = rdflib.Graph()
            data_graph.bind(Semantics.prefix, Semantics.namespace)
            uncertainty_subject = Semantics.namespace[f'{self._semantic_name}MeasurementUncertainty']
            covariance = self.__getitem__('covariance', 0)
            if covariance is not None:
                rdf_covariance = self.serialize_value(data_graph, covariance)
                data_graph.add((uncertainty_subject, Namespaces.rdf.type, Namespaces.si.CoverageInterval))
                data_graph.add((uncertainty_subject, Namespaces.si.hasStandardUnc, rdf_covariance))

            else:
                data_graph.bind('earl', Namespaces.earl)
                data_graph.add((uncertainty_subject, Namespaces.rdf.type, Namespaces.earl.NotApplicable))

            data_graph.add((uncertainty_subject, Namespaces.schema.license, Semantics.metadata_license))
            result = data_graph

        elif resource_type == ResourceType.observation:
            data_graph = rdflib.Graph()
            data_graph.bind('sosa', Namespaces.sosa)
            data_graph.bind(Semantics.prefix, Semantics.namespace)
            data_graph.bind('soil', Namespaces.soil)
            data_graph.bind('qudt', Namespaces.qudt)
            data_graph.bind('unit', Namespaces.unit)
            measurement_subject = Semantics.namespace[f'{self._semantic_name}Measurement']
            result_subject = Semantics.namespace[f'{self._semantic_name}MeasurementResult']

            sensor_triples = list(self._metadata.triples((None, Namespaces.sosa.isObservedBy, None)))
            assert len(sensor_triples) == 1

            # create observation node
            data_graph.add((measurement_subject, Namespaces.rdf.type, rdflib.URIRef(Namespaces.sosa.Observation)))
            data_graph.add((measurement_subject, Namespaces.schema.name, rdflib.Literal(f'{self._name} Measurement')))
            data_graph.add(
                (measurement_subject, Namespaces.sosa.observedProperty, Semantics.namespace[self._semantic_name]))
            data_graph.add((measurement_subject, Namespaces.sosa.hasResult, result_subject))
            data_graph.add((measurement_subject, Namespaces.sosa.madeBySensor, sensor_triples[0][2]))
            data_graph.add((measurement_subject, Namespaces.schema.license, Semantics.metadata_license))

            result = data_graph
        else:
            raise DeviceException('The provided kind of semantic information cannot be returned.')
        return result

    def resolve_semantic_path(self, suffix: str) -> ('Element', ResourceType):
        try:
            return super().resolve_semantic_path(suffix)
        except ChildNotFoundException:
            if suffix == f'{self.semantic_name.split("/")[-1]}MeasurementResult':
                return self, ResourceType.data
            elif suffix == f'{self.semantic_name.split("/")[-1]}MeasurementUncertainty':
                return self, ResourceType.uncertainty
            elif suffix == f'{self.semantic_name.split("/")[-1]}Measurement':
                return self, ResourceType.observation

            raise ChildNotFoundException('Could not resolve the semantic path.')

    @property
    def semantic_name(self) -> str:
        if self._metadata is None:
            return ""
        subject = next(
            self._metadata.subjects(predicate=Namespaces.rdf.type, object=Namespaces.sosa.ObservableProperty))
        return subject.toPython()
