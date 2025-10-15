"""A Crossplane composition function."""

import asyncio
import importlib
import inspect
import logging
import sys

import grpc
from crossplane.function.proto.v1 import run_function_pb2 as fnv1
from crossplane.function.proto.v1 import run_function_pb2_grpc as grpcv1
from .. import pythonic

logger = logging.getLogger(__name__)


class FunctionRunner(grpcv1.FunctionRunnerService):
    """A FunctionRunner handles gRPC RunFunctionRequests."""

    def __init__(self, debug=False, renderUnknowns=False):
        """Create a new FunctionRunner."""
        self.debug = debug
        self.renderUnknowns = renderUnknowns
        self.clazzes = {}

    def invalidate_module(self, module):
        self.clazzes.clear()
        if module in sys.modules:
            del sys.modules[module]
        importlib.invalidate_caches()

    async def RunFunction(
        self, request: fnv1.RunFunctionRequest, _: grpc.aio.ServicerContext
    ) -> fnv1.RunFunctionResponse:
        try:
            return await self.run_function(request)
        except Exception as e:
            return self.fatal(request, logger, 'RunFunction', e)

    async def run_function(self, request):
        composite = request.observed.composite.resource
        name = list(reversed(composite['apiVersion'].split('/')[0].split('.')))
        name.append(composite['kind'])
        name.append(composite['metadata']['name'])
        logger = logging.getLogger('.'.join(name))

        if composite['apiVersion'] == 'pythonic.fortra.com/v1alpha1' and composite['kind'] == 'Composite':
            if 'spec' not in composite or 'composite' not in composite['spec']:
                return self.fatal(request, logger, 'Missing spec "composite"')
            composite = composite['spec']['composite']
        else:
            if 'composite' not in request.input:
                return self.fatal(request, logger, 'Missing input "composite"')
            composite = request.input['composite']

        # Ideally this is something the Function API provides
        if 'step' in request.input:
            step = request.input['step']
        else:
            step = str(hash(composite))

        clazz = self.clazzes.get(composite)
        if not clazz:
            if '\n' in composite:
                module = Module()
                try:
                    exec(composite, module.__dict__)
                except Exception as e:
                    return self.fatal(request, logger, 'Exec', e)
                for field in dir(module):
                    value = getattr(module, field)
                    if inspect.isclass(value) and issubclass(value, pythonic.BaseComposite) and value != pythonic.BaseComposite:
                        if clazz:
                            return self.fatal(request, logger, 'Composite script has multiple BaseComposite classes')
                        clazz = value
                if not clazz:
                    return self.fatal(request, logger, 'Composite script does not have a BaseComposite class')
            else:
                composite = composite.rsplit('.', 1)
                if len(composite) == 1:
                    return self.fatal(request, logger, f"Composite class name does not include module: {composite[0]}")
                try:
                    module = importlib.import_module(composite[0])
                except Exception as e:
                    return self.fatal(request, logger, 'Import module', e)
                clazz = getattr(module, composite[1], None)
                if not clazz:
                    return self.fatal(request, logger, f"{composite[0]} does not define: {composite[1]}")
                composite = '.'.join(composite)
                if not inspect.isclass(clazz):
                    return self.fatal(request, logger, f"{composite} is not a class")
                if not issubclass(clazz, pythonic.BaseComposite):
                    return self.fatal(request, logger, f"{composite} is not a subclass of BaseComposite")
            self.clazzes[composite] = clazz

        try:
            composite = clazz(request, logger)
        except Exception as e:
            return self.fatal(request, logger, 'Instantiate', e)

        step = composite.context._pythonic[step]
        iteration = int(step.iteration) + 1
        step.iteration = iteration
        composite.context.iteration = iteration
        logger.debug(f"Starting compose, {ordinal(len(composite.context._pythonic))} step, {ordinal(iteration)} pass")

        try:
            result = composite.compose()
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            return self.fatal(request, logger, 'Compose', e)

        if requireds := self.get_requireds(step, composite):
            logger.info(f"Requireds requested: {','.join(requireds)}")
        else:
            self.process_usages(composite)
            self.process_unknowns(composite)
            self.process_auto_readies(composite)
            logger.info('Completed compose')

        return composite.response._message

    def fatal(self, request, logger, message, exception=None):
        if exception:
            message += ' exceptiion'
            logger.exception(message)
            m = str(exception)
            if not m:
                m = exception.__class__.__name__
            message += ': ' + m
        else:
            logger.error(message)
        return fnv1.RunFunctionResponse(
            meta=fnv1.ResponseMeta(
                tag=request.meta.tag,
            ),
            results=[
                fnv1.Result(
                    severity=fnv1.SEVERITY_FATAL,
                    message=message,
                )
            ]
        )

    def get_requireds(self, step, composite):
        requireds = []
        for name, required in composite.requireds:
            if required.apiVersion and required.kind:
                r = pythonic.Map(apiVersion=required.apiVersion, kind=required.kind)
                if required.namespace:
                    r.namespace = required.namespace
                if required.matchName:
                    r.matchName = required.matchName
                for key, value in required.matchLabels:
                    r.matchLabels[key] = value
                if r != step.requireds[name]:
                    step.requireds[name] = r
                    requireds.append(name)
        return requireds

    def process_usages(self, composite):
        for _, resource in sorted(entry for entry in composite.resources):
            dependencies = resource.desired._getDependencies
            if dependencies:
                if self.debug:
                    for destination, source in sorted(dependencies.items()):
                        destination = self.trimFullName(destination)
                        source = self.trimFullName(source)
                        composite.logger.debug(f"Dependency: {destination} = {source}")
                if resource.usages or (resource.usages is None and composite.usages):
                    resources = {}
                    requireds = {}
                    for destination, source in sorted(dependencies.items()):
                        name = source.split('.')
                        if (len(name) > 5 and
                            name[0] == 'request' and
                            name[1] == 'observed' and
                            name[2] == 'resources' and
                            name[4] == 'resource'
                        ):
                            if name[3] not in resources:
                                resources[name[3]] = []
                            resources[name[3]].append(f"{'.'.join(destination.split('.')[5:])} = {'.'.join(name[5:])}")
                        elif (len(name) > 5 and
                            name[0] == 'request' and
                            name[1] == 'extra_resources' and
                            name[3].startswith('items[') and name[3][-1] == ']' and
                            name[4] == 'resource'
                        ):
                            key = (name[2], int(name[3][6:-1]))
                            if key not in requireds:
                                requireds[key] = []
                            requireds[key].append(f"{'.'.join(destination.split('.')[5:])} = {'.'.join(name[5:])}")
                    for name, dependencies in resources.items():
                        source = composite.resources[name]
                        name = [resource.name, str(source.kind)]
                        if source.metadata.namespace:
                            name.append(str(source.metadata.namespace))
                        name.append(str(source.observed.metadata.name))
                        usage = composite.resources['_'.join(name)]('apiextensions.crossplane.io/v1beta1', 'Usage')
                        #usage = composite.resources['_'.join(name)]('protection.crossplane.io/v1beta1', 'Usage')
                        if resource.metadata.namespace:
                            usage.metadata.namespace = resource.metadata.namespace
                        usage.spec.reason = '\n'.join(dependencies)
                        usage.spec.replayDeletion = True
                        usage.spec.by.apiVersion = resource.apiVersion
                        usage.spec.by.kind = resource.kind
                        usage.spec.by.resourceRef.name = resource.observed.metadata.name
                        usage.spec.of.apiVersion = source.apiVersion
                        usage.spec.of.kind = source.kind
                        if source.metadata.namespace:
                            usage.spec.of.resourceRef.namespace = source.metadata.namespace
                        usage.spec.of.resourceRef.name = source.observed.metadata.name
                    for key, dependencies in requireds.items():
                        source = composite.requireds[key[0]][key[1]]
                        name = [resource.name, str(source.kind)]
                        if source.metadata.namespace:
                            name.append(str(source.metadata.namespace))
                        name.append(str(source.metadata.name))
                        usage = composite.resources['_'.join(name)]('apiextensions.crossplane.io/v1beta1', 'Usage')
                        #usage = composite.resources['_'.join(name)]('protection.crossplane.io/v1beta1', 'Usage')
                        if resource.metadata.namespace:
                            usage.metadata.namespace = resource.metadata.namespace
                        usage.spec.reason = '\n'.join(dependencies)
                        usage.spec.replayDeletion = True
                        usage.spec.by.apiVersion = resource.apiVersion
                        usage.spec.by.kind = resource.kind
                        usage.spec.by.resourceRef.name = resource.observed.metadata.name
                        usage.spec.of.apiVersion = source.apiVersion
                        usage.spec.of.kind = source.kind
                        if source.metadata.namespace:
                            usage.spec.of.resourceRef.namespace = source.metadata.namespace
                        usage.spec.of.resourceRef.name = source.observed.metadata.name

    def process_unknowns(self, composite):
        unknownResources = []
        warningResources = []
        fatalResources = []
        for name, resource in sorted(entry for entry in composite.resources):
            unknowns = resource.desired._getUnknowns
            if unknowns:
                unknownResources.append(name)
                warning = False
                fatal = False
                if resource.observed:
                    warningResources.append(name)
                    warning = True
                    if resource.unknownsFatal or (resource.unknownsFatal is None and composite.unknownsFatal):
                        fatalResources.append(name)
                        fatal = True
                if self.debug:
                    for destination, source in sorted(unknowns.items()):
                        destination = self.trimFullName(destination)
                        source = self.trimFullName(source)
                        if fatal:
                            composite.logger.error(f'Observed unknown: {destination} = {source}')
                        elif warning:
                            composite.logger.warning(f'Observed unknown: {destination} = {source}')
                        else:
                            composite.logger.debug(f'Desired unknown: {destination} = {source}')
                if resource.observed:
                    resource.desired._patchUnknowns(resource.observed)
                elif self.renderUnknowns:
                    resource.desired._renderUnknowns(self.trimFullName)
                else:
                    del composite.resources[name]

        if fatalResources:
            level = composite.logger.error
            reason = 'FatalUnknowns'
            message = f"Observed resources with unknowns: {','.join(fatalResources)}"
            status = False
            event = composite.events.fatal
        elif warningResources:
            level = composite.logger.warning
            reason = 'ObservedUnknowns'
            message = f"Observed resources with unknowns: {','.join(warningResources)}"
            status = False
            event = composite.events.warning
        elif unknownResources:
            level = composite.logger.info
            reason = 'DesiredUnknowns'
            message = f"Desired resources with unknowns: {','.join(unknownResources)}"
            status = False
            event = composite.events.info
        else:
            level = None
            reason = 'AllComposed'
            message = 'All resources are composed'
            status = True
            event = None
        if not self.debug and level:
            level(message)
        composite.conditions.ResourcesComposed(reason, message, status)
        if event:
            event(reason, message)

    def process_auto_readies(self, composite):
        for name, resource in composite.resources:
            if resource.autoReady or (resource.autoReady is None and composite.autoReady):
                if resource.ready is None:
                    if resource.conditions.Ready.status:
                        resource.ready = True

    def trimFullName(self, name):
        name = name.split('.')
        for values in (
                ('request', 'observed', 'composite', 'resource'),
                ('request', 'observed', 'resources', None, 'resource'),
                ('request', 'extra_resources', None, 'items', None, 'resource'),
                ('response', 'desired', 'resources', None, 'resource'),
        ):
            if len(values) < len(name):
                ix = 0
                for iv, value in enumerate(values):
                    if value:
                        if value != name[ix]:
                            if not name[ix].startswith(f"{values[iv]}[") or iv+1 >= len(values) or values[iv+1]:
                                break
                            continue
                    ix += 1
                else:
                    ix = 0
                    for value in values:
                        if value:
                            if value == name[ix]:
                                del name[ix]
                            elif ix:
                                name[ix-1] += name[ix][len(value):]
                                del name[ix]
                            else:
                                name[ix] = name[ix][len(value):]
                        else:
                            ix += 1
                    break
        return '.'.join(name)


def ordinal(ix):
    ix = int(ix)
    if 11 <= (ix % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(ix % 10, 4)]
    return str(ix) + suffix


class Module:
    def __init__(self):
        self.BaseComposite = pythonic.BaseComposite
        self.append = pythonic.append
        self.Map = pythonic.Map
        self.List = pythonic.List
        self.Unknown = pythonic.Unknown
        self.Yaml = pythonic.Yaml
        self.Json = pythonic.Json
        self.B64Encode = pythonic.B64Encode
        self.B64Decode = pythonic.B64Decode
