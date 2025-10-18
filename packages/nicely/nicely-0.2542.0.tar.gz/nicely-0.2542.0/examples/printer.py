''' nicely example

    Example uses of the nicely.Printer class.
'''

import collections

from nicely import Printer

'''
    The simplest way to use Printer.print is
'''
p = Printer()
p.print(collections)

'''
    or
'''
pp = Printer().print
pp(collections)

'''
    of course, we can change the config
'''
p = Printer(max_lines=33, max_map=33)
p.print(collections)

'''
    or the destination
'''
with open('collections', 'w') as out:
    pp = Printer(max_map=33, max_lines=33, target=out).print
    pp(collections.Counter)
    pp(collections.ChainMap)
