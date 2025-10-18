class __quickfile:

    def __init__(self, folder:str):
        self.folder = folder

    def dir(self):
        from tempfile import gettempdir
        from .pc import Path, mkdir

        G = Path('G:/Scripts/' + self.folder)
        C = Path(gettempdir() + '/server/' + self.folder)

        if G.exists():
            return G
        else:
            mkdir(C)
            return C 

    def new(
        self,
        name: str = 'undefined',
        ext: str = 'ph',
        id: str = None
    ):
        from .text import random

        if id:
            id = str(id)
        else:
            id = random(50)

        return self.dir().child(f'{name}-{id}.{ext}')

temp = __quickfile('temp').new
cache = __quickfile('cache').new

class xml:

    def __init__(self, path, title):
        from xml.etree import ElementTree
        from .pc import Path

        self.root = ElementTree(title)
        self.path = Path(path)

    def child(element, title, text):
        from xml.etree import ElementTree
        e = ElementTree.SubElement(element, title)
        e.text = text
        return e

    def save(self):
        from xml.etree import ElementTree
        from bs4 import BeautifulSoup
        
        tree = ElementTree.ElementTree(self.root)
        
        tree.write(self.path.path, encoding="utf-8", xml_declaration=True)
        
        d = BeautifulSoup(self.path.open(), 'xml').prettify()

        self.path.write(d)

class pkl:

    def __init__(self, path, default=None):
        from .pc import Path
        self.path = Path(path)
        self.default = default

    def read(self):
        from dill import load
        
        try:
            with self.path.open('rb') as f:
                return load(f)
        except:
            return self.default

    def save(self, value):
        from dill import dump
        
        with self.path.open('wb') as f:
            dump(value, f)

class vdisk:

    class File:

        via_with = False

        def __enter__(self):
            self.via_with = True
            if not self.mount():
                return

        def __exit__(self, *_):
            if self.via_with:
                self.dismount()

        def __init__(self, VHD, MNT, timeout:int=30, ReadOnly:bool=False):
            from .pc import Path

            self.VHD = Path(VHD)
            self.MNT = Path(MNT)
            self.timeout = timeout
            self.ReadOnly = {True:' -ReadOnly', False:''} [ReadOnly]

        def mount(self):

            self.dismount()

            return vdisk.run(
                cmd = f'Mount-VHD -Path "{self.VHD}" -NoDriveLetter -Passthru {self.ReadOnly} | Get-Disk | Get-Partition | Add-PartitionAccessPath -AccessPath "{self.MNT}"',
                timeout = self.timeout
            )

        def dismount(self):

            vdisk.run(
                cmd = f'Dismount-DiskImage -ImagePath "{self.VHD}"',
                timeout = self.timeout
            )

            self.MNT.delete()

    def list(self=None):
        from json import loads
        try:
            p = vdisk.run(
                cmd = 'Get-Volume | Select-Object DriveLetter, FileSystem, Size, SizeRemaining, HealthStatus | ConvertTo-Json'
            )
            return loads(p.output())
        except:
            return []

    def reset(self=None):
        from . import run

        run(['mountvol', '/r'], True)

        for VHD in vdisk.list():
            vdisk.run(
                cmd = f'Dismount-DiskImage -ImagePath "{VHD}"'
            )

    def run(cmd, timeout:int=30):
        from . import run

        return run(
            args = [cmd],
            wait = True,
            terminal = 'ps',
            hide = True,
            timeout = timeout
        )

class json:

    def __init__(self, path, default={}, encode:bool=False):
        from .pc import Path

        self.path = Path(path)
        self.encode = encode
        self.default = default
    
    def read(self):
        from json import load
        from .text import hex

        try:
            data = load(self.path.open())
            if self.encode:
                return hex.decode(data)
            else:
                return data
        except:
            return self.default

    def save(self, data):
        from json import dump
        from .text import hex

        if self.encode:
            data = hex.encode(data)

        dump(
            obj = data,
            fp = self.path.open('w'),
            indent = 3
        )

class properties:

    def __init__(self, path, default=''):
        from .pc import Path

        self.path = Path(path)
        self.default = default
    
    def __obj(self):
        from configobj import ConfigObj
        return ConfigObj(self.path.path)

    def read(self):
        try:
            return self.__obj().dict()
        except:
            return self.default
    
    def save(self, data):

        config = self.__obj()

        for name in data:
            config[name] = data[name]

        config.write()

class yaml:
    
    def __init__(self, path, default={}):
        from .pc import Path
        
        self.path = Path(path)
        self.default = default
    
    def read(self):
        from yaml import safe_load

        try:

            with self.path.open() as f:
                data = safe_load(f)

            if data is None:
                return self.default
            else:
                return data

        except:
            return self.default
    
    def save(self, data):
        from yaml import dump

        with self.path.open('w') as file:
            dump(data, file, default_flow_style=False, sort_keys=False)

class text:

    def __init__(self, path, default=''):
        from .pc import Path
        
        self.path = Path(path)
        self.default = default
    
    def read(self):
        try:
            self.path.read()
        except:
            return self.default
    
    def save(self, data):
        self.path.write(data)

class archive:

    def __init__(self, file):
        from zipfile import ZipFile
        from .pc import Path

        self.file = Path(file)
        self.zip = ZipFile(self.file.path)
        self.files = self.zip.namelist()

    def extractFile(self, file, path):
        from zipfile import BadZipFile
        from .pc import warn

        try:
            self.zip.extract(file, path)
        except BadZipFile as e:
            warn(e)

    def extractAll(self, path, show_progress:bool=True):
        from tqdm import tqdm
        from .pc import Path, mkdir
        
        dst = Path(path)

        mkdir(dst)

        if show_progress:
            
            with tqdm(total=len(self.files), unit=' file') as pbar:
                for file in self.files:
                    pbar.update(1)
                    self.extractFile(file, path)

        else:
            self.zip.extractall(path)

class csv:

    def __init__(self, path, default=''):
        from .pc import Path
        
        self.path = Path(path)
        self.default = default

    def read(self):
        from csv import reader

        try:
            with self.path.open() as csvfile:
                return reader(csvfile)
        except:
            return self.default

    def write(self, data):
        from csv import writer

        with self.path.open('w') as csvfile:
            writer(csvfile).writerows(data)

class toml:

    def __init__(self, path, default=''):
        from .pc import Path
        
        self.path = Path(path)
        self.default = default

    def read(self):
        from toml import load

        try:
            with self.path.open() as f:
                return load(f)
        except:
            return self.default
        
    def save(self, data):
        from tomli_w import dump

        with self.path.open('wb') as f:
            dump(data, f, indent=2)
