import asyncio
import datetime
import inspect
import time
from abc import ABC
from typing import Any, List, Callable, Union

import nest_asyncio
import pytz
import rdflib

from .datatype import Datatype
from .semantics import Namespaces
from ..utils.resources import ResourceType

nest_asyncio.apply()

from .element import Element
from .error import DimensionException, RangeException, TypeException, NotImplementedException, ChildNotFoundException
from ..utils import root_logger
from ..utils.constants import HTTP_GET, HTTP_OPTIONS
from ..utils.error import DeviceException

logger = root_logger.get(__name__)


def validate_time(time_rfc3339: Union[str, List]):
    if isinstance(time_rfc3339, list):
        for e in time_rfc3339:
            if not validate_time(e):
                return False
        return True
    else:
        if time_rfc3339 is None or time_rfc3339 == "":
            return False

        formats = ["%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"]

        for fmt in formats:
            try:
                if fmt.endswith('Z'):
                    datetime.datetime.strptime(time_rfc3339.rstrip('Z'), fmt.rstrip('Z'))
                else:
                    datetime.datetime.strptime(time_rfc3339, fmt)
                return True

            except ValueError:
                continue
        return False


def parse_time(time_rfc3339: Union[str, List]):
    if isinstance(time_rfc3339, list):
        return [parse_time(e) for e in time_rfc3339]
    else:
        if time_rfc3339 is None or time_rfc3339 == "":
            return None

        formats = ["%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"]

        for fmt in formats:
            try:
                # Attempt to parse the timestamp with the current format
                if fmt.endswith('Z'):
                    # Strip the 'Z' and replace it after parsing if format specifies 'Z' at the end
                    dt = datetime.datetime.strptime(time_rfc3339.rstrip('Z'), fmt.rstrip('Z'))
                    dt = dt.replace(tzinfo=pytz.UTC)
                else:
                    dt = datetime.datetime.strptime(time_rfc3339, fmt)
                return dt

            except ValueError:
                # If parsing fails, try the next format
                continue

        return None


def serialize_time(time):
    return time.isoformat()


