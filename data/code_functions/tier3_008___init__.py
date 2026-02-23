# Source : https://github.com/celery/celery/blob/main/celery/app/base.py (line 317)
# License: BSD-3
# Complexity: 17
# Tier   : tier3

def __init__(self, main=None, loader=None, backend=None,
             amqp=None, events=None, log=None, control=None,
             set_as_current=True, tasks=None, broker=None, include=None,
             changes=None, config_source=None, fixups=None, task_cls=None,
             autofinalize=True, namespace=None, strict_typing=True,
             **kwargs):

    self._local = threading.local()
    self._backend_cache = None

    self.clock = LamportClock()
    self.main = main
    self.amqp_cls = amqp or self.amqp_cls
    self.events_cls = events or self.events_cls
    self.loader_cls = loader or self._get_default_loader()
    self.log_cls = log or self.log_cls
    self.control_cls = control or self.control_cls
    self._custom_task_cls_used = (
        # Custom task class provided as argument
        bool(task_cls)
        # subclass of Celery with a task_cls attribute
        or self.__class__ is not Celery and hasattr(self.__class__, 'task_cls')
    )
    self.task_cls = task_cls or self.task_cls
    self.set_as_current = set_as_current
    self.registry_cls = symbol_by_name(self.registry_cls)
    self.user_options = defaultdict(set)
    self.steps = defaultdict(set)
    self.autofinalize = autofinalize
    self.namespace = namespace
    self.strict_typing = strict_typing

    self.configured = False
    self._config_source = config_source
    self._pending_defaults = deque()
    self._pending_periodic_tasks = deque()

    self.finalized = False
    self._finalize_mutex = threading.RLock()
    self._pending = deque()
    self._tasks = tasks
    if not isinstance(self._tasks, TaskRegistry):
        self._tasks = self.registry_cls(self._tasks or {})

    # If the class defines a custom __reduce_args__ we need to use
    # the old way of pickling apps: pickling a list of
    # args instead of the new way that pickles a dict of keywords.
    self._using_v1_reduce = app_has_custom(self, '__reduce_args__')

    # these options are moved to the config to
    # simplify pickling of the app object.
    self._preconf = changes or {}
    self._preconf_set_by_auto = set()
    self.__autoset('broker_url', broker)
    self.__autoset('result_backend', backend)
    self.__autoset('include', include)

    for key, value in kwargs.items():
        self.__autoset(key, value)

    self._conf = Settings(
        PendingConfiguration(
            self._preconf, self._finalize_pending_conf),
        prefix=self.namespace,
        keys=(_old_key_to_new, _new_key_to_old),
    )

    # - Apply fix-ups.
    self.fixups = set(self.builtin_fixups) if fixups is None else fixups
    # ...store fixup instances in _fixups to keep weakrefs alive.
    self._fixups = [symbol_by_name(fixup)(self) for fixup in self.fixups]

    if self.set_as_current:
        self.set_current()

    # Signals
    if self.on_configure is None:
        # used to be a method pre 4.0
        self.on_configure = Signal(name='app.on_configure')
    self.on_after_configure = Signal(
        name='app.on_after_configure',
        providing_args={'source'},
    )
    self.on_after_finalize = Signal(name='app.on_after_finalize')
    self.on_after_fork = Signal(name='app.on_after_fork')

    # Boolean signalling, whether fast_trace_task are enabled.
    # this attribute is set in celery.worker.trace and checked by celery.worker.request
    self.use_fast_trace_task = False

    self.on_init()
    _register_app(self)