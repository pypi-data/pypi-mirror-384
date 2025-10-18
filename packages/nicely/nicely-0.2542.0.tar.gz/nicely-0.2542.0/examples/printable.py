''' nicely example

    This module shows how to implement the '__print__' method to make objects "printable".
'''

from nicely import dump

'''
    We need to define a '__print__' method for each class that we want to 'dump'.
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
    def __print__(self, printer):
        with printer.brackets(self.opening, self.closing):
            printer.print(self.text)

class Section(Element):
    def __init__(self, *elements):
        self.elements = elements
    def __print__(self, printer):
        with printer.brackets(self.opening, self.closing):
            for e in self.elements:
                printer.print(e)

'''
    Now we can instanciate our classes, and 'dump' them.
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
