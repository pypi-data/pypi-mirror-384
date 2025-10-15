
import datetime
from google.protobuf.duration_pb2 import Duration
from crossplane.function.proto.v1 import run_function_pb2 as fnv1

from . import protobuf


_notset = object()


class BaseComposite:
    def __init__(self, request, logger):
        self.request = protobuf.Message(None, 'request', request.DESCRIPTOR, request, 'Function Request')
        response = fnv1.RunFunctionResponse(
            meta=fnv1.ResponseMeta(
                tag=request.meta.tag,
                ttl=Duration(
                    seconds=60,
                ),
            ),
            desired=request.desired,
            context=request.context,
        )
        self.response = protobuf.Message(None, 'response', response.DESCRIPTOR, response)
        self.logger = logger
        self.credentials = Credentials(self.request)
        self.context = self.response.context
        self.environment = self.context['apiextensions.crossplane.io/environment']
        self.requireds = Requireds(self)
        self.resources = Resources(self)
        self.unknownsFatal = True
        self.autoReady = True
        self.usages = False

        observed = self.request.observed.composite
        desired = self.response.desired.composite
        self.observed = observed.resource
        self.desired = desired.resource
        self.apiVersion = self.observed.apiVersion
        self.kind = self.observed.kind
        self.metadata = self.observed.metadata
        self.spec = self.observed.spec
        self.status = self.desired.status
        self.conditions = Conditions(observed, self.response)
        self.connection = Connection(observed, desired)
        self.events = Events(self.response)

    @property
    def ttl(self):
        if self.response.meta.ttl.nanos:
            return float(self.response.meta.ttl.seconds) + (float(self.response.meta.ttl.nanos) / 1000000000.0)
        return int(self.response.meta.ttl.seconds)

    @ttl.setter
    def ttl(self, ttl):
        if isinstance(ttl, int):
            self.response.meta.ttl.seconds = ttl
            self.response.meta.ttl.nanos = 0
        elif isinstance(ttl, float):
            self.response.meta.ttl.seconds = int(ttl)
            if ttl.is_integer():
                self.response.meta.ttl.nanos = 0
            else:
                self.response.meta.ttl.nanos = int((ttl - int(self.response.meta.ttl.seconds)) * 1000000000)
        else:
            raise ValueError('ttl must be an int or float')

    @property
    def ready(self):
        ready = self.desired._parent.ready
        if ready == fnv1.Ready.READY_TRUE:
            return True
        if ready == fnv1.Ready.READY_FALSE:
            return False
        return None

    @ready.setter
    def ready(self, ready):
        if ready:
            ready = fnv1.Ready.READY_TRUE
        elif ready == None or (isinstance(ready, protobuf.Value) and ready._isUnknown):
            ready = fnv1.Ready.READY_UNSPECIFIED
        else:
            ready = fnv1.Ready.READY_FALSE
        self.desired._parent.ready = ready

    async def compose(self):
        raise NotImplementedError()


class Credentials:
    def __init__(self, request):
        self.__dict__['_request'] = request

    def __getattr__(self, key):
        return self[key]

    def __getitem__(self, key):
        return Credential(self._request.credentials[key])

    def __bool__(self):
        return bool(self._request.credentials)

    def __len__(self):
        return len(self._request.credentials)

    def __contains__(self, key):
        return key in self._request.credentials

    def __iter__(self):
        for key, resource in self._request.credentials:
            yield key, self[key]


class Credential:
    def __init__(self, credential):
        self.__dict__['_credential'] = credential

    def __getattr__(self, key):
        return self[key]

    def __getitem__(self, key):
        return self._credential.credential_data.data[key]

    def __bool__(self):
        return bool(self._credential.credential_data.data)

    def __len__(self):
        return len(self._credential.credential_data.data)

    def __contains__(self, key):
        return key in self._credential.credential_data.data

    def __iter__(self):
        for key, resource in self._credential.credential_data.data:
            yield key, self[key]


class Resources:
    def __init__(self, composite):
        self.__dict__['_composite'] = composite

    def __getattr__(self, key):
        return self[key]

    def __getitem__(self, key):
        return Resource(self._composite, key)

    def __bool__(self):
        return bool(self._composite.response.desired.resources)

    def __len__(self):
        return len(self._composite.response.desired.resources)

    def __contains__(self, key):
        return key in self._composite.response.desired.resources

    def __iter__(self):
        for name, resource in self._composite.response.desired.resources:
            yield name, self[name]

    def __setattr__(self, key, resource):
        self[key] = resource

    def __setitem__(self, key, resource):
        self._composite.response.desired.resources[key].resource = resource

    def __delattr__(self, key):
        del self[key]

    def __delitem__(self, key):
        if key in self._composite.response.desired.resources:
            del self._composite.response.desired.resources[key]


