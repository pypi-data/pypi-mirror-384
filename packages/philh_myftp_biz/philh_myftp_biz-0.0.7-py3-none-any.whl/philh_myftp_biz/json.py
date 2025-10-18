import json

load = json.load
loads = json.loads
dump = json.dump
dumps = json.dumps

def valid(value:str):
    try:
        loads(value)
        return True
    except json.decoder.JSONDecodeError:
        return False

class new:

    def __init__(self, dict:dict={}):
        from .file import json, pkl, temp
        from .pc import _var

        if isinstance(dict, (json, _var, pkl)):
            self.var = dict

        elif isinstance(dict, new):
            self.var = dict.var

        else:
            self.var = json(
                path = temp('array', 'json'),
                default = dict,
                encode = True
            )

        self.save = self.var.save
        self.read = self.var.read

    def remove(self, item):
        arr = self.read()
        del arr[item]
        self.save(arr)

    def names(self):
        from .array import generate
        return generate(self.read())

    def values(self):
        data = self.read()
        return [data[x] for x in self.names()]

    def inverted(self):
        data = self.read()
        data_ = {}
        for x in data:
            data_[data[x]] = x
        return new(data_)

    def __iter__(self):
        self._names:list = self.names()
        self._values:list = self.values()
        self.x = 0
        return self

    def __next__(self):
        if self.x == len(self._names):
            raise StopIteration
        else:
            name = self._names[self.x]
            value = self._values[self.x]
            self.x += 1
            return name, value

    def __len__(self):
        return len(self.names())
    
    def __getitem__(self, key):
        try:
            return self.read()[key]
        except KeyError:
            return None

    def __setitem__(self, key, value):
        data = self.read()
        data[key] = value
        self.save(data)

    def __delitem__(self, key):
        self.remove(self.read()[key])

    def __contains__(self, value):
        return (value in self.names()) or (value in self.values())
    
    def __iadd__(self, dict):
        data = self.read()
        for name in dict:
            data[name] = dict[name]
        self.save(data)
        return self

    def filtered(self, func=lambda x: x): #TODO
        data = filter(self.read(), func)
        return new(data)
    
    def filter(self, func=lambda x: x): #TODO
        self.save( filter(self.read(), func) )
        return self

    def __str__(self):
        return json.dumps(self.read(), indent=2)
