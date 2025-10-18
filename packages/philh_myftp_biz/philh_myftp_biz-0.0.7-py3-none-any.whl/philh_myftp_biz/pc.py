from .db import colors, size
from typing import Literal, Self, Generator
import os, sys

__input = input
__print = print

def NAME():
    from socket import gethostname
    hn = gethostname()
    del gethostname
    return hn

def SERVER_LAN():
    from .web import ping
    p = ping('192.168.1.2')
    del ping
    return p

def OS() -> Literal['windows', 'unix']:
    return {
        True: 'windows',
        False: 'unix'
    } [os.name == 'nt']

class Path:

    def __init__(self, *input):
        from pathlib import Path as libPath, PurePath

        # ==================================

        if len(input) > 1:
            joined: str = os.path.join(*input)
            self.path = joined.replace('\\', '/')

        elif isinstance(input[0], Path):
            self.path = input[0].path

        elif isinstance(input[0], str):
            self.path = libPath(input[0]).absolute().as_posix()

        elif isinstance(input[0], PurePath):
            self.path = input[0].as_posix()

        elif isinstance(input[0], libPath):
            self.path = input[0].as_posix()

        # ==================================

        self.path: str = self.path.replace('\\', '/')
        self.__Path = libPath(self.path)

        self.exists = self.__Path.exists
        self.isfile = self.__Path.is_file
        self.isdir = self.__Path.is_dir

        self.set_access = _set_access(self)

        self.mtime = _mtime(self)

        # ==================================

    def chext(self, ext):

        dst = self.path

        if self.ext():
            dst = dst[:dst.rfind('.')+1] + ext
        else:
            dst += '.' + ext

        if self.exists():
            self.rename(dst)
        
        self.path = dst

    def cd(self):
        if self.isfile():
            return cd(self.parent().path)
        else:
            return cd(self.path)

    def absolute(self):
        return Path(self.__Path.absolute())
    
    def resolute(self):
        return Path(self.__Path.resolve(True))
    
    def child(self, *name):

        if self.isfile():

            raise TypeError("Parent path cannot be a file")
        
        else:

            return Path(self.__Path.joinpath(*name))

    def __str__(self):
        return self.path

    def islink(self):
        return self.__Path.is_symlink() or self.__Path.is_junction()

    def size(self) -> int:
        if self.isfile():
            return os.path.getsize(self.path)

    def children(self) -> Generator[Self]:
        for p in self.__Path.iterdir():
            yield Path(p)

    def descendants(self) -> Generator[Self]:
        for root, dirs, files in self.__Path.walk():
            for item in (dirs + files):
                yield Path(root, item)

    def parent(self):
        return Path(self.__Path.parent)

    def var(self, name, default=None):
        return _var(self, name, default)
    
    def sibling(self, item):
        return self.parent().child(item)
    
    def ext(self):
        ext = os.path.splitext(self.path)[1][1:]
        if len(ext) > 0:
            return ext.lower()

    def type(self):
        from .db import mime_types

        types = mime_types

        if self.isdir():
            return 'dir'

        elif self.ext() in types:
            return types[self.ext()]

    def delete(self):
        from send2trash import send2trash
        from shutil import rmtree

        if self.exists():
            
            self.set_access.full()

            try:
                send2trash(self.path)

            except OSError:

                if self.isdir():
                    rmtree(self.path)
                else:
                    os.remove(self.path)

    def rename(self, dst, overwrite:bool=True):

        src = self
        dst = Path(dst)

        if dst.ext() is None:
            dst.chext(self.ext())
        
        with src.cd():
            try:
                os.rename(src.path, dst.path)
            except FileExistsError as e:
                if overwrite:
                    dst.delete()
                    os.rename(src, dst)
                else:
                    raise e

    def name(self):
        if self.ext():
            return self.path[:self.path.rfind('.')].split('/')[-1]
        else:
            return self.path.split('/')[-1]

    def seg(self, i:int=-1):
        return self.path.split('/') [i]

    def copy(
        self,
        dst: (Self | str)
    ):
        from shutil import copyfile, copytree
        
        dst = Path(dst)

        try:
            
            mkdir(dst.parent())

            if self.isfile():

                if dst.isdir():
                    dst = dst.child( self.seg() )

                if dst.exists():
                    dst.delete()

                copyfile(
                    src = self.path, 
                    dst = dst.path
                )

            else:
                copytree(
                    src = self.path,
                    dst = dst.path,
                    dirs_exist_ok = True
                )

        except Exception as e:
            print('Undoing ...')
            dst.delete()
            raise e

    def move(self, dst):
        self.copy(dst)
        self.delete()

    def inuse(self):
        if self.exists():
            try:
                os.rename(self.path, self.path)
                return False
            except PermissionError:
                return True
        else:
            return False

    def raw(self):
        if self.isfile():
            return self.open('rb').read()
        
    def read(self):
        return self.open().read()
    
    def write(self, value=''):
        self.open('w').write(value)

    def open(self, mode='r'):
        return open(self.path, mode)

