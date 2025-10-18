''' nicely example

    This module shows how to implement the __print__ function to make objects "printable".
'''

from nicely.formatters import Formatter
from nicely.printer import Printer
from nicely import dump

'''
    Let's say that we want to make the following classes "printable".
'''

class Element:
    tag = ''
    def __init__(self, text):
        self.text = text
    @property
    def opening(self):
        return '<%s>'%self.tag
    @property
    def closing(self):
        return '</%s>'%self.tag

class Section(Element):
    def __init__(self, *elements):
        self.elements = elements

'''
    For the Printer to be able to handle our classes
    we need to define a formatter for each one of them.
'''
class Element_formatter(Formatter):
    def validate(self):
        return isinstance(self.obj, Element)
    def __print__(self, printer):
        with printer.brackets(self.obj.opening, self.obj.closing):
            printer.print(self.obj.text)

class Section_formatter(Formatter):
    def validate(self):
        return isinstance(self.obj, Section)
    def __print__(self, printer):
        with printer.brackets(self.obj.opening, self.obj.closing):
            for e in self.obj.elements:
                printer.print(e)

'''
    We add our custom formatters to the Printer's ones.
    Note that as we use isinstance to 'validate',
    the order in which the formatters are appened is important.
'''
Printer.formatters.append(Section_formatter)
Printer.formatters.append(Element_formatter)

'''
    Now we can instanciate our custon classes,
    they will be handled by the Printer as expected.
'''

class Title(Element): tag = 'title'

class P(Element): tag = 'p'

class Head(Section): tag = 'head'

class Body(Section): tag = 'body'

class Html(Section): tag = 'html'

html = Html(
    Head(
        Title('Title'),
    ),
    Body(
        P('First para'),
        P('Second one'),
    ),
)

dump(html)
