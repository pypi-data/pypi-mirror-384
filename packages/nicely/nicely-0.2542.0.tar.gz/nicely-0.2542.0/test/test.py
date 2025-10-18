'''
    nicely tests.
'''
from util import check


check('test',
'''test
''')


check('test1\ntest2',
"""'''
    test1
    test2
'''
""")


check('test1\ntest2\ntest3\ntest4',
"""'''
    test1
    test2
    test3
    ... 4
'''
""",
max_lines = 2,
)


check('test 123456789',
'''test 1234 ...
''',
max_str = 13,
)


check('test1\ntest23456789\ntest3\ntest4\ntest5',
"""'''
    test1
    test23456 ...
    test3
    ... 5
'''
""",
max_lines = 2, max_str = 13,
)


check([3, 2, 1],
'''[
    1,
    2,
    3,
]
''',
sort = True,
)


check([3, 2, 1],
'''[
    3,
    2,
    1,
]
''',
sort = False,
)


check([3, 'a', 1],
'''[
    3,
    a,
    1,
]
''')


check([3, 'a\nb', 1],
"""[
    3,
    '''
        a
        b
    ''',
    1,
]
""")


check([1,[2],3],
'''[
    1,
    [
        2,
    ],
    3,
]
''')


check([1,2,[4,3],5,6],
'''[
    1,
    2,
    [
        3,
        4,
    ],
    5,
    6,
]
''',
sort = True,
)


check([1,2,[4,3],5,6],
'''[
    1,
    2,
    [
        4,
        3,
    ],
    5,
    6,
]
''',
sort = False,
)


check([1,2,[4,3],5,6],
'''[
    1,
    2,
    [
        3,
        4,
    ],
    ... 5
]
''',
max_seq = 2, sort = True,
)


check(dict(a=1, bb=2, ccc=3, d=4, e=5),
'''{
      a = 1,
     bb = 2,
    ccc = 3,
      d = 4,
      e = 5,
}
''',
sort = True,
)


check(dict(a=1, bb=2, ccc=3, d=4, e=5),
'''{
      a = 1,
     bb = 2,
    ccc = 3,
    ... 5
}
''',
max_map = 2, sort = True,
)


check(dict(a=1, bb=2, ccc=3, dddd=4, eeeee=5),
'''{
      a = 1,
     bb = 2,
    ccc = 3,
    ... 5
}
''',
max_map = 2, sort = True,
)


check(dict(a=1, bb=dict(d=9, eeeee=8), ccc=3),
'''{
      a = 1,
     bb = {
            d = 9,
        eeeee = 8,
    },
    ccc = 3,
}
''',
sort = True,
)


check(dict(a=1, bb=[9, 8], ccc=3),
'''{
      a = 1,
     bb = [
        8,
        9,
    ],
    ccc = 3,
}
''',
sort = True,
)


check(dict(a=1, bb=[9, 8], ccc='''foo\nbar'''),
"""{
      a = 1,
     bb = [
        8,
        9,
    ],
    ccc = '''
        foo
        bar
    ''',
}
""",
sort = True
)


check([1, 2, dict(a=3, b=4), 5, 6],
'''[
    1,
    2,
    {
        a = 3,
        b = 4,
    },
    5,
    6,
]
''',
sort = True,
)


check([1, 2, dict(f=(999, 888, 777), a=3, bbb=4, c=dict(dddd=5, e=6)), 7, 8],
'''[
    1,
    2,
    {
          a = 3,
        bbb = 4,
          c = {
            dddd = 5,
               e = 6,
        },
          f = (
            777,
            888,
            999,
        ),
    },
    7,
    8,
]
''',
sort = True,
)


check([1, 2, dict(f=(999, 888, 777), a=3, bbb=4, c=dict(dddd=5, e=6)), 7, 8],
'''[
    1,
    2,
    {
          a = 3,
        bbb = 4,
        ... 4
    },
    ... 5
]
''',
max_seq = 2, max_map = 1, sort = True,
)


from collections import namedtuple

nt = namedtuple('test', 'foo_bar baz')
check(nt(2, 3),
'''(
        baz = 3,
    foo_bar = 2,
)
''',
sort = True,
)