class Resource:
    def __init__(self, composite, name):
        self.name = name
        observed = composite.request.observed.resources[name]
        desired = composite.response.desired.resources[name]
        self.observed = observed.resource
        self.desired = desired.resource
        self.conditions = Conditions(observed)
        self.connection = Connection(observed)
        self.unknownsFatal = None
        self.autoReady = None
        self.usages = None

    def __call__(self, apiVersion=_notset, kind=_notset, namespace=_notset, name=_notset):
        self.desired()
        if apiVersion != _notset:
            self.apiVersion = apiVersion
        if kind != _notset:
            self.kind = kind
        if namespace != _notset:
            self.metadata.namespace = namespace
        if name != _notset:
            self.metadata.name = name
        return self

    @property
    def apiVersion(self):
        return self.desired.apiVersion

    @apiVersion.setter
    def apiVersion(self, apiVersion):
        self.desired.apiVersion = apiVersion

    @property
    def kind(self):
        return self.desired.kind

    @kind.setter
    def kind(self, kind):
        self.desired.kind = kind

    @property
    def externalName(self):
        if 'crossplane.io/external-name' in self.metadata.annotations:
            return self.metadata.annotations['crossplane.io/external-name']
        return self.observed.metadata.annotations['crossplane.io/external-name']

    @externalName.setter
    def externalName(self, name):
        self.metadata.annotations['crossplane.io/external-name'] = name

    @property
    def metadata(self):
        return self.desired.metadata

    @metadata.setter
    def metadata(self, metadata):
        self.desired.metadata = metadata

    @property
    def spec(self):
        return self.desired.spec

    @spec.setter
    def spec(self, spec):
        self.desired.spec = spec

    @property
    def data(self):
        return self.desired.data

    @data.setter
    def data(self, data):
        self.desired.data = data

    @property
    def status(self):
        return self.observed.status

    @property
    def ready(self):
        ready = self.desired._parent.ready
        if ready == fnv1.Ready.READY_TRUE:
            return True
        if ready == fnv1.Ready.READY_FALSE:
            return False
        return None

    @ready.setter
    def ready(self, ready):
        if ready:
            ready = fnv1.Ready.READY_TRUE
        elif ready == None or (isinstance(ready, protobuf.Value) and ready._isUnknown):
            ready = fnv1.Ready.READY_UNSPECIFIED
        else:
            ready = fnv1.Ready.READY_FALSE
        self.desired._parent.ready = ready


class Requireds:
    def __init__(self, composite):
        self._composite = composite

    def __getattr__(self, key):
        return self[key]

    def __getitem__(self, key):
        return RequiredResources(self._composite, key)

    def __bool__(self):
        return bool(len(self))

    def __len__(self):
        names = set()
        for name, resource in self._composite.request.extra_resources:
            names.add(name)
        for name, resource in self._composite.response.requirements.extra_resources:
            names.add(name)
        return len(names)

    def __contains__(self, key):
        if key in self._composite.request.extra_resources:
            return True
        if key in self._composite.response.desired.resources:
            return True
        return False

    def __iter__(self):
        names = set()
        for name, resource in self._composite.request.extra_resources:
            names.add(name)
        for name, resource in self._composite.response.requirements.extra_resources:
            names.add(name)
        for name in sorted(names):
            yield name, self[name]


