from typing import Literal, Self, Generator

def IP():
    from socket import gethostname, gethostbyname
    return gethostbyname(gethostname())

def ping(addr:str) -> bool:
    from ping3 import ping as __ping

    r = __ping(addr)

    return not bool(r)

def socket(timeout:int=10):
    
    from socket import socket, AF_INET, SOCK_STREAM

    s = socket(AF_INET, SOCK_STREAM)
    
    s.settimeout(timeout)
    
    return s

def mac2ip(mac):
    from .array import filter
    from . import run
    from .pc import OS

    if OS() == 'windows':
        arp_table = run(['arp', '-a'], True, hide=True).output()

    base = '.'.join(IP().split('.')[:-1]) + '.{}'

    for x in range(1, 256):

        ip = base.format(x)

        if ip in arp_table:

            mac_ = filter(
                arp_table.split(ip)[1].split('\n')[0].split(' '),
                lambda x: '-' in x
            )[0]

            if mac_ == mac.replace(':', '-'):
                return ip

class conn:

    def __init__(self, conn:socket):
        self.conn = conn

        from struct import pack, unpack

        self.__pack = pack
        self.__unpack = unpack

    def send(self, data):
        from .text import hex

        data = hex.encode(data).encode()

        # Pack the length into a 4-byte header (e.g., using '!' for network byte order, 'I' for unsigned int)
        header = self.__pack('!I', len(data))

        # Send the header
        self.conn.sendall(header)

        # Send the actual data
        self.conn.sendall(data)

    def recv(self):
        from .text import hex

        # Unpack the length from the header
        length = self.__unpack('!I', 
            self.conn.recv(4)
        )[0]

        # Receive the actual data based on the unpacked length
        data = self.conn.recv(length).decode('utf-8')

        return hex.decode(data)

class host:

    def __init__(self, ip=IP(), port:int=80):
        self.bindings = (ip, port)
        self.s = socket()
        self.start()
    
    def close(self):
        self.s.close()
        self.started = False

    def start(self):
        try:
            self.s.bind(self.bindings)
            self.s.listen()

            self.started = True
        except:
            self.started = False
            return

    def listen(self) -> Generator[conn]:
        while True:
            yield conn(self.s.accept()[0])

def client(ip=IP(), port=80):
    try:
        conn_ = socket()
        conn_.connect((ip, port))
        return conn(conn_)
    except:
        return None

def port_listening(ip=IP(), port:int=80):
    
    from socket import timeout

    try:
        with socket() as s:
            s.settimeout(1)
            s.connect((ip, port))
            return True
    except (timeout, ConnectionRefusedError, OSError):
        return False
    
class Port:

    def __init__(self, host, port):

        from socket import error, SHUT_RDWR

        self.port = port

        s = socket()

        try:
            s.connect((host, port))
            s.shutdown(SHUT_RDWR)
            self.free = False
        except error:
            self.free = True
        finally:
            s.close()

def find_open_port(min:int, max:int):
    for x in range(min, max+1):
        port = Port(IP(), x)
        if port.free:
            return port.port

class ssh:

    def __init__(self, ip:str, username:str, password:str, timeout:int=None, port:int=22):

        from paramiko import SSHClient, AutoAddPolicy

        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        self.client.connect(ip, port, username, password, timeout=timeout)

    def run(self, command):

        # Execute a command
        stdout, stderr = self.client.exec_command(command)[1:]

        error_mess = stderr.read().decode()

        #
        class output:

            if len(error_mess) == 0:
                output = stdout.read().decode()
                error = False
            else:
                output = error_mess
                error = True
            
        return output

    def close(self):
        self.client.close()