nt2 = namedtuple('test2', 'foo bar baz')
check(nt2(2, 3, 5),
'''(
    bar = 3,
    baz = 5,
    foo = 2,
)
''',
sort = True,
)


check(nt2(2, 3, 5),
'''(
    bar = 3,
    foo = 2,
)
''',
sort = True, ignore='baz',
)


check(set((1, 5, frozenset((3, 2, 1)), 2, 6)),
'''{
    1,
    2,
    5,
    6,
    {
        1,
        2,
        3,
    },
}
''',
sort = True,
)


check(frozenset((1, 5, 2, 6)),
'''{
    1,
    2,
    5,
    6,
}
''',
sort = True,
)


check(frozenset('1 2 3 4 5 6 7 9'.split()),
'''{
    1,
    2,
    3,
    4,
    ... 8
}
''',
max_seq = 3, sort = True,
)


check(dict(abc=3, abd=6, cab=9, cba=8, cbc=7),
'''{
    cab = 9,
    cba = 8,
    cbc = 7,
}
''',
sort = True, ignore = r'ab.*',
)


check(dict(abc=3, bad=6, cab=9, cba=8, cbc=7),
'''{
    cab = 9,
}
''',
sort = True, ignore = (r'.*bc', r'.*ba'),
)


check([1,2,3,[4,5,6]],
'''[
|-->1,
|-->2,
|-->3,
|-->[
|-->|-->4,
|-->|-->5,
|-->|-->6,
|-->],
]
''',
indent = '|-->',
)


class Test_0:
    '''Printer Test Class'''
    def __init__(self):
        self.data = '''
            Foo
            Bar
            Ham
            Baz
        '''.split()
    def __print__(self, printer):
        with printer.brackets('<<<', '>>>'):
            printer.print(self.data)


check(Test_0(),
"""<<<
    [
        Bar,
        Baz,
        Foo,
        Ham,
    ]
>>>
""",
sort = True,
)


class Test_1:
    def __init__(self):
        self.data = '''
            Foo
            Bar
            Ham egg spam
            Baz
        '''
    def __print__(self, printer):
        with printer.brackets('<<<', '>>>'):
            printer.print(self.data)


check(Test_1(),
"""<<<
    '''
        Foo
        Bar
        Ham egg spam
        Baz
    '''
>>>
""")


check([123, Test_1(), 456],
"""[
    123,
    <<<
        '''
            Foo
            Bar
            Ham egg spam
            Baz
        '''
    >>>,
    456,
]
""")


class Test_1b:
    def __init__(self):
        self.data = ('''
            Foo
            Bar
            Ham egg spam
            Baz
        ''',
        333,
        )
    def __print__(self, printer):
        with printer.brackets('{{', '}}'):
            printer.print(self.data)


check(Test_1b(),
"""{{
    (
        '''
            Foo
            Bar
            Ham egg spam
            Baz
        ''',
        333,
    )
}}
""")


check(Test_1b(),
"""Test_1b:{{
    tuple:(
        str:'''
            Foo
            Bar
            Ham egg spam
            Baz
        ''',
        int:333,
    )
}}
""",
types = True)


class Test_2:
    def __init__(self):
        self.data = [
            8,
            7,
            'foo bar',
            nt(33, 42),
            set((3.3, 42)),
            3,
            [7, 8, {5:6,8:9}, 9],
            [45, 78, 12, 33],
            Test_1(),
            dict(a=3, b=7, c=Test_1(), d=[3,6,Test_1(),9], e=dict(ebbbbbb=6, ec=4, eaa=3.3)),
        ]
    def __print__(self, printer):
        printer.print(self.data)


check(Test_2(),
"""[
    8,
    7,
    foo bar,
    (
            baz = 42,
        foo_bar = 33,
    ),
    {
        3.3,
        42,
    },
    3,
    [
        7,
        8,
        {
            5 = 6,
            8 = 9,
        },
        9,
    ],
    [
        12,
        33,
        45,
        78,
    ],
    <<<
        '''
            Foo
            Bar
            Ham egg spam
            Baz
        '''
    >>>,
    {
        a = 3,
        b = 7,
        c = <<<
            '''
                Foo
                Bar
                Ham egg spam
                Baz
            '''
        >>>,
        d = [
            3,
            6,
            <<<
                '''
                    Foo
                    Bar
                    Ham egg spam
                    Baz
                '''
            >>>,
            9,
        ],
        e = {
                eaa = 3.3,
            ebbbbbb = 6,
                 ec = 4,
        },
    },
]
""",
sort = True,
)


