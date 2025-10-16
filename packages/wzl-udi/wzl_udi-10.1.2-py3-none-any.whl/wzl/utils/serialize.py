from typing import Any, Dict
from xml.etree.ElementTree import Element, tostring


def to_xml(root: str, data: Dict) -> str:
    """ Takes a dictionary and translates it to a XML-string.

    Args:
        root: String used as tag of the enclosing root-element of the xml-tree.
        data: Dictionary to be serialized to XML-string.

    Returns:
        String of an XML-Element-Tree.
    """
    def _recursive_serialization(tag: str, data: Any) -> Element:
        element = Element(tag)
        if isinstance(data, dict):
            for key, value in data.items():
                element.append(_recursive_serialization(key, value))
        elif isinstance(data, list):
            for index, value in enumerate(data):
                child = _recursive_serialization(tag, value)
                child.set('index', str(index))
                element.append(child)
        else:
            element.text = str(data)
        return element

    return tostring(_recursive_serialization(root, data), encoding='unicode')
