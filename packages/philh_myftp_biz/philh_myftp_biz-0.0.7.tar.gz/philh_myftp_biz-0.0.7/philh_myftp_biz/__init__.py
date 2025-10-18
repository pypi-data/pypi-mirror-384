
# =====================================

from typing import Literal

from . import (
    array,
    classOBJ,
    db,
    file,
    json,
    modules,
    num,
    pc,
    text,
    time,
    web
)

# =====================================

# Declare Modules (Only for specific systems)
PC = modules.Module('PC')
AD = modules.Module('AD')
AI = modules.Module('AI')
Ffmpeg = modules.Module('Ffmpeg')
Minecraft = modules.Module('Minecraft')
Package = modules.Module('Package')
Plex = modules.Module('Plex')
VMs = modules.Module('VMs')
Website = modules.Module('Website')
YouTube = modules.Module('YouTube')

# =====================================

def args():
    from sys import argv
    from .text import auto_convert

    out = []

    for a in argv:
        out += [auto_convert(a)]

    return out

def waitfor(func):
    from .time import sleep

    while not func():
        sleep(.1)

def var(title, default='', temp=False):
    from .file import temp, cache, pkl
    from .text import hex

    args = 'var', 'pkl', hex.encode(title)

    if temp:
        path = temp(*args)
    else:
        path = cache(*args)

    return pkl(path, default)

def thread(func, args=()):
    from threading import Thread

    p = Thread(
        target = func,
        args = args
    )
    p.start()
    
    return p

class run:
    from os import getcwd
    from sys import maxsize

    def __init__(self,
        args: list | str,
        wait:bool = False,
        terminal: Literal['cmd', 'ps', 'py', 'pip', 'pym', 'vbs'] = 'cmd',
        dir = getcwd(),
        nested:bool = True,
        hide:bool = False,
        cores:int = 4,
        timeout:int = maxsize
    ):
        from .array import new
  
        self.params = {
            'args' : self.__args__(args, terminal),
            'wait' : wait,
            'dir' : dir,
            'nested' : nested,
            'hide' : hide,
            'cores' : cores,
            'timeout' : timeout
        }

        self.cores = new([0, 1, 2, 3]).random(cores)

        self.start()

    def __args__(self, args, terminal):
        from .array import stringify
        from .pc import Path, OS
        from sys import executable

        # =====================================
        
        if isinstance(args, list):
            args = stringify(args)
        elif isinstance(args, str):
            args = [args]

        file = Path(args[0])

        # =====================================

        if terminal == 'ext':

            exts = {
                'ps1' : 'ps',
                'py'  : 'py',
                'exe' : 'cmd',
                'bat' : 'cmd',
                'vbs' : 'vbs'
            }

            if file.ext():
                terminal = exts[file.ext()]

        # =====================================

        if terminal == 'cmd':
            if OS() == 'windows':
                return args
            else:
                return ['cmd', '/c'] + args

        elif terminal == 'ps':
            if file.exists():
                return ['Powershell', '-File'] + args
            else:
                return ['Powershell', '-Command'] + args

        elif terminal == 'py':
            return [executable, *args]

        elif terminal == 'pip':
            return [executable, '-m', 'pip', *args]

        elif terminal == 'pym':
            return [executable, '-m', *args]
        
        elif terminal == 'vbs':
            return ['wscript'] + args

        else:
            return args

    def wait(self):
        self.process.wait()

    def __background__(self):
        from .time import every

        for _ in every(.1):
            if self.finished() or self.timed_out():
                self.stop()
                return
            else:
                self.task.cores(*self.cores)

    def __stdout__(self):
        from .text import hex
        from .pc import cls, terminal

        cls_cmd = hex.encode('*** Clear Terminal ***')

        for line in self.process.stdout:
            if cls_cmd in line:
                cls()
            elif len(line) > 0:
                terminal.write(line, 'out')

    def __stderr__(self):
        from .pc import terminal

        for line in self.process.stderr:
            terminal.write(line, 'err')

    def start(self):
        from subprocess import Popen, PIPE
        from .time import Stopwatch
        from .pc import process
       
        self.process = Popen(
            shell = self.params['nested'],
            args = self.params['args'],
            cwd = self.params['dir'],
            stdout = PIPE,
            stderr = PIPE,
            text = True
        )

        self.task = process(self.process.pid)
        self.stopwatch = Stopwatch().start()

        if not self.params['hide']:
            thread(self.__stdout__)
            thread(self.__stderr__)

        thread(self.__background__)

        if self.params['wait']:
            self.wait()

    def restart(self):
        self.stop()
        self.start()

    def timed_out(self):
        if self.params['timeout']:
            return self.stopwatch.elapsed() > self.params['timeout']
        else:
            return False

    def finished(self):
        return self.task.alive()

    def stop(self):
        self.stopwatch.stop()
        self.task.stop()

    def output(self, process:bool=False):
        from .json import valid, loads
        from .text import hex
        
        output = self.process.communicate()[0]
        
        if process:

            if hex.valid(output):
                return hex.decode(output)

            elif valid(output):
                return loads(output)

        return output

class errors:

    def FileNotFound(path:str):
        from errno import ENOENT
        from os import strerror

        return FileNotFoundError(ENOENT, strerror(ENOENT), path)
