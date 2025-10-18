'''
    Nice Printer
'''

from contextlib import contextmanager
from operator import itemgetter
from sys import stdout
import re

from .utils import State, Stack
#pylint: disable=wildcard-import,unused-wildcard-import
from .formatters import *


#pylint: disable=unused-variable


#pylint: disable=too-many-instance-attributes
class Printer:
    ''' Fancy Printer

    Dump an arbritrary data structure to a file-like destination.
    '''

    # One formater is needed for each supported type.
    # Strings don't need a Formater as there're handled directly by the Printer.
    # User Formaters may be added or inserted.
    # Watch the order, the first matching Formater will be used.
    formatters = [
        Namedtuple_formatter,
        Tuple_formatter,
        List_formatter,
        Dict_formatter,
        Set_formatter,
        Frozenset_formatter,
        Iter_formatter,
        Module_formatter,
        Class_formatter,
    ]
    # All formatters must subclass Formatter
    assert all(issubclass(f, Formatter) for f in formatters)

    #pylint: disable=too-many-arguments,line-too-long
    def __init__(self, sort=True, types=False, max_seq=9, max_map=9, max_str=77, max_lines=9, max_depth=9, ignore=None, indent=None, target=stdout):
        self.sort = sort                  # if True: sequences will be sorted (if possible)
        self.max_seq = max_seq            # max items in sequence
        self.max_map = max_map            # max items in mapping
        self.max_str = max(max_str-4, 4)  # max string length (at least 4)
        self.max_lines = max_lines        # max lines in multi-lines string
        self.max_depth = max_depth        # max structure depth
        self.ignore = ignore or []        # keys to ignore in mappings
        self.indent = indent or '    '    # indentation string
        self.target = target.write        # output destination
        self.types = State(types)         # if True: data types will be shown
        ignore = [self.ignore] if isinstance(self.ignore, str) else self.ignore
        self._ignore = [re.compile(r).match for r in ignore]
        self._indent = State(True)
        self._inline = State(False)
        self._width = State(1)
        self._align = State('')
        self._stack = Stack()
        self._level = 0

    def wrap(self, obj):
        # Wrap obj with the appropriate Formatter.
        #pylint: disable=invalid-name,redefined-outer-name
        for Formatter in self.formatters:
            formatter = Formatter(obj)
            if formatter.validate():
                return formatter
        return obj

    @contextmanager
    def brackets(self, op_bk, cl_bk):
        # Handle opening and closing tags.
        if self.types:
            parent = self._stack.last
            typ = type(parent.obj) if isinstance(parent, Formatter) else type(parent)
            typ = typ.__name__ + ':'
        else:
            typ = ''
        with self.types(False), self._inline(False):
            self.print_obj(typ + op_bk)
        self._level += 1
        with self._indent(True), self._inline(False):
            yield
        self._level -= 1
        with self.types(False), self._indent(True):
            self.print_obj(cl_bk)

    def print_obj(self, arg=''):
        # Main printing method.
        arg = self.wrap(arg)
        if hasattr(arg, '__print__'):  # That's a Formatter.
            with self._stack(arg):
                arg.__print__(self)
        else:
            ind = self.indent*self._level if self._indent else ''
            typ = f'{type(arg).__name__}:' if self.types else ''
            pad = self._width.value
            sid = self._align.value
            ret = '' if self._inline else '\n'
            arg = str(arg)
            if len(arg) > self.max_str:
                arg = f'{arg[:self.max_str]} ...'
            val = typ + arg
            self.target(f'{ind}{val:{sid}{pad}}{ret}')

    def print_str_obj(self, arg=''):
        # Send arg to the appropriate handler.
        #pylint: disable=expression-not-assigned
        self.print_str(arg) if isinstance(arg, str) else self.print_obj(arg)

    @contextmanager
    def trailing_comma(self):
        # add a comma a the end of a line in a sequence.
        with self._inline(True):
            yield
        with self._indent(False), self._inline(False), self.types(False):
            self.print_obj(',')

    def check_depth(self):
        # Limit output to max_depth.
        if len(self._stack) > self.max_depth:
            with self.types(False), self._inline(False):
                self.print_obj('...')
            return False
        return True

    def sort_seq(self, seq):
        # sort seq if needed and possible.
        seq = list(seq)
        if self.sort:
            try:
                seq.sort()
            except TypeError: pass
        return seq

    def limit(self, seq, lim):
        # check the limits.
        for cpt, item in enumerate(seq):
            if cpt > lim:
                with self.types(False), self._inline(False):
                    self.print_obj(f'... {len(seq)}')
                break
            yield item

    def print_seq(self, seq):
        # Handle sequences.
        if not self.check_depth(): return
        seq = self.sort_seq(seq)
        for item in self.limit(seq, self.max_seq):
            with self.trailing_comma():
                self.print_str_obj(item)

    def print_map(self, items):
        # Handle mappings.
        if not items: return
        if not self.check_depth(): return
        items = self.sort_seq(items)
        #pylint: disable=bad-builtin
        if self.types:
            def type_arg(arg): return f'{type(arg).__name__}:{arg}'
            width = max(map(len, map(type_arg, map(itemgetter(0), items[:self.max_map+1]))))
        else:
            width = max(map(len, map(str, map(itemgetter(0), items[:self.max_map+1]))))
        for key, val in self.limit(items, self.max_map):
            if any(match(key) for match in self._ignore):
                continue
            with self.trailing_comma():
                with self._width(width):
                    with self._align('>'):
                        self.print_obj(key)
                with self._indent(False):
                    with self.types(False):
                        self.print_obj(' = ')
                    self.print_str_obj(val)

    def print_str(self, arg):
        # Handle strings.
        lines = [lin for lin in (line.strip() for line in arg.split('\n')) if lin]
        if len(lines) > 1:
            with self._stack(arg), self.brackets("'''", "'''"):
                for line in self.limit(lines, self.max_lines):
                    with self._inline(False), self.types(False):
                        self.print_obj(line)
        else:
            self.print_obj(lines[0] if lines else '""')

    def print(self, arg):
        # Entry point.
        self._indent.value = True
        self.print_str_obj(arg)
