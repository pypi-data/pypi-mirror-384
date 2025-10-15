"""
Module adding additional functionality to python basic threads in the form of a PropogatingThread.
"""

from threading import Thread

# pylint: disable-next=line-too-long
# implementation based on https://stackoverflow.com/questions/2829329/catch-a-threads-exception-in-the-caller-thread


class PropagatingThread(Thread):
    """
    Class that extends Thread to propogate return results and exception upon joining.
    """

    def __init__(self, target=None, name=None, args=(), kwargs=None):
        """
        Args:
            target: The callable object to be invoked by the run() method. Defaults to None, meaning
             nothing is called.
            name: The thread name. By default, a unique name is constructed of the form "Thread-N"
             where N is a small decimal number.
            args: A list or tuple of arguments for the target invocation. Defaults to ().
            kwargs: A dictionary of keyword arguments for the target invocation. Defaults to {}.
        """
        super().__init__(target=target, name=name, args=args, kwargs=kwargs)
        self.ret = None
        self.exc = None

    def run(self):
        """
        Run function in thread.
        """
        self.exc = None
        try:
            self.ret = self._target(*self._args, **self._kwargs)
        # pylint: disable-next=broad-exception-caught
        except BaseException as e:
            self.exc = e

    def join(self, timeout=None):
        """
        Join thread and either return results from function or reraise exception.

        Args:
            timeout: Maximum time to wait for thread to finish.

        Returns:
             Result of excecuted function.
        """
        super().join(timeout)
        if self.exc:
            raise self.exc
        return self.ret
