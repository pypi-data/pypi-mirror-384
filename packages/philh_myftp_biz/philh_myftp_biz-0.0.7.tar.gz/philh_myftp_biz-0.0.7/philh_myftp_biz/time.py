import sys

def sleep(s:int, print:bool=False):

    from time import sleep as __sleep

    if print:
        print('Waiting ...')
        for x in range(1, s+1):
            print('{}/{} seconds'.format(x, s))
            __sleep(1)
    else:
        __sleep(s)
    
    return True

class every:
    
    def __init__(self, s:int, max_iters:int=sys.maxsize):
        self.s = s
        self.max_iters = max_iters

    def __iter__(self):
        self.x = 0
        return self
    
    def __next__(self):
        from time import sleep as __sleep

        if self.x == self.max_iters:
            raise StopIteration
        else:
            __sleep(self.s)
            return

def toHMS(stamp):
    m, s = divmod(stamp, 60)
    h, m = divmod(m, 60)
    return ':'.join([
        strDigit(h),
        strDigit(m),
        strDigit(s)
    ])

def strDigit(n):
    from math import trunc
    return str( trunc(n) ).ljust( 2, '0' )

class Stopwatch:

    def __init__(self):
        from time import perf_counter

        self.start_time = None
        self.end_time = None
        self.running = False
        self.now = perf_counter

    def elapsed(self, string:bool=False):
        if self.running:
            elapsed = self.now() - self.start_time
        else:
            elapsed = self.end_time - self.start_time

        if string:
            return toHMS(elapsed)
        else:
            return elapsed

    def start(self):
        self.start_time = self.now()
        self.end_time = None
        self.running = True
        return self

    def stop(self):
        self.end_time = self.now()
        self.running = False
        return self

class from_stamp:

    def __init__(self, stamp):
        from datetime import timezone, timedelta, datetime

        self.dt = datetime.fromtimestamp(
            timestamp = stamp,
            tz = timezone(
                offset = timedelta(hours=-4)
            )
        )

        self.year: int = self.dt.year
        self.month: int = self.dt.month
        self.day: int = self.dt.day
        self.hour: int = self.dt.hour
        self.minute: int = self.dt.minute
        self.second: int = self.dt.second

        self.unix: int = stamp
        self.__unix: int = stamp

    def update(self):
        from datetime import datetime

        if self.__unix == self.unix:

            t = datetime(
                self.year,
                self.month,
                self.day,
                self.hour,
                self.minute,
                self.second
            )

            self.unix = t.timestamp()
            self.__unix = t.timestamp()

        else:

            t = from_stamp(self.unix)

            self.year = t.year
            self.month = t.month
            self.day = t.day
            self.hour = t.hour
            self.minute = t.minute
            self.second = t.second
    
    class __toString:
        def __init__(self, p:'from_stamp'):
            self.year = str(p.year)
            self.month = str(p.month)
            self.day = str(p.day)
            self.hour = str(p.hour)
            self.minute = str(p.minute)
            self.second = str(p.second)
            self.unix = str(p.unix)

    def toString(self) -> __toString:
        return self.__toString(self)

    def stamp(self, format):
        from datetime import datetime
        return datetime.strftime(format)

def now() -> from_stamp:
    from time import time

    return from_stamp(time())

def from_string(string, separator='/', order='YMD') -> from_stamp:
    from datetime import datetime

    split = string.split(separator)

    order = order.lower()
    Y = split[order.index('y')]
    M = split[order.index('m')]
    D = split[order.index('d')]

    dt_ = datetime.strptime(f'{Y}-{M}-{D}', "%Y-%m-%d")
    return from_stamp(dt_.timestamp())

def from_ymdhms(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
):
    from datetime import datetime

    t = datetime(
        year,
        month,
        day,
        hour,
        minute,
        second
    )

    return from_stamp(t.timestamp())

def get(*input) -> from_stamp:
    from datetime import datetime

    return from_stamp(datetime(*input).timestamp())
