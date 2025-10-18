'''
    Data type Formaters.

    All Formaters must be derived from Formater.
'''

from types import ModuleType


#pylint: disable=invalid-name


class Formatter:
    ''' Base class for all Formaters. '''

    def __init__(self, obj):
        # The object to be formated.
        self.obj = obj

    def validate(self):
        '''
            Must be implemented by subclasses
            Should retun True if self.obj can be handled by this class.
        '''
        raise NotImplementedError

    def __print__(self, printer):
        '''
            Must be implemented by subclasses
            Call printer's methods appropriatly to get the desired result.
        '''
        raise NotImplementedError


'''
    Default Formaters for built-in container types and namespaces.
'''


class Tuple_formatter(Formatter):

    def validate(self):
        return isinstance(self.obj, tuple)

    def __print__(self, printer):
        with printer.brackets('(', ')'):
            printer.print_seq(self.obj)


class List_formatter(Formatter):

    def validate(self):
        return isinstance(self.obj, list)

    def __print__(self, printer):
        with printer.brackets('[', ']'):
            printer.print_seq(self.obj)


class Iter_formatter(List_formatter):

    def validate(self):
        return hasattr(self.obj, '__iter__') and not isinstance(self.obj, str)


class Dict_formatter(Formatter):

    def validate(self):
        return isinstance(self.obj, dict)

    def __print__(self, printer):
        with printer.brackets('{', '}'):
            printer.print_map(self.obj.items())


class Namedtuple_formatter(Formatter):

    def validate(self):
        return isinstance(self.obj, tuple) and getattr(self.obj, '_fields', False)

    def __print__(self, printer):
        with printer.brackets('(', ')'):
            printer.print_map(list(zip(self.obj._fields, self.obj)))


class Set_formatter(Formatter):

    def validate(self):
        return isinstance(self.obj, set)

    def __print__(self, printer):
        with printer.brackets('{', '}'):
            printer.print_seq(self.obj)


class Frozenset_formatter(Formatter):

    def validate(self):
        return isinstance(self.obj, frozenset)

    def __print__(self, printer):
        with printer.brackets('{', '}'):
            printer.print_seq(self.obj)


class Module_formatter(Formatter):

    def validate(self):
        if isinstance(self.obj, ModuleType):
            self.name = self.obj.__name__
            self.op_bk = 'module:%s<' % self.name
            self.cl_bk = '>'
            return True
        return False

    def __print__(self, printer):
        exclude = '__builtins__',
        items = {}
        for name in dir(self.obj):
            if name in exclude:
                continue
            else:
                val = getattr(self.obj, name)
                if isinstance(val, ModuleType):
                    if val.__name__.startswith(self.name):
                        items[name] = val
                elif isinstance(val, type):
                    if val.__module__.startswith(self.name):
                        items[name] = val
                else:
                    items[name] = val
        with printer.brackets(self.op_bk, self.cl_bk):
            printer.print_map(items.items())


class Class_formatter(Formatter):

    def validate(self):
        exclude = 'object', 'type'
        if isinstance(self.obj, type):
            name = self.obj.__name__
            if name in exclude:
                return False
            self.op_bk = 'class:%s<' % name
            self.cl_bk = '>'
            return True
        return False

    def __print__(self, printer):
        exclude = '__abstractmethods__', '__dict__', '__weakref__', '__new__', '__subclasshook__'
        nontypes = (
            'wrapper_descriptor', 'method_descriptor', 'member_descriptor',
            'getset_descriptor', 'BuiltinFunctionType', 'BuiltinMethodType',
        )
        items = {}
        for name in dir(self.obj):
            if name in exclude:
                continue
            else:
                val = getattr(self.obj, name)
                if type(val).__name__ in nontypes:
                    continue
                elif isinstance(val, type):
                    if val.__module__.startswith(self.obj.__module__):
                        items[name] = val
                else:
                    items[name] = val
        with printer.brackets(self.op_bk, self.cl_bk):
            printer.print_map(items.items())