class torrent:

    class qbit:

        def __init__(self, addr: str):

            from qbittorrentapi import Client, LoginFailed, Forbidden403Error

            self.__LoginFailed = LoginFailed, Forbidden403Error

            self.client = Client(
                host = addr,
                port = 8080,
                username = 'admin',
                password = '3mW8{:t69Ho.',
                VERIFY_WEBUI_CERTIFICATE = False
            )

        def online(self):
            
            try:
                self.client.auth_log_in()
                return True
            
            except self.__LoginFailed:
                return False

        def api(self):
            from .time import sleep

            while not self.online():
                sleep(.1)

            return self.client

    tpb_url = "https://thepiratebay0.org/search/{}/1/99/0"

    def quality_from_title(title:str):

        title = title.lower()

        if '2160p' in title:
            return 2160
        
        if '1440p' in title:
            return 1440
        
        if '1080p' in title:
            return 1080
        
        if '720p' in title:
            if 'hdtv' in title:
                return 'hdtv'
            else:
                return 720
        
        if '480p' in title:
            return 480
        
        if '360p' in title:
            return 360
        
        if 'tvrip x264' in title:
            return 'tv'

    class queue:

        def find(tag):
            for t in torrent.qbit().api().torrents_info():
                if tag in t.tags:
                    return t

        class torrent:

            def __init__(self, t):
                from .array import priority
                
                self.hash = t.hash
                self.name = t.name

                seeders = t.num_complete
                remaining = t.size - t.downloaded
                self.priority = priority(seeders, remaining, True)

        def clear(rm_files:bool=True):
            qbit = torrent.qbit().api
            for t in qbit().torrents_info():
                qbit().torrents_delete(
                    torrent_hashes = t.hash,
                    delete_files = rm_files
                )

        def sort():
            from .array import sort

            api = torrent.qbit().api

            torrents = []

            for t in api().torrents_info():
                torrents.append(
                    torrent.queue.torrent(t)
                )

            torrents = sort(
                torrents,
                lambda t: t.priority
            )

            for x, t in enumerate(torrents):
                api().torrents_bottom_priority(t.hash)

    class Magnet:

        def state(self):
        
            class state:
                errored = None
                finished = None
                exists = None

            if self.get():
                enum = self.get().state_enum
                state.finished = enum.is_uploading or enum.is_complete
                state.errored = enum.is_errored
                state.exists = True
            else:
                state.exists = False
        
            return state

        def __init__(self, title=None, seeders=None, leechers=None, url=None, quality=None, size=None):
            
            self.title = title
            self.seeders = seeders
            self.leechers = leechers
            self.url = url
            self.quality = quality
            self.size = size

            self.qbit = torrent.qbit().api

        def start(self):
            self.qbit().torrents_add(
                self.url,
                save_path = 'G:/Scripts/__temp__/',
                tags = self.url
            )

        def get(self):
            for t in self.qbit().torrents_info():
                if self.url in t.tags:
                    return t

        def restart(self):
            self.stop()
            self.start()
                
        def stop(self, rm_files:bool=True):
            torrent = self.get()
            if torrent:
                self.qbit().torrents_delete(
                    torrent_hashes = torrent.hash,
                    delete_files = rm_files
                )

        def files(self):
            torrent = self.get()
            for file in torrent.files:
                yield [
                    f'{torrent.save_path}/{file.name}',
                    file.size
                ]

    def searchTPB(*queries) -> Generator[Magnet]:
        from .text import rm
        from .pc import size

        for query in queries:

            query = rm(query, '.', "'")
            url = torrent.tpb_url.format(query)
            soup = static(url).soup

            for row in soup.select('tr:has(a.detLink)'):
                try:

                    title: str = row.select_one('a.detLink').text
                    details: str = row.select_one('font.detDesc').text

                    yield torrent.Magnet(
                        title = title,
                        seeders = int(row.select('td')[-2].text),
                        leechers = int(row.select('td')[-1].text),
                        url = row.select_one('a[href^="magnet:"]')['href'],
                        quality = torrent.quality_from_title(title),
                        size = size.to_bytes(details.split('Size ')[1].split(',')[0])
                    )

                except:
                    pass