check(Test_2(),
"""list:[
    int:8,
    int:7,
    str:foo bar,
    test:(
            str:baz = int:42,
        str:foo_bar = int:33,
    ),
    set:{
        float:3.3,
        int:42,
    },
    int:3,
    list:[
        int:7,
        int:8,
        dict:{
            int:5 = int:6,
            int:8 = int:9,
        },
        int:9,
    ],
    list:[
        int:12,
        int:33,
        int:45,
        int:78,
    ],
    Test_1:<<<
        str:'''
            Foo
            Bar
            Ham egg spam
            Baz
        '''
    >>>,
    dict:{
        str:a = int:3,
        str:b = int:7,
        str:c = Test_1:<<<
            str:'''
                Foo
                Bar
                Ham egg spam
                Baz
            '''
        >>>,
        str:d = list:[
            int:3,
            int:6,
            Test_1:<<<
                str:'''
                    Foo
                    Bar
                    Ham egg spam
                    Baz
                '''
            >>>,
            int:9,
        ],
        str:e = dict:{
                str:eaa = float:3.3,
            str:ebbbbbb = int:6,
                 str:ec = int:4,
        },
    },
]
""",
types = True, sort = True,
)


check('',
'''""
''')


check([''],
'''[
    "",
]
''')


check(['', 'a'],
'''[
    "",
    a,
]
''')


check([],
'''[
]
''')


check((),
'''(
)
''')


check({},
'''{
}
''')


check(dict(test='name'),
'''{
    test = name,
}
''',
name = 'test.name',
)


check(Test_0,
'''class:Test_0<
                  __doc__ = Printer Test Class,
          __firstlineno__ = 404,
                 __init__ = <function Test_0.__init__  ...,
        __init_subclass__ = <built-in method __init_su ...,
               __module__ = __main__,
                __print__ = <function Test_0.__print__ ...,
    __static_attributes__ = (
        data,
    ),
>
''',
max_str = 30, sort = True,
)


def check_math():
    import math
    check(math,
"""module:math<
    __doc__  = '''
        This module is always available.  It provides access to the
        mathematical functions defined by the C standard.
    ''',
       __name__ = math,
    __package__ = "",
      __spec__  = ModuleSpec(name='math', loader=<class '_frozen_importlib.BuiltinImporter'>,  ...,
           acos = <built-in function acos>,
          acosh = <built-in function acosh>,
          asin  = <built-in function asin>,
          asinh = <built-in function asinh>,
           atan = <built-in function atan>,
          atan2 = <built-in function atan2>,
          atanh = <built-in function atanh>,
           ceil = <built-in function ceil>,
       copysign = <built-in function copysign>,
            cos = <built-in function cos>,
           cosh = <built-in function cosh>,
        degrees = <built-in function degrees>,
              e = 2.718281828459045,
    ... 53
>
""",
        max_map = 16, max_str = 80, sort = True,
    )


    check(math,
"""module:math<
         atan = <built-in function atan>,
        atan2 = <built-in function atan2>,
        atanh = <built-in function atanh>,
         ceil = <built-in function ceil>,
     copysign = <built-in function copysign>,
      degrees = <built-in function degrees>,
            e = 2.718281828459045,
          erf = <built-in function erf>,
         erfc = <built-in function erfc>,
          exp = <built-in function exp>,
        expm1 = <built-in function expm1>,
         fabs = <built-in function fabs>,
    factorial = <built-in function factorial>,
        floor = <built-in function floor>,
         fmod = <built-in function fmod>,
        frexp = <built-in function frexp>,
         fsum = <built-in function fsum>,
    ... 53
>
""",
        max_map = 26, max_str = 80, sort = True, ignore = (r'__.*__', r'.*(sin|cos).*',),
    )


print(' ok')
