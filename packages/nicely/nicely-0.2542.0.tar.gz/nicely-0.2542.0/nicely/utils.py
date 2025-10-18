'''
    Utility classes.
'''

from contextlib import contextmanager


class State:
    ''' Save state on enter and restore it on exit '''

    def __init__(self, value):
        self.value = value

    @contextmanager
    def _cm(self, val):
        bak = self.value
        self.value = val
        yield
        self.value = bak

    def __call__(self, val):
        return self._cm(val)

    def __bool__(self):
        return bool(self.value)


class Stack:
    ''' Push a value on enter and pop it on exit'''

    def __init__(self):
        self._stack = []

    @contextmanager
    def _cm(self, val):
        self._stack.append(val)
        yield
        self._stack.pop()

    def __call__(self, val):
        return self._cm(val)

    def __len__(self):
        return len(self._stack)

    @property
    def last(self):
        return self._stack[-1]
