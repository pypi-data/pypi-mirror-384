import re
import urllib

import rdflib

from ..utils.constants import URL_PATTERN


class Semantics(object):
    prefix: str = None
    url: str = None
    namespace: rdflib.Namespace = None
    profile_license: rdflib.term.Identifier = rdflib.URIRef("https://spdx.org/licenses/CC-BY-4.0.html")
    metadata_license: rdflib.term.Identifier = rdflib.URIRef("https://spdx.org/licenses/CC-BY-NC-ND-4.0.html")
    data_license: rdflib.term.Identifier = rdflib.Literal("All rights reserved.")

    def __init__(self, config: dict[str, str]):
        Semantics.prefix = config['prefix']
        Semantics.url = config['url']
        Semantics.namespace = rdflib.Namespace(config['url'])
        if 'profile-license' in config:
            if re.match(URL_PATTERN, config['profile-license']):
                Semantics.profile_license = rdflib.URIRef(config['profile-license'])
            else:
                Semantics.profile_license = rdflib.Literal(config['profile-license'])
        if 'metadata-license' in config:
            if re.match(URL_PATTERN, config['metadata-license']):
                Semantics.metadata_license = rdflib.URIRef(config['metadata-license'])
            else:
                Semantics.metadata_license = rdflib.Literal(config['metadata-license'])
        if 'data-license' in config:
            if re.match(URL_PATTERN, config['data-license']):
                Semantics.data_license = rdflib.URIRef(config['data-license'])
            else:
                Semantics.data_license = rdflib.Literal(config['data-license'])


class Namespaces(object):
    dcterms = rdflib.namespace.DCTERMS
    earl = rdflib.Namespace('http://www.w3.org/ns/earl#')
    m4i = rdflib.Namespace('http://w3id.org/nfdi4ing/metadata4ing#')
    owl = rdflib.Namespace('http://www.w3.org/2002/07/owl#')
    quantitykind = rdflib.Namespace('http://qudt.org/vocab/quantitykind/')
    qudt = rdflib.Namespace('http://qudt.org/schema/qudt/')
    rdf = rdflib.namespace.RDF
    schema = rdflib.Namespace('http://schema.org/')
    si = rdflib.Namespace('https://ptb.de/si/')
    soil = rdflib.Namespace('https://purl.org/fair-sensor-services/soil#')
    sosa = rdflib.namespace.SOSA
    ssn = rdflib.namespace.SSN
    ssn_system = rdflib.Namespace('http://www.w3.org/ns/ssn/systems/')
    unit = rdflib.Namespace('http://qudt.org/vocab/unit/')
