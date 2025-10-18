import math, sys

trunc = math.trunc
floor = math.floor
max = sys.maxsize

def digit(number:int, i:int):
    return int( str(number) [i] )

def shuffle_range(min, max):
    from .array import generate, shuffle

    range_ = range(min, max+1)
    range = generate(range_)
    return shuffle(range)

class valid:

    int_str_float = (int | str | float)

    def int(num: int_str_float):
        try:
            int(num)
            return True
        except ValueError:
            return False

    def float(num: int_str_float):
        try:
            float(num)
            return True
        except ValueError:
            return False

def is_prime(num):

    pre = {
        0: False,
        1: False,
        2: True
    }

    if num in pre:
        return pre[num]

    else:

        if digit(num, -1) in [0, 2, 4, 5, 6, 8]:
            return False
        
        else:
            for i in range(2, num):
                if (num % i) == 0:
                    return False

            return True