def get(**args):
    from requests import get as __get
    from requests.exceptions import ConnectionError
    from .pc import warn

    if 'headers' not in args:            
        args['headers'] = {}

    args['headers']['User-Agent'] = 'Mozilla/5.0'
    args['headers']['Accept-Language'] = 'en-US,en;q=0.5'

    while True:
        try:
            return __get(**args)
        except ConnectionError as e:
            warn(e)

class api:

    def omdb(url='', params=[]):
        params['apikey'] = 'dc888719'
        return get(
            url = f'https://www.omdbapi.com/{url}',
            params = params
        ).json()
    
    def numista(url='', params=[]):
        return get(
            url = f'https://api.numista.com/v3/{url}',
            params = params,
            headers = {'Numista-API-Key': 'KzxGDZXGQ9aOQQHwnZSSDoj3S8dGcmJO9SLXxYk1'},
        ).json()
    
    def mojang(url='', params=[]):
        return get(
            url = f'https://api.mojang.com/{url}',
            params = params
        ).json()
    
    def geysermc(url='', params=[]):
        return get(
            url = f'https://api.geysermc.org/v2/{url}',
            params = params
        ).json()

    def __init__(self, url:str=None, params={}, headers=None):
        self.data = get(
            url = url,
            params = params,
            headers = headers,
        ).json()
    
    def __main__(self):
        return self.data

class soup:

    def convItems(self, soups):
        elements = []
        for s in soups:
            elements.append(soup(s))
        return elements

    by = Literal[
        'class', 'classname', 'class_name',
        'id',
        'xpath',
        'name',
        'attr', 'attribute'
    ]

    from bs4 import BeautifulSoup
    def __init__(self, soup:BeautifulSoup):
        
        from lxml.etree import _Element, HTML

        self.dom:_Element = HTML(str(soup))
        self.soup = soup

    def element(self, by:by, name:str) -> list[Self]:
        
        by = by.lower()

        if by in ['class', 'classname', 'class_name']:
            return self.convItems(
                self.soup.select(f'.{name}')
            )

        if by in ['id']:
            return self.convItems(
                self.soup.find_all(id=name)
            )

        if by in ['xpath']:
            return self.convItems(
                self.dom.xpath(name)
            )

        if by in ['name']:
            return self.convItems(
                self.soup.find_all(name=name)
            )

        if by in ['attr', 'attribute']:
            t, c = name.split('=')
            return self.convItems(
                self.soup.find_all(attrs={t: c})
            )

class FireFox:

    def dir():
        from .pc import Path
        return Path("C:/Users/Administrator/AppData/Roaming/Mozilla/Firefox")

    class Profile:

        def __init__(self, name:str):
            from .file import properties

            self.name = name.lower()

            profiles: dict[str, dict[str, str]] = properties(
                path = FireFox.dir().child('profiles.ini')
            ).read()

            for id in profiles:
                if id.startswith('Profile'):
                    if data['Name'].lower() == self.name:

                        from browser_cookie3 import firefox as bc_firefox
                        from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
                
                        self.path = FireFox.dir().child(data['Path'])
                        
                        self.selenium = FirefoxProfile(self.path.path)

                        self.cookiejar = bc_firefox(self.path.child('cookies.sqlite').path)

                        self.cookies = []
                        for cookie in self.cookiejar:
                            
                            data = {
                                'name': cookie.name,
                                'value': cookie.value,
                                'secure': bool(cookie.secure)
                            }

                            if cookie.expires:
                                data['expiry'] = cookie.expires
                            
                            if cookie.path_specified:
                                data['path'] = cookie.path

                            if cookie.domain_specified:
                                data['domain'] = cookie.domain

                            self.cookies += [data]
                        
                        return