def cwd():
    return Path(os.getcwd())

class cd:

    def __enter__(self):
        self.via_with = True

    def __exit__(self, *_):
        if self.via_with:
            self.back()

    def __init__(self, dir):

        self.via_with = False

        self.src = os.getcwd()

        self.dst = Path(dir)
        
        if self.dst.isfile():
            self.dst = self.dst.parent()

        self.open()

    def open(self):
        os.chdir(self.dst.path)

    def back(self):
        os.chdir(self.src.path)

class terminal:
    
    def width():
        from shutil import get_terminal_size
        return get_terminal_size().columns

    def write(text, stream:Literal['out', 'err']='out'):
        from io import StringIO
        stream: StringIO = getattr(sys, 'std'+stream)
        stream.write(text)
        stream.flush()

    def del_last_line():
        cmd = "\033[A{}\033[A"
        spaces = (' ' * terminal.width())
        print(cmd.format(spaces), end='')

    def is_elevated():
        try:
            from ctypes import windll
            return windll.shell32.IsUserAnAdmin()
        except:
            return False
        
    def elevate():
        if not terminal.is_elevated():
            from elevate import elevate
            elevate() # show_console=False

    def dash(p:int=100):
        __print(terminal.width() * (p//100) * '-')

def cls():
    from .text import hex

    __print(hex.encode('*** Clear Terminal ***'))
    os.system('cls')

class power:

    def restart(t:int=30):
        from . import run

        run(
            args = ['shutdown', '/r', '/t', t],
            wait = True
        )

    def shutdown(t:int=30):    
        from . import run
        
        run(
            args = ['shutdown', '/s', '/t', t],
            wait = True
        )

    def abort():
        from . import run
        
        run(
            args = ['shutdown', '/a'],
            wait = True
        )

def print(
    *args,
    pause: bool = False,
    color: colors.names = 'DEFAULT',
    sep: str = ' ',
    end: str = '\n',
    overwrite: bool = False
):
    
    if overwrite:
        end = ''
        terminal.del_last_line()
    
    message = colors.values[color.upper()]
    for arg in args:
        message += str(arg) + sep

    message = message[:-1] + colors.values['DEFAULT'] + end

    if pause:
        input(message)
    else:
        terminal.write(message)

def script_dir(__file__):
    return Path(os.path.abspath(__file__)).parent()

class _mtime:

    def __init__(self, path:Path):
        self.path = path

    def set(self, mtime=None):
        from .time import now
        if mtime:
            os.utime(self.path.path, (mtime, mtime))
        else:
            now = now().unix
            os.utime(self.path.path, (now, now))

    def get(self):
        return os.path.getmtime(self.path.path)
    
    def stopwatch(self):
        from .time import Stopwatch
        SW = Stopwatch()
        SW.start_time = self.get()
        return SW

class _var:

    def __init__(self, file:Path, var, default=None):
        from .text import hex

        self.file = file
        self.default = default

        self.path = file.path + ':' + hex.encode(var)

        file.set_access.full()

    def read(self):
        from .text import hex

        try:
            value = open(self.path).read()
            return hex.decode(value)
        except:
            return self.default
        
    def save(self, value):
        from .text import hex
        m = _mtime(self.file).get()
        
        open(self.path, 'w').write(
            hex.encode(value)
        )
        
        _mtime(self.file).set(m)

class _set_access:

    def __init__(self, path:Path):
        self.path = path

    def __paths(self):

        yield self.path

        if self.path.isdir():
            for path in self.path.descendants():
                yield path
    
    def readonly(self):
        for path in self.__paths():
            path.Path.chmod(0o644)

    def full(self):
        for path in self.__paths():
            path.Path.chmod(0o777)

def mkdir(path:str|Path):
    os.makedirs(str(path), exist_ok=True)

def link(src, dst):

    src = Path(src)
    dst = Path(dst)

    if dst.exists():
        dst.delete()

    mkdir(dst.parent())

    os.link(
        src = src.path,
        dst = dst.path
    )

def relpath(file, root1, root2):
    return Path(

        str(root2),
        
        os.path.relpath(
            str(file),
            str(root1)
        )
    
    )

def relscan(src:Path, dst:Path) -> list[list[Path]]:

    items = []

    def scanner(src_:Path, dst_:Path):
        for item in os.listdir(src.path):

            s = src_.child(item)
            d = dst_.child(item)

            if s.isfile():
                items.append([s, d])

            elif s.isdir():
                scanner(s, d)
            
    scanner(src, dst)
    return items

def warn(exc: Exception):
    from io import StringIO
    from traceback import print_exception
    
    IO = StringIO()

    print_exception(exc, file=IO)
    terminal.write(IO.getvalue(), 'err')

class dots:
    
    def __init__(self, n:int):

        self.n = n
        self.dots = '.'

    def next(self):

        if len(self.dots) >= self.n:
            self.dots = ''

        self.dots += '.'

        return self.dots

def input(prompt, timeout:int=None, default=None):

    if timeout:

        from inputimeout import inputimeout, TimeoutOccurred

        try:
            return inputimeout(prompt=prompt, timeout=timeout)
    
        except TimeoutOccurred:
            return default
        
        finally:
            del inputimeout, TimeoutOccurred
    
    else:
        return __input(prompt)

class process:

    def exceptions():
        from psutil import NoSuchProcess, AccessDenied, ZombieProcess
        
        return (NoSuchProcess, AccessDenied, ZombieProcess, AttributeError)

    def exists(pid:int):
        from psutil import Process
        
        try:
            Process(pid)
            return True
        except process.exceptions():
            return False

    class Process:

        def __init__(self, pid:int):
            from psutil import Process
            
            try:
                self.process = Process(pid)
            except process.exceptions():
                self.process = None

        def stop(self):
            if self.exists():
                self.process.terminate()

        def exists(self):
            try:
                self.process.as_dict()
                return True
            except process.exceptions():
                return False

        def children(self) -> Generator[Self]:
            if self.exists():
                for child in self.process.children(True):
                    if process.exists(child.pid):
                        yield process.Process(child.pid)

        def cores(self, *cores):
            if self.exists():
                self.process.cpu_affinity(cores)

    def __init__(self, id):        
        self.id = id

    def scanner(self):
        if isinstance(self.id, int):
            yield process.Process(self.id)

        elif isinstance(self.id, str):
            from psutil import process_iter
            for proc in process_iter():
                if proc.name().lower() == self.id.lower():
                    yield process.Process(proc.pid)

    def cores(self, *cores):
        for process in self.scanner():
            for child in process.children():
                child.cores(*cores)
            process.cores(*cores)

    def stop(self):
        for process in self.scanner():
            for child in process.children():
                child.stop()
            process.stop()

    def alive(self):
        from .array import generate
        items = generate(self.scanner())
        return len(items) > 0

def is_duplicate(file1, file2):
    data1 = open(file1, 'rb').read()
    data2 = open(file2, 'rb').read()
    return data1 == data2

class duplicates:

    class Group:

        def __init__(self):
            from .array import new
            self.files: list[Path] = new()
            self.duplicates: list[Path] = new()

        def __iadd__(self, path:Path):
            from .array import new
            
            if path not in self.files:
                self.files += [path]

            raw_files = new()

            for file in self.files:
                
                raw = file.raw()

                if raw in raw_files:
                    self.files -= file
                    self.duplicates += file
                else:
                    raw_files += raw

            return self

    def __init__(self):
        from .json import new as jnew
        from .array import new as anew

        self.dirs: list[Path] = anew()
        self.groups: dict[int, duplicates.Group] = jnew()

    def __iadd__(self, dir):
        self.dirs += [Path(dir)]
        return self
    
    def scan(self):

        groups: dict[int, duplicates.Group] = {}

        for dir in self.dirs:
            for file in dir.children():

                if file.size not in self.groups:
                    groups[file.size] = [self.Group()]

                groups[file.size] += [file]

        return groups

    def clean(self):
        groups = self.scan()
        for size, group in groups.items():
            for file in group.duplicates:
                file.delete()

    def file_exists(self, path):
        
        file = Path(path)
        
        groups = self.scan()
        for size, group in groups.items():
            
            if file.size() == int(size):
                group += file
                return file in group.duplicates

class size:

    def to_bytes(string:str):
        from re import search

        match = search(
            r"(\d+(\.\d+)?)\s*([a-zA-Z]+)",
            string.strip()
        )

        value = float(match.group(1))

        unit = match.group(3).upper()
        unit = unit[0] + unit[-1]

        return value * size.conv_factors[unit]

    def from_bytes(
        value: int | float,
        unit: size.units | None = None,
        ndigits: int = sys.maxsize
    ):

        format = lambda unit: round(
            number = (float(value) / size.conv_factors[unit]),
            ndigits = ndigits
        )

        if unit:
            return str(format(unit)) + ' ' + unit
        else:
            r = 0
            for unit in reversed(size.conv_factors):
                r = format(unit)
                if r >= 1:            
                    return str(r) + ' ' + unit

