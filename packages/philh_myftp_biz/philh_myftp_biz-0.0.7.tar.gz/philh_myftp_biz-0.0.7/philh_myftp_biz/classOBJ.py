from .db import colors

class child:

    def __init__(self, parent, name:str):
        
        self.parent = parent
        self.name = name

        self.private = name.startswith('__')

        self.callable = callable(self.value())

        self.empty = (self.value() == None)

    def value(self):
        return getattr(self.parent, self.name)
    
    def __str__(self):
        from json import dumps

        try:
            return dumps(
                obj = self.value(),
                indent = 2
            )
        except:
            return str(self.value())

class new:
    def __init__(self, **args):
        for name in args:
            setattr(self, name, args[name])

def path(obj):
    return obj.__class__.__module__ + '.' + obj.__class__.__qualname__

def children(obj):
    for name in dir(obj):
        yield child(obj, name)

def stringify(obj):

    from io import StringIO
    
    IO = StringIO()

    IO.write('--- ')
    IO.write(path(obj))
    IO.write(' ---\n')

    for c in children(obj):
        if not (c.private or c.callable or c.empty):
            IO.write(c.name)
            IO.write(' = ')
            IO.write(str(c))
            IO.write('\n')

    return IO.getvalue()

def log(obj, color:colors.names='DEFAULT'):
    from pc import print as __print
    
    print()

    __print(
        stringify(obj),
        color = color
    )
    
    print()

def to_json(obj):

    json_obj = {}

    for c in children(obj):
        if not (c.private or c.callable or c.empty):
            json_obj[c.name] = c.value()

    return json_obj
