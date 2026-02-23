# Source : https://github.com/tornadoweb/tornado/blob/master/tornado/ioloop.py (line 682)
# License: Apache-2.0
# Complexity: 3
# Tier   : tier1

def add_future(
    self,
    future: "Union[Future[_T], concurrent.futures.Future[_T]]",
    callback: Callable[["Future[_T]"], None],
) -> None:
    """Schedules a callback on the ``IOLoop`` when the given
    `.Future` is finished.

    The callback is invoked with one argument, the
    `.Future`.

    This method only accepts `.Future` objects and not other
    awaitables (unlike most of Tornado where the two are
    interchangeable).
    """
    if isinstance(future, Future):
        # Note that we specifically do not want the inline behavior of
        # tornado.concurrent.future_add_done_callback. We always want
        # this callback scheduled on the next IOLoop iteration (which
        # asyncio.Future always does).
        #
        # Wrap the callback in self._run_callback so we control
        # the error logging (i.e. it goes to tornado.log.app_log
        # instead of asyncio's log).
        future.add_done_callback(
            lambda f: self._run_callback(functools.partial(callback, f))
        )
    else:
        assert is_future(future)
        # For concurrent futures, we use self.add_callback, so
        # it's fine if future_add_done_callback inlines that call.
        future_add_done_callback(future, lambda f: self.add_callback(callback, f))