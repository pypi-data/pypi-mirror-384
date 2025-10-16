import datetime
import threading

from .. import entities


class BaseServiceRunner:
    _do_reset = False
    _auto_refresh_dtlpy_token = None
    _refresh_dtlpy_token = None
    _threads_terminated = list()
    _threads_terminated_lock = threading.Lock()
    _service_entity = None

    def do_reset(self):
        self._do_reset = True

    @staticmethod
    def ping(progress):
        progress.logger.debug('received ping at: {}'.format(datetime.datetime.now().isoformat()))
        return 'pong'

    def _terminate(self, tid):
        with self._threads_terminated_lock:
            self._threads_terminated.append(tid)

    def kill_event(self):
        ident = threading.get_ident()
        if ident in self._threads_terminated:
            with self._threads_terminated_lock:
                self._threads_terminated.pop(self._threads_terminated.index(ident))
            raise InterruptedError('Execution received termination signal')

    @property
    def service_entity(self) -> entities.Service:
        assert isinstance(self._service_entity, entities.Service), "service_entity must be a dl.Service object"
        return self._service_entity

    @service_entity.setter
    def service_entity(self, value):
        assert isinstance(value, entities.Service), "service_entity must be a dl.Service object"
        self._service_entity = value


class Progress:
    """
    Follow the event progress
    """

    def update(self,
               status=None,
               progress=0,
               message=None,
               output=None,
               duration=None,
               action=None
               ):
        """
        Update the progress flow

        :param str status: the progress status to display
        :param int progress: number of finished flow
        :param str message: the progress message to display
        :param dict output: json serializable object to update the event output
        :param float duration: the event duration
        :param str action: event action
        """
        pass


class ItemStatusEvent:
    def __init__(self, _json: dict):
        if _json is None:
            _json = dict()

        self.pipeline_id = _json.get('pipelineId', None)
        self.node_id = _json.get('nodeId', None)
        self.action = _json.get('action', None)

        status = _json.get('status', dict())
        if status is None:
            status = dict()

        self.task_id = status.get('taskId', None)
        self.assignment_id = status.get('assignmentId', None)
        self.status = status.get('status', None)
        self.creator = status.get('creator', None)
        self.timestamp = status.get('timestamp', None)


class ExecutionEventContext:
    def __init__(self, _json: dict):
        if _json is None:
            _json = dict()

        self.resource = _json.get('resource', None)
        self.source = _json.get('source', None)
        self.action = _json.get('action', None)
        self.resource_id = _json.get('resourceId', None)
        self.user_id = _json.get('userId', None)
        self.dataset_id = _json.get('datasetId', None)
        self.project_id = _json.get('projectId', None)
        self.body = _json.get('body', None)
        self.item_status_event = ItemStatusEvent(_json.get('itemStatusEvent', dict()))


class Context:
    """
    Contex of the service state
    """

    def __init__(
            self,
            service: entities.Service = None,
            package: entities.Package = None,
            project: entities.Project = None,
            event_context: dict = None,
            execution_dict: dict = None,
            progress: Progress = None,
            logger=None,
            sdk=None
    ):
        """
        A Context entity use DTLPY entities for context in a service runner


        :param dict execution_dict: the current execution dict in the state
        :param dict service: the current service entity in th state
        :param dict package: the current package entity in th state
        :param dict project: the current project entity in th state
        :param dict event_context: ExecutionEventContext json display the Execution event context
        :param dl.Progress progress: Progress object for work flow
        :param logger: logger object
        :param sdk: the dtlpy package
        """
        # dtlpy
        self._logger = logger
        self._sdk = sdk
        self._progress = progress

        self.event = ExecutionEventContext(event_context)
        if execution_dict is None:
            execution_dict = dict()
        self.execution_dict = execution_dict

        # ids
        self.trigger_id = execution_dict.get('trigger_id', None)
        self.execution_id = execution_dict.get('id', None)

        # pipeline
        pipeline = execution_dict.get('pipeline', dict())
        if pipeline is None:
            pipeline = dict()
        self.pipeline_id = pipeline.get('id', None)
        self.node_id = pipeline.get('nodeId', None)
        self.pipeline_execution_id = pipeline.get('executionId', None)

        # objects
        self._service = service
        self._package = package
        self._project = project
        self._task = None
        self._assignment = None
        self._pipeline = None
        self._node = None
        self._execution = None
        self._pipeline_execution = None

    @property
    def package(self):
        assert isinstance(self._package, entities.Package), "Missing `package` in context"
        return self._package

    @property
    def project(self):
        assert isinstance(self._project, entities.Project), "Missing `project` in context"
        return self._project

    @property
    def service(self):
        assert isinstance(self._service, entities.Service), "Missing `service` in context"
        return self._service

    @property
    def item_status_creator(self):
        return self.event.item_status_event.creator

    @property
    def item_status(self):
        return self.event.item_status_event.status

    @property
    def item_status_operation(self):
        return self.event.item_status_event.action

    @property
    def execution(self) -> entities.Execution:
        if self._execution is None:
            # noinspection PyProtectedMember
            self._execution = self.sdk.Execution.from_json(
                _json=self.execution_dict,
                client_api=self.service._client_api,
                service=self.service,
                project=self.project
            )
        return self._execution

    @property
    def task_id(self) -> str:
        return self.event.item_status_event.task_id

    @property
    def task(self) -> entities.Task:
        if self._task is None and self.task_id is not None:
            try:
                self._task = self.sdk.tasks.get(task_id=self.task_id)
            except Exception:
                self.logger.exception('Failed to get task')
        return self._task

    @property
    def assignment_id(self) -> str:
        return self.event.item_status_event.assignment_id

    @property
    def assignment(self) -> entities.Assignment:
        if self._assignment is None and self.assignment_id is not None:
            self._assignment = self.sdk.assignments.get(assignment_id=self.assignment_id)
        return self._assignment

    @property
    def pipeline(self) -> entities.Pipeline:
        if self._pipeline is None and self.pipeline_id is not None:
            self._pipeline = self.sdk.pipelines.get(pipeline_id=self.pipeline_id)
        return self._pipeline

    @property
    def node(self):
        if self._node is None and self.pipeline is not None and self.node_id is not None:
            self._node = [n for n in self.pipeline.nodes if n.node_id == self.node_id][0]
        return self._node

    @property
    def pipeline_execution(self):
        if self._pipeline_execution is None and self.pipeline_execution_id is not None:
            self._pipeline_execution = self.sdk.pipeline_executions.get(
                pipeline_execution_id=self.pipeline_execution_id,
                pipeline_id=self.pipeline_id
            )
        return self._pipeline_execution

    @property
    def sdk(self):
        if self._sdk is None:
            import dtlpy
            self._sdk = dtlpy
        return self._sdk

    @property
    def logger(self):
        if self._logger is None:
            import logging
            self._logger = logging.getLogger("[AgentContext]")
        return self._logger
