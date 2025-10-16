from types import TracebackType


def _shrink_down(self, collect=True):
    class Noop:
        def __enter__(self):
            pass

        def __exit__(
            self, exc_type: type, exc_val: Exception, exc_tb: TracebackType
        ) -> None:
            pass

    resource = self._resource
    # Items to the left are last recently used, so we remove those first.
    with getattr(resource, "mutex", Noop()):
        # keep in mind the dirty resources are not shrinking
        while (
            len(resource.queue)
            and (len(resource.queue) + len(self._dirty)) > self.limit
        ):
            if isinstance(resource.queue, list):
                # list does not support .popleft() so we use .pop(0)
                R = resource.queue.pop(0)
            else:
                R = resource.queue.popleft()

            if collect:
                self.collect_resource(R)