class RequiredResources:
    def __init__(self, composite, name):
        self.name = name
        self._selector = composite.response.requirements.extra_resources[name]
        self._resources = composite.request.extra_resources[name]

    def __call__(self, apiVersion=_notset, kind=_notset, namespace=_notset, name=_notset, labels=_notset):
        self._selector()
        if apiVersion != _notset:
            self.apiVersion = apiVersion
        if kind != _notset:
            self.kind = kind
        if namespace != _notset:
            self.namespace = namespace
        if name != _notset:
            self.matchName = name
        if labels != _notset:
            self.matchLabels = labels
        return self

    @property
    def apiVersion(self):
        return self._selector.api_version

    @apiVersion.setter
    def apiVersion(self, apiVersion):
        self._selector.api_version = apiVersion

    @property
    def kind(self):
        return self._selector.kind

    @kind.setter
    def kind(self, kind):
        self._selector.kind = kind

    @property
    def namespace(self):
        return self._selector.namespace

    @namespace.setter
    def namespace(self, namespace):
        self._selector.namespace = namespace

    @property
    def matchName(self):
        return self._selector.match_name

    @matchName.setter
    def matchName(self, name):
        self._selector.match_name = name

    @property
    def matchLabels(self):
        return self._selector.match_labels.labels

    @matchLabels.setter
    def matchLabels(self, labels):
        self._selector.match_labels.labels()
        if labels:
            for entry in labels:
                if isinstance(entry, str):
                    self._selector.match_labels.labels[entry] = labels[entry]
                elif isinstance(entry, (list, tuple)):
                    self._selector.match_labels.labels[entry[0]] = entry[1]

    def __getitem__(self, ix):
        return RequiredResource(self.name, ix, self._resources.items[ix])

    def __bool__(self):
        return bool(self._resources.items)

    def __len__(self):
        return len(self._resources.items)

    def __iter__(self):
        for ix in range(len(self)):
            yield self[ix]


class RequiredResource:
    def __init__(self, name, ix, resource):
        self.name = name
        self.ix = ix
        self.observed = resource.resource
        self.apiVersion = self.observed.apiVersion
        self.kind = self.observed.kind
        self.metadata = self.observed.metadata
        self.spec = self.observed.spec
        self.data = self.observed.data
        self.status = self.observed.status
        self.conditions = Conditions(resource)

    def __bool__(self):
        return bool(self.observed)


class Conditions:
    def __init__(self, observed, response=None):
        self._observed = observed
        self._response = response

    def __getattr__(self, type):
        return self[type]

    def __getitem__(self, type):
        return Condition(self, type)


class Condition(protobuf.ProtobufValue):
    def __init__(self, conditions, type):
        self._conditions = conditions
        self.type = type

    @property
    def _protobuf_value(self):
        status = self.status
        value = {
            'type': self.type,
            'status': 'Unknown' if status is None else str(status),
            'reason': self.reason or '',
            'message': self.message or '',
        }
        time = self.lastTransitionTime
        if time:
            value['lastTransitionTime'] = time.isoformat().replace('+00:00', 'Z')
        return value

    def __call__(self, reason=_notset, message=_notset, status=_notset, claim=_notset):
        self._find_condition(True)
        if reason != _notset:
            self.reason = reason
        if message != _notset:
            self.message = message
        if status != _notset:
            self.status = status
        if claim != _notset:
            self.claim = claim
        return self

    @property
    def status(self):
        condition = self._find_condition()
        if condition:
            if condition.status in (fnv1.Status.STATUS_CONDITION_TRUE, 'True', True):
                return True
            if condition.status in (fnv1.Status.STATUS_CONDITION_FALSE, 'False', False):
                return False
        return None

    @status.setter
    def status(self, status):
        condition = self._find_condition(True)
        if status:
            condition.status = fnv1.Status.STATUS_CONDITION_TRUE
        elif status == None:
            condition.status = fnv1.Status.STATUS_CONDITION_UNKNOWN
        elif isinstance(status, protobuf.Value) and status._isUnknown:
            condition.status = fnv1.Status.STATUS_CONDITION_UNSPECIFIED
        else:
            condition.status = fnv1.Status.STATUS_CONDITION_FALSE


    @property
    def reason(self):
        condition = self._find_condition()
        if condition:
            return condition.reason
        return None

    @reason.setter
    def reason(self, reason):
        self._find_condition(True).reason = reason

    @property
    def message(self):
        condition = self._find_condition()
        if condition:
            return condition.message
        return None

    @message.setter
    def message(self, message):
        self._find_condition(True).message = message

    @property
    def lastTransitionTime(self):
        for observed in self._conditions._observed.resource.status.conditions:
            if observed.type == self.type:
                time = observed.lastTransitionTime
                if time:
                    return datetime.datetime.fromisoformat(str(time))
        return None

    @property
    def claim(self):
        condition = self._find_condition()
        return condition and condition.target == fnv1.Target.TARGET_COMPOSITE_AND_CLAIM

    @claim.setter
    def claim(self, claim):
        condition = self._find_condition(True)
        if claim:
            condition.target = fnv1.Target.TARGET_COMPOSITE_AND_CLAIM
        elif claim == None or (isinstance(claim, protobuf.Value) and claim._isUnknown):
            condition.target = fnv1.Target.TARGET_UNSPECIFIED
        else:
            condition.target = fnv1.Target.TARGET_COMPOSITE

    def _find_condition(self, create=False):
        if self._conditions._response is not None:
            for condition in self._conditions._response.conditions:
                if condition.type == self.type:
                    return condition
        if not create:
            for observed in self._conditions._observed.resource.status.conditions:
                if observed.type == self.type:
                    return observed
            return None
        if self._conditions._response is None:
            raise ValueError('Condition is read only')
        condition = fnv1.Condition()
        condition.type = self.type
        return self._conditions._response.conditions.append(condition)


