''' nicely example

    Example uses ot the nicely.dump function.
'''

import collections

from nicely import dump

'''
    The simplest way to use dump is
'''
dump(collections)
'''
    which uses the default parameters and so dumps the argument on stdout and to the 'nicely.dump' file.
'''

'''
    In addition to all the arguments that the nicely.Printer class would accept,
    we can pass to the dump function the name of the destination file.
'''
dump(collections.Counter, name='counter')       # we can use the default ext (dump)
dump(collections.ChainMap, name='chainmap.log') # or specifiy the full name

'''
    if the output on the screen is not wanted, we can set the 'default' parameter to False.
'''
dump(collections, default=False)
'''
    if the name of the destination file is not specified, if will be 'nicely.dump'.
'''
