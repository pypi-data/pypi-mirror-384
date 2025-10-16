# -*- coding: utf-8 -*-
import asyncio
import functools
import json
import os
import traceback
from typing import Dict, Union

import rdflib
from aiohttp import web
from aiohttp.web import middleware
from aiohttp.web_request import Request
from multidict import MultiDict
from wzl.mqtt import MQTTPublisher

from .error import ServerException
from ..soil.component import Component
from ..soil.element import Element
from ..soil.error import InvokationException, ReadOnlyException, ChildNotFoundException
from ..soil.function import Function
from ..soil.measurement import Measurement
from ..soil.parameter import Parameter
from ..soil.semantics import Semantics, Namespaces
from ..stream.scheduler import StreamScheduler
from ..soil.variable import Variable
from ..utils import root_logger
from ..utils import serialize
from ..utils.constants import BASE_UUID_PATTERN, HTTP_GET, HTTP_OPTIONS
from ..utils.error import DeviceException, UserException, PathResolutionException
from ..utils.resources import ResourceType

logger = root_logger.get(__name__)


@middleware
async def cors(request, handler):
    logger.info("CORS Middleware handles request from {}".format(request.url))
    logger.debug('Request Headers: {}'.format(request.headers))
    response = web.Response()
    # check if the request is a preflight request
    if 'Access-Control-Request-Method' in request.headers and request.headers['Access-Control-Request-Method'] in [
        "POST", "PATCH"]:
        response.headers.update({'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH',
                                 'Access-Control-Allow-Headers': request.headers['Access-Control-Request-Headers']})
        response.headers.update({'Access-Control-Allow-Origin': request.headers['Origin']})
        logger.debug('Preflight Response Headers :{}'.format(response.headers))
        return response
    try:
        response = await handler(request)
    except Exception as e:
        logger.error(traceback.format_exc())
        response = web.json_response({"description": str(e)}, status=500)
        logger.error(["[CORS] {} at {}".format(str(e), request.url)])
    finally:
        response.headers.update({'Access-Control-Allow-Origin': request.headers.get('Origin', "*")})
        logger.debug('Response Headers :{}'.format(response.headers))
        return response