class Connection:
    def __init__(self, observed, desired=None):
        self.__dict__['_observed'] = observed
        self.__dict__['_desired'] = desired

    def __bool__(self):
        if self._desired is not None and len(self._desired.connection_details) > 0:
            return True
        if self._observed is not None and len(self._observed.connection_details) > 0:
            return True
        return False

    def __getattr__(self, key):
        return self[key]

    def __getitem__(self, key):
        value = None
        if self._desired is not None and key in self._desired.connection_details:
            value = self._desired.connection_details[key]
        if value is None and key in self._observed.connection_details:
            value = self._observed.connection_details[key]
        return value

    def __setattr__(self, key, value):
        self[key] = value

    def __setitem__(self, key, value):
        if self._desired is None:
            raise ValueError('Connection is read only')
        self._desired.connection_details[key] = value


class Events:
    def __init__(self, response):
        self._results = response.results

    def info(self, reason=_notset, message=_notset, claim=_notset):
        event = Event(self._results.append())
        event.info = True
        if reason != _notset:
            event.reason = reason
        if message != _notset:
            event.message = message
        if claim != _notset:
            event.claim = claim
        return event

    def warning(self, reason=_notset, message=_notset, claim=_notset):
        event = Event(self._results.append())
        event.warning = True
        if reason != _notset:
            event.reason = reason
        if message != _notset:
            event.message = message
        if claim != _notset:
            event.claim = claim
        return event

    def fatal(self, reason=_notset, message=_notset, claim=_notset):
        event = Event(self._results.append())
        event.fatal = True
        if reason != _notset:
            event.reason = reason
        if message != _notset:
            event.message = message
        if claim != _notset:
            event.claim = claim
        return event

    def __bool__(self):
        return len(self) > 0

    def __len__(self):
        len(self._results)

    def __getitem__(self, key):
        if key >= len(self._results):
            return Event()
        return Event(self._results[key])

    def __iter__(self):
        for ix in range(len(self._results)):
            yield self[ix]


class Event:
    def __init__(self, result=None):
        self._result = result

    def __bool__(self):
        return self._result is not None

    @property
    def info(self):
        return bool(self) and self._result.severity == fnv1.Severity.SEVERITY_NORMAL

    @info.setter
    def info(self, info):
        if bool(self):
            if info:
                self._result.severity = fnv1.Severity.SEVERITY_NORMAL
            else:
                self._result.severity = fnv1.Severity.SEVERITY_UNSPECIFIED

    @property
    def warning(self):
        return bool(self) and self._result.severity == fnv1.Severity.SEVERITY_WARNING

    @warning.setter
    def warning(self, warning):
        if bool(self):
            if warning:
                self._result.severity = fnv1.Severity.SEVERITY_WARNING
            else:
                self._result.severity = fnv1.Severity.SEVERITY_NORMAL

    @property
    def fatal(self):
        return bool(self) and self._result.severity == fnv1.Severity.SEVERITY_FATAL

    @fatal.setter
    def fatal(self, fatal):
        if bool(self):
            if fatal:
                self._result.severity = fnv1.Severity.SEVERITY_FATAL
            else:
                self._result.severity = fnv1.Severity.SEVERITY_NORMAL

    @property
    def reason(self):
        return self._result.reason if bool(self) else None

    @reason.setter
    def reason(self, reason):
        if bool(self):
            self._result.reason = reason

    @property
    def message(self):
        return self._result.message if bool(self) else None

    @message.setter
    def message(self, message):
        if bool(self):
            self._result.message = message

    @property
    def claim(self):
        return bool(self) and self._result == fnv1.Target.TARGET_COMPOSITE_AND_CLAIM

    @claim.setter
    def claim(self, claim):
        if bool(self):
            if claim:
                self._result.target = fnv1.Target.TARGET_COMPOSITE_AND_CLAIM
            elif claim == None or (isinstance(claim, protobuf.Value) and claim._isUnknown):
                self._result.target = fnv1.Target.TARGET_UNSPECIFIED
            else:
                self._result.target = fnv1.Target.TARGET_COMPOSITE