class Variable(Element, ABC):
    def __init__(self, uuid: str, name: str, description: str, datatype: Datatype, dimension: List[int], range: List,
                 value: Any, getter: Callable, ontology: str = None, profile: str = None):
        Element.__init__(self, uuid, name, description, ontology, profile)
        # if type(datatype) is not str:
        #     raise Exception('{}: Datatype must be passed as string.'.format(uuid))
        Variable.check_all(datatype, dimension, range, value)
        if getter is not None and not callable(getter):
            raise TypeError("{}: The getter of the Figure must be callable!".format(uuid))
        self._datatype = datatype
        self._dimension = dimension
        self._range = range
        if datatype == Datatype.TIME:
            self._value = parse_time(value)
        else:
            self._value = value
        self._getter = getter

    @property
    def datatype(self):
        return self._datatype

    @property
    def dimension(self):
        return self._dimension

    @property
    def range(self):
        return self._range

    def __getitem__(self, item: str, method=HTTP_GET):
        """
        Getter-Method.
        According to the given key the method returns the value of the corresponding attribute.
        :param item: name of the attribute. Provided as string without leading underscores.
        :param method: ???
        :return: the value of the attribute indicated by 'item'.
        """
        if item == "datatype":
            return self._datatype
        if item == "value":
            if method != HTTP_OPTIONS:
                try:
                    if inspect.iscoroutinefunction(self.get):
                        loop = asyncio.get_event_loop()
                        value = loop.run_until_complete(asyncio.gather(self.get()))[0]
                    else:
                        value = self.get()

                    if self._datatype == Datatype.TIME:
                        value = serialize_time(value)
                    elif self._datatype == Datatype.ENUM:
                        value = str(value)

                except Exception as e:
                    raise DeviceException(
                        'Could not provide value of Measurement/Parameter {}: {}'.format(self.uuid, str(e)),
                        predecessor=e)

                Variable.check_all(self._datatype, self._dimension, self._range, value)
                self._value = value
                return value
            else:
                return self._value
        if item == 'dimension':
            return self._dimension
        if item == 'range':
            return self._range
        if item == []:
            return self
        return super().__getitem__(item, method)

    # def __setitem__(self, key: str, value):
    #     """
    #     Setter - Method
    #     If key is "value" datatype, dimension and range is checked for correctness.
    #     :param key: sets the value of the attribute with name 'item' to the provided value.
    #     :param value: value to be set
    #     """
    #     super().__setitem__(key, value)

    def serialize(self, keys: [str], legacy_mode: bool, method=HTTP_GET):
        """
        Serializes an object of type Figure into a JSON-like dictionary.
        :param keys: All attributes given in the "keys" array are serialized.
        :param method: ???
        :return: a dictionary having all "keys" as keys and the values of the corresponding attributes as value.
        """
        # list is empty provide all attributes of the default-serialization
        if not keys:
            keys = ['uuid', 'name', 'description', 'datatype', 'value', 'dimension', 'range']
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
    def check_dimension(dimension: List, value: Any):
        """
        Checks whether the given value is of given dimension
        :param dimension: the dimension the value provided by "value" should have
        :param value: value to be checked for the dimension
        """
        # dimension of undefined value must not be checked => valid
        if value is None:
            return
        # base case 1: dimension is empty and variable is not a scalar => not valid
        if not dimension and not Variable.is_scalar(value):
            raise DimensionException('Figure of dimension 0 can not be of type list!')
        # base case 2: dimension is empty and variable is a scalar => valid
        elif not dimension:
            return
        try:
            # base case 3: current dimension is fixed size "x" and length of the value is not "x" => not valid
            if dimension[0] != 0 and len(value) != dimension[0]:
                raise DimensionException('Dimension of data does not match dimension of variable!')
        except TypeError as te:
            raise DimensionException(str(te))
        # recursion case
        # at this point value is guaranteed to be of type list
        # => recursively check the dimension of each "subvalue"
        for v in value:
            try:
                Variable.check_dimension(dimension[1:], v)
            except DimensionException as e:
                raise e

    @staticmethod
    def check_type(datatype: Datatype, value: any):
        """
        Checks if the given value is of the correct datatype. If value is not a scale, it checks all "subvalues" for correct datatype.
        :param datatype: datatype the value provided by "value" should have
        :param value: value to be checked for correct datatype
        """
        # datatype of undefined value must not be checked => valid
        if value is None:
            return
        # base case: value is a scalar
        if Variable.is_scalar(value):
            # check if the type of value corresponds to given datatype
            if datatype == Datatype.BOOLEAN and not isinstance(value, bool):
                raise TypeException("Boolean field does not match non-boolean value {}!".format(value))
            elif datatype == Datatype.INTEGER and not isinstance(value, int):
                raise TypeException("Integer field does not match non-integer value {}!".format(value))
            elif datatype == Datatype.FLOAT and not isinstance(value, float) and not isinstance(value, int):
                raise TypeException("Float field does not match non-float value {}!".format(value))
            elif datatype == Datatype.STRING and not isinstance(value, str):
                raise TypeException("String field does not match non-string value {}!".format(value))
            elif datatype == Datatype.ENUM and not isinstance(value, str):
                raise TypeException(
                    "Enum field {} must be a string!".format(value))
            elif datatype == Datatype.TIME and not isinstance(value, str):
                raise TypeException(
                    "Time field {} must be string.".format(
                        value))
            elif datatype == Datatype.TIME and isinstance(value, str):
                if value != "" and value is not None and not validate_time(value):
                    raise TypeException("Value is not a valid RFC3339-formatted timestring: {}".format(value))
        else:
            # recursion case: value is an array or matrix => check datatype of each "subvalue" recursively
            for v in value:
                try:
                    Variable.check_type(datatype, v)
                except TypeException as e:
                    raise e

    @staticmethod
    def check_range(datatype: Datatype, range, value):
        """
        Checks if the given value is within provided range (depending on the given datatype)

        IMPORTANT: It is not checked whether the value is of correct type. If the type of value is not correct, the result
        of check_range is not meaningful! To get expressive result check datatype before calling check_range!

        :param datatype: datatype of the value
        :param range: the range the value should be within
        :param value: value to be checked for range

        For all datatypes (except "bool" and "enum")the range specification is of the following form: [lower bound (LB), upper bound (UB)]
        If LB or UB are None the value is unrestricted to the bottom or top, respectively.
        In case of "int", "double" and "time" the interpretation of LB and UB is straightforward.
        For "string" LB and UB restrict the length of the string. (If LB is given as None, 0 is the natural LB of cause)
        "bool" is naturally bounded to "True" and "False", thus the range is not checked.
        In case of "enum" the range contains the list of all possible values.
        """
        # if the list is empty, all values are possible
        if not range:
            if datatype == Datatype.ENUM:
                raise RangeException('A value of type enum must provide a range with possible values!')
            else:
                return
        # base case: value is scalar => check if the value is in range
        if Variable.is_scalar(value):
            # bool is not checked, since there is only true and false
            if datatype == Datatype.BOOLEAN:
                return
            elif datatype == Datatype.INTEGER and value is not None:
                if range[0] is not None and value < range[0]:
                    raise RangeException("Integer value {} is smaller than lower bound {}!".format(value, range[0]))
                elif range[1] is not None and value > range[1]:
                    raise RangeException("Integer value {} is higher than upper bound {}!".format(value, range[1]))
            elif datatype == Datatype.FLOAT and value is not None:
                if range[0] is not None and value < range[0]:
                    raise RangeException("Double value {} is smaller than lower bound {}!".format(value, range[0]))
                elif range[1] is not None and value > range[1]:
                    raise RangeException("Double value {} is higher than upper bound {}!".format(value, range[1]))
            elif datatype == Datatype.STRING and value is not None:
                if range[0] is not None and len(value) < range[0]:
                    raise RangeException(
                        "String value {} is too short. Minimal required length is {}!".format(value, range[0]))
                elif range[1] is not None and len(value) > range[1]:
                    raise RangeException(
                        "String value {} is too long. Maximal allowed length is {}!".format(value, range[1]))
            elif datatype == Datatype.ENUM and value is not None:
                if value not in range:
                    raise RangeException("Enum value {} is not within the set of allowed values!".format(value))
            elif datatype == Datatype.TIME and value is not None and value != "":
                if range[0] is not None:
                    if not validate_time(range[0]):
                        raise TypeException(
                            "Can not check range of time value. Lower bound {} is not a valid RFC3339 timestring.".format(
                                range[0]))
                    if parse_time(value) < parse_time(range[0]):
                        raise RangeException(
                            "Time value {} is smaller than lower bound {}!".format(parse_time(value),
                                                                                   parse_time(range[0])))
                elif range[1] is not None:
                    if not validate_time(range[1]):
                        raise TypeException(
                            "Can not check range of time value. Upper bound {} is not a valid RFC3339 timestring.".format(
                                range[0]))
                    if parse_time(value) > parse_time(range[1]):
                        raise RangeException(
                            "Time value {} is greater than upper bound {}!".format(parse_time(value),
                                                                                   parse_time(range[1])))
        else:
            # recursion case: value is an array or matrix => check range of each "subvalue" recursively
            for v in value:
                try:
                    Variable.check_range(datatype, range, v)
                except RangeException as e:
                    raise e

    def serialize_value(self, data_graph: rdflib.Graph, value: Any) -> rdflib.term.Identifier:
        if isinstance(value, list):
            blank_node = rdflib.BNode()
            data_graph.add((blank_node, Namespaces.rdf.rest, Namespaces.rdf.nil))
            data_graph.add(
                (blank_node, Namespaces.rdf.first, self.serialize_value(data_graph, value[len(value) - 1])))
            for entry in reversed(value[:-1]):
                new_blank_node = rdflib.BNode()
                data_graph.add((new_blank_node, Namespaces.rdf.rest, blank_node))
                data_graph.add((new_blank_node, Namespaces.rdf.first, self.serialize_value(data_graph, entry)))
                blank_node = new_blank_node
            return blank_node
        else:
            return rdflib.Literal(value, datatype=self.datatype.to_semantic())

    @staticmethod
    def is_scalar(value):
        return not isinstance(value, list)

    @staticmethod
    def check_all(datatype, dimension, range, value):
        Variable.check_type(datatype, value)
        Variable.check_dimension(dimension, value)
        Variable.check_range(datatype, range, value)

    @property
    def get(self):
        if self._getter is not None:
            return self._getter
        else:
            raise NotImplementedException(self._uuid, self._name)

    def resolve_semantic_path(self, suffix: str) -> (Element, ResourceType):
        try:
            return super().resolve_semantic_path(suffix)
        except ChildNotFoundException:
            # check if the path fits the range
            if suffix == f'{self.semantic_name.split("/")[-1]}Range':
                return self, ResourceType.range

            raise ChildNotFoundException('Could not resolve the semantic path.')
