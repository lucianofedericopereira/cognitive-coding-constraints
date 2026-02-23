# Source : https://github.com/celery/celery/blob/main/celery/app/base.py (line 489)
# License: BSD-3
# Complexity: 6
# Tier   : tier2

def task(self, *args, **opts):
    """Decorator to create a task class out of any callable.

    See :ref:`Task options<task-options>` for a list of the
    arguments that can be passed to this decorator.

    Examples:
        .. code-block:: python

            @app.task
            def refresh_feed(url):
                store_feed(feedparser.parse(url))

        with setting extra options:

        .. code-block:: python

            @app.task(exchange='feeds')
            def refresh_feed(url):
                return store_feed(feedparser.parse(url))

    Note:
        App Binding: For custom apps the task decorator will return
        a proxy object, so that the act of creating the task is not
        performed until the task is used or the task registry is accessed.

        If you're depending on binding to be deferred, then you must
        not access any attributes on the returned object until the
        application is fully set up (finalized).
    """
    if USING_EXECV and opts.get('lazy', True):
        # When using execv the task in the original module will point to a
        # different app, so doing things like 'add.request' will point to
        # a different task instance.  This makes sure it will always use
        # the task instance from the current app.
        # Really need a better solution for this :(
        from . import shared_task
        return shared_task(*args, lazy=False, **opts)

    def inner_create_task_cls(shared=True, filter=None, lazy=True, **opts):
        _filt = filter

        def _create_task_cls(fun):
            if shared:
                def cons(app):
                    return app._task_from_fun(fun, **opts)

                cons.__name__ = fun.__name__
                connect_on_app_finalize(cons)
            if not lazy or self.finalized:
                ret = self._task_from_fun(fun, **opts)
            else:
                # return a proxy object that evaluates on first use
                ret = PromiseProxy(self._task_from_fun, (fun,), opts,
                                   __doc__=fun.__doc__)
                self._pending.append(ret)
            if _filt:
                return _filt(ret)
            return ret

        return _create_task_cls

    if len(args) == 1:
        if callable(args[0]):
            return inner_create_task_cls(**opts)(*args)
        raise TypeError('argument 1 to @task() must be a callable')
    if args:
        raise TypeError(
            '@task() takes exactly 1 argument ({} given)'.format(
                sum([len(args), len(opts)])))
    return inner_create_task_cls(**opts)