class browser:
    from selenium.webdriver.remote.webelement import WebElement

    by = Literal['class', 'id', 'xpath', 'name', 'attr']
            
    def __init__(
        self,
        headless: bool = True,
        wait: int = 20,
        cookies: (list[dict] | None) = None,
        debug: bool = False
    ):
        from selenium.webdriver import FirefoxService, FirefoxOptions, Firefox
        from selenium.common.exceptions import InvalidCookieDomainException
        from subprocess import CREATE_NO_WINDOW
        
        self.via_with = False
        self.wait = wait
        self.__debug_enabled = debug

        service = FirefoxService()
        service.creation_flags = CREATE_NO_WINDOW

        options = FirefoxOptions()
        options.add_argument("--disable-search-engine-choice-screen")        
        if headless:
            options.add_argument("--headless")

        # Start Chrome Session with options
        self.__session = Firefox(options, service)

        if cookies:
            for cookie in cookies:
                try:
                    self.__session.add_cookie(cookie)
                except InvalidCookieDomainException:
                    pass

        # Set Implicit Wait for session
        self.__session.implicitly_wait(self.wait)

        self.current_url = self.__session.current_url

        self.reload = self.__session.refresh
        self.run = self.__session.execute_script

    def __enter__(self):
        self.via_with = True
        return self

    def __exit__(self, *_):
        if self.via_with:
            self.close()
    
    def __debug(self,
        title:str,
        data:dict={}
        ):
        from .json import dumps
        
        if self.__debug_enabled:
            print(title+':', dumps(data))

    def element(self, by:by, name:str, wait:bool=True) -> list[WebElement]:
        from selenium.webdriver.common.by import By

        # Force 'by' input to lowercase
        by = by.lower()

        # Check if by is 'class'
        if by == 'class':
            
            if isinstance(name, list):
                name = '.'.join(name)

            _by = By.CLASS_NAME

        # Check if by is 'id'
        if by == 'id':
            _by = By.ID

        # Check if by is 'xpath'
        if by == 'xpath':
            _by = By.XPATH

        # Check if by is 'name'
        if by == 'name':
            _by = By.NAME

        # Check if by is 'attr'
        if by == 'attr':
            _by = By.CSS_SELECTOR
            t, c = name.split('=')
            name = f"a[{t}='{c}']"

        self.__debug(
            title = "Finding Element", 
            data = {'by': by, 'name':name}
            )

        find_elements = lambda: self.__session.find_elements(_by, name)

        if wait:
            elements = []
            while len(elements) == 0:
                elements = find_elements()
            return elements
        else:
            return find_elements()

    def open(self,
        url:str,
        wait:bool = True
    ):
        
        self.__session.get(url)

        self.__debug(
            title = "Opening", 
            data = {'url':url}
            )

        if wait:
            while True:
                readyState = self.run("return document.readyState")
                if readyState in ["complete", 'interactive']:
                    return

    def close(self):
        from selenium.common.exceptions import InvalidSessionIdException
        
        self.__debug('Closing Session')

        try:
            self.__session.close()
        except InvalidSessionIdException:
            pass

    def soup(self):
        from bs4 import BeautifulSoup
        
        return soup(BeautifulSoup(
            self.__session.page_source,
            'html.parser'
        ))

def static(url):
    from bs4 import BeautifulSoup

    return soup(
        BeautifulSoup(
            get(url=url).content,
            'html.parser'
        )
    )

def dynamic(url, driver:browser=None):
    from bs4 import BeautifulSoup
    
    if driver is None:
        driver = browser()

    driver.open(url)

    return driver.soup()

def download(url, path, show_progress:bool=True, cookies=None):
    from tqdm import tqdm
    from urllib.request import urlretrieve

    r = get(
        url = url,
        stream = True,
        cookies = cookies
    )

    size = int(r.headers.get("content-length", 0))

    if show_progress:
        with tqdm(total=size, unit="B", unit_scale=True) as bar:
            with open(path, "wb") as file:
                for data in r.iter_content(1024):
                    bar.update(len(data))
                    file.write(data)
    else:
        urlretrieve(url, path)