class HTTPServer(object):
    """Provides a web application as of the aiohttp-library.

    """

    def __init__(self, loop: asyncio.AbstractEventLoop, host: str, port: int, model: Component,
                 dataformat: str = 'json', legacy_mode=False, scheduler: StreamScheduler = None,
                 publisher: MQTTPublisher = None, profiles_path: str = None):
        """Constructor

        Args:
            loop: The asyncio-event-loop used to execute the server.
            host: Hostname of the server, i.e. a URL such as 'localhost'.
            port: Port the server should run at.
            model: The root component of the SOIL model, should be initialized via Component.load(...)
            dataformat: String specifying the dataformat of the responses of the server, either 'json' (default) or 'xml'.
            legacy_mode: If true, the datatypes are serialized to "bool" and "float" (instead of "boolean" and "float").
            scheduler: Stream handler. Is required to hand over jobs of streams and events for dynamic components, if created at runtime.
        """
        if dataformat not in ['json', 'xml']:
            raise ValueError('Dataformat must be one of "json" or "xml".')

        self.loop = loop
        self.host = host
        self.port = port
        self.root = model
        self._dataformat = dataformat
        self._legacy_mode = legacy_mode
        self._scheduler = scheduler
        self._publisher = publisher
        self._profiles_path = profiles_path

        self.app = web.Application(loop=self.loop, middlewares=[cors])

        # define two routes for each request to make the 'objects' part optional
        self.app.router.add_get(r'/objects{uuids:(/' + BASE_UUID_PATTERN + r')*/?}', self.get)
        self.app.router.add_get(r'/{uuids:(' + BASE_UUID_PATTERN + r'($|/))*}', self.get)
        self.app.router.add_post(r'/objects{uuids:(/' + BASE_UUID_PATTERN + r')*/?}', self.post)
        self.app.router.add_post(r'/{uuids:(' + BASE_UUID_PATTERN + r'($|/))*}', self.post)
        self.app.router.add_delete(r'/objects{uuids:(/' + BASE_UUID_PATTERN + r')*/?}', self.delete)
        self.app.router.add_delete(r'/{uuids:(' + BASE_UUID_PATTERN + r'($|/))*}', self.delete)
        self.app.router.add_route('OPTIONS', r'/objects{uuids:(/' + BASE_UUID_PATTERN + r')*/?}', self.options)
        self.app.router.add_route('OPTIONS', r'/{uuids:(' + BASE_UUID_PATTERN + r'($|/))*}', self.options)
        self.app.router.add_put(r'/objects{uuids:(/' + BASE_UUID_PATTERN + r')*/?}', self.put)
        self.app.router.add_put(r'/{uuids:(' + BASE_UUID_PATTERN + r'($|/))*}', self.put)
        self.app.router.add_patch(r'/objects{uuids:(/' + BASE_UUID_PATTERN + r')*/?}', self.patch)
        self.app.router.add_patch(r'/{uuids:(' + BASE_UUID_PATTERN + r'($|/))*}', self.patch)
        web.run_app(self.app, host=self.host, port=self.port, loop=loop)
        logger.info('HTTP-Server serving on {}:{}'.format(host, port))

    @staticmethod
    def analyze_request_url(request: Request) -> ResourceType:
        assert request.url.parts[0] == '/'

        url_parts = request.url.parts
        if url_parts[-1] == '':
            url_parts = url_parts[:-1]

        if len(url_parts) == 3 and url_parts[1] == Semantics.prefix:
            return ResourceType.profile if 'Profile' in url_parts[-1] else ResourceType.metadata

        if request.url.path == '/' or url_parts[-1][:3] in ['COM', 'FUN', 'PAR', 'MEA', 'ARG', 'RET']:
            return ResourceType.element

        return ResourceType.metadata

    @staticmethod
    def parse_uuids(request: Request):
        """Splits the request URL to extract the FQID of the targeted element of the SOIL-Interface.

        Args:
            request:

        Returns:

        """
        uuids = request.match_info.get('uuids', 'uuids')
        uuid_list = uuids.split('/')
        while '' in uuid_list:
            uuid_list.remove('')
        return uuid_list

    def _filter_query(self, query: MultiDict):
        queried_attributes = []
        for key in query:
            if key in ['uuid', 'name', 'description', 'datatype', 'range', 'value', 'constant', 'timestamp',
                       'dimension', 'unit', 'covariance', 'label', 'children', 'arguments', 'returns', 'ontology']:
                queried_attributes += [key]
        return queried_attributes

    def prepare_response(self, body: Union[Dict, rdflib.Graph], element: Element, status: int = 200,
                         query: MultiDict = None, semantic: bool = False):
        dataformat = self._dataformat
        if query is not None and 'format' in query and query['format'] in ['json', 'xml', 'turtle']:
            dataformat = query['format']
        if query is not None and 'semantic' in query and query['semantic'] in ['data', 'metadata', 'profile']:
            semantic = True

        if dataformat == 'json':
            if semantic:
                assert isinstance(body, rdflib.Graph)
                # rdflib serialization returns a string, so we need to parse it as plain json again to return it properly
                body = json.loads(body.serialize(format='json-ld'))
            return web.json_response(body, status=status)
        elif dataformat == 'xml':
            if semantic:
                assert isinstance(body, rdflib.Graph)
                xml = body.serialize(format='xml')
            else:
                if element is not None and 200 <= status <= 300:
                    root = ''
                    if isinstance(element, Component):
                        root = 'component'
                    elif isinstance(element, Function):
                        root = 'function'
                    elif isinstance(element, Measurement):
                        root = 'measurement'
                    elif isinstance(element, Parameter):
                        root = 'parameter'
                else:
                    root = 'error'
                xml = serialize.to_xml(root, body)
            return web.Response(text=xml, status=status, content_type='application/xml')
        elif dataformat == 'turtle':
            if semantic:
                assert isinstance(body, rdflib.Graph)
                text = body.serialize(format='turtle')
            else:
                return web.Response(text='Can not serialize non semantic information to Turtle', status=400,
                                    content_type='text/plain')
            return web.Response(text=text, status=status, content_type=' text/plain')

    async def get(self, request):
        logger.info("GET Request from {}".format(request.url))
        logger.debug('Request: {}'.format(request))
        logger.debug('Query Parameters: {}'.format(request.query_string))

        resource_type = HTTPServer.analyze_request_url(request)
        keys = self._filter_query(request.query)

        try:
            if resource_type == ResourceType.profile:
                if self._profiles_path is None:
                    raise UserException('Can\'t return requested metadata profile, as no profiles have been created for this sensor service.')

                profilename = request.url.parts[-2] if request.url.parts[-1] == '' else request.url.parts[-1]

                if len(profilename) > 12 and profilename[-12:-7] == 'Range':
                    filename = profilename.replace('RangeProfile', '.shacl.ttl')
                else:
                    filename = profilename.replace('Profile', '.shacl.ttl')

                profile_path = os.path.join(self._profiles_path, filename)
                response = rdflib.Graph()
                response.parse(profile_path)
                response.add(
                    (rdflib.URIRef(Semantics.namespace[profilename]), Namespaces.dcterms.license, Semantics.profile_license))
                item, status = None, 200

            elif resource_type.is_semantic():
                semantic_name = request.url.parts[-2] if request.url.parts[-1] == '' else request.url.parts[-1]

                item, resource_type = self.root.resolve_semantic_path(semantic_name)
                recursive = request.query is not None and 'all' in request.query
                response = item.serialize_semantics(resource_type, recursive)
            else:
                assert resource_type == ResourceType.element
                uuids = HTTPServer.parse_uuids(request)

                if request.query is not None and 'semantic' in request.query and request.query[
                    'semantic'] in ResourceType.semantic_resources:
                    resource_type = ResourceType.from_string(request.query['semantic'])

                try:
                    item = self.root[uuids]

                    if resource_type.is_semantic():
                        recursive = request.query is not None and 'all' in request.query
                        response = item.serialize_semantics(resource_type, recursive)
                    else:
                        response = item.serialize(keys, self._legacy_mode, HTTP_GET)
                except KeyError as e:
                    logger.error(traceback.format_exc())
                    response = {'error': str(e)}
                    logger.error('Response: {}'.format(response))
                    return self.prepare_response(response, None, status=404, query=request.query)

            status = 200
            logger.info('Response: {}'.format(response))
        except (DeviceException, ServerException, UserException) as e:
            logger.error(traceback.format_exc())
            response = {'error': str(e)}
            status = 500
            logger.error('Response: {}'.format(response))

        return self.prepare_response(response, item, status=status, query=request.query, semantic=resource_type.is_semantic())

    async def post(self, request):
        logger.info("POST Request from {}".format(request.url))
        logger.debug('Request: {}'.format(request))
        data = await request.json()
        logger.debug('Body: {}'.format(data))
        uuids = HTTPServer.parse_uuids(request)

        try:
            item = self.root[uuids]
        except KeyError as e:
            logger.error(traceback.format_exc())
            response = {'error': str(e)}
            logger.error('Response: {}'.format(response))
            return self.prepare_response(response, None, status=404, query=request.query)

        if isinstance(item, Function):
            try:
                if item.publishes:
                    try:
                        async for item in item.invoke_generator(data["arguments"], legacy_mode=self._legacy_mode):
                            self._publisher.publish('/'.join(uuids), json.dumps(item))
                    except RuntimeError as e:
                        if not isinstance(e.__cause__, StopAsyncIteration):
                            raise e
                    response = {}
                else:
                    response = await item.invoke(data["arguments"], legacy_mode=self._legacy_mode)
                status = 200
                logger.info('Response: {}'.format(response))
            except (DeviceException, ServerException, UserException) as e:
                logger.error(traceback.format_exc())
                response = {'error': str(e)}
                status = 500
                logger.error('Response: {}'.format(response))
        else:
            response, status = {}, 405
            logger.error('Response: {}'.format(response))

        return self.prepare_response(response, item, status=status, query=request.query)

    async def delete(self, request):
        logger.info("DELETE Request from {}".format(request.url))
        logger.debug('Request: {}'.format(request))
        uuids = HTTPServer.parse_uuids(request)

        try:
            item = self.root[uuids[:-1]]
        except KeyError as e:
            logger.error(traceback.format_exc())
            response = {'error': str(e)}
            logger.error('Response: {}'.format(response))
            return self.prepare_response(response, None, status=404, query=request.query)

        if not isinstance(item, Component):
            return self.prepare_response({}, None, status=405, query=request.query)
        try:
            await self.loop.run_in_executor(None, functools.partial(item.remove, uuids[-1]))

            if self._scheduler is not None:
                self._scheduler.remove_jobs('/'.join(uuids))
            status = 200
            # logger.info('Response: {}'.format(response))
        except ChildNotFoundException as e:
            logger.error(traceback.format_exc())
            response = {'error': str(e)}
            status = 404
            logger.error('Response: {}'.format(response))
        except (DeviceException, ServerException, UserException) as e:
            logger.error(traceback.format_exc())
            response = {'error': str(e)}
            status = 500
            logger.error('Response: {}'.format(response))
        return self.prepare_response(response, item, status=status, query=request.query)

    async def options(self, request):
        logger.info("HEAD Request from {}".format(request.url))
        logger.debug('Request: {}'.format(request))
        logger.debug('Query Parameters: {}'.format(request.query_string))
        keys = self._filter_query(request.query)

        try:
            item = self.root[HTTPServer.parse_uuids(request)]
        except KeyError as e:
            logger.error(traceback.format_exc())
            response = {'error': str(e)}
            logger.error('Response: {}'.format(response))
            return self.prepare_response(response, None, status=404, query=request.query)

        if not isinstance(item, Variable):
            return self.prepare_response({}, None, status=405, query=request.query)

        response = item.serialize(keys, self._legacy_mode, HTTP_OPTIONS)
        logger.info('Response: {}'.format(response))
        return self.prepare_response(response, item, query=request.query)

    async def patch(self, request):
        logger.info("PATCH Request from {}".format(request.url))
        logger.debug('Request: {}'.format(request))
        data = await request.json()
        logger.debug('Body: {}'.format(data))

        try:
            item = self.root[HTTPServer.parse_uuids(request)]
        except KeyError as e:
            logger.error(traceback.format_exc())
            response = {'error': str(e)}
            logger.error('Response: {}'.format(response))
            return self.prepare_response(response, None, status=404, query=request.query)

        if isinstance(item, Parameter):
            try:
                response = await self.loop.run_in_executor(None, item.set, data["value"])
                status = 200
                logger.info('Response: {}'.format(response))
            except ReadOnlyException as e:
                logger.error(traceback.format_exc())
                response = {'error': str(e)}
                status = 403
                logger.error('Response: {}'.format(response))
            except InvokationException as e:
                logger.error(traceback.format_exc())
                response = {'error': str(e)}
                status = 500
                logger.error('Response: {}'.format(response))
        else:
            response, status = {}, 405
            logger.error('Response: {}'.format(response))
        return self.prepare_response(response, item, status=status, query=request.query)

    async def put(self, request):
        logger.info("PUT Request from {}".format(request.url))
        logger.debug('Request: {}'.format(request))
        data = await request.json()
        logger.debug('Body: {}'.format(data))
        uuids = HTTPServer.parse_uuids(request)

        try:
            item = self.root[uuids[:-1]]
        except KeyError as e:
            logger.error(traceback.format_exc())
            response = {'error': str(e)}
            logger.error('Response: {}'.format(response))
            return self.prepare_response(response, None, status=404, query=request.query)

        if not isinstance(item, Component):
            return self.prepare_response({}, None, status=405, query=request.query)
        try:
            implementation = await self.loop.run_in_executor(None,
                                                             functools.partial(item.add, uuids[-1], data['class_name'],
                                                                               data['json_file'], *data['args'],
                                                                               **data['kwargs']))
            if self._scheduler is not None:
                self._scheduler.add_jobs(implementation.streams('/'.join(uuids)))
            status = 200
            response = {}
            # logger.info('Response: {}'.format(response))
        except (DeviceException, ServerException, UserException) as e:
            logger.error(traceback.format_exc())
            response = {'error': str(e)}
            status = 500
            logger.error('Response: {}'.format(response))
        return self.prepare_response(response, item, status=status, query=request.query)
