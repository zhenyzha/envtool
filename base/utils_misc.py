#-*-coding:utf-8-*-
import random
import string
from sys import version_info, stdout
from collections import OrderedDict
import os
import subprocess
import time
import sys


class Colored(object):
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    FUCHSIA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    #: no color
    RESET = '\033[0m'

    def color_str(self, color, s):
        return '{}{}{}'.format(
            getattr(self, color),
            s,
            self.RESET
        )

    def red(self, s):
        return self.color_str('RED', s)

    def green(self, s):
        return self.color_str('GREEN', s)

    def yellow(self, s):
        return self.color_str('YELLOW', s)

    def blue(self, s):
        return self.color_str('BLUE', s)

    def fuchsia(self, s):
        return self.color_str('FUCHSIA', s)

    def cyan(self, s):
        return self.color_str('CYAN', s)

    def white(self, s):
        return self.color_str('WHITE', s)


def py3_to_str(bytes_or_str):
    if isinstance(bytes_or_str, bytes):
        value = bytes_or_str.decode('utf-8')
    else:
        value = bytes_or_str
    return value


def py3_to_bytes(bytes_or_str):
    if isinstance(bytes_or_str, str):
        value = bytes_or_str.encode('utf-8')
    else:
        value = bytes_or_str
    return value


def py2_to_unicode(unicode_or_str):
    if isinstance(unicode_or_str, str):
        value = unicode(unicode_or_str, 'utf-8')
    else:
        value = unicode_or_str
    return value


def py2_to_str(unicode_or_str):
    if isinstance(unicode_or_str, unicode):
        value = unicode_or_str.encode('utf-8')
    else:
        value = unicode_or_str
    return value


def convert_to_str(bytes_or_unicode):
    if version_info.major == 3:
        return py3_to_str(bytes_or_unicode)
    elif version_info.major == 2:
        return py2_to_str(bytes_or_unicode)


def generate_random_string(length, ignore_str=string.punctuation,
                           convert_str=""):
    r = random.SystemRandom()
    sr = ""
    chars = string.ascii_letters + string.digits + string.punctuation
    if not ignore_str:
        ignore_str = ""
    for i in ignore_str:
        chars = chars.replace(i, "")

    while length > 0:
        tmp = r.choice(chars)
        if convert_str and (tmp in convert_str):
            tmp = "\\%s" % tmp
        sr += tmp
        length -= 1
    return sr


def py2_get_terminal_size():
    rows, columns = subprocess.check_output(['stty', 'size']).split()
    return int(rows), int(columns)


def py3_get_terminal_size():
    rows = os.get_terminal_size().lines
    columns = os.get_terminal_size().columns
    return rows, columns


def usage(dict):
    if version_info.major == 3:
        _, columns = py3_get_terminal_size()
    elif version_info.major == 2:
        _, columns = py2_get_terminal_size()
    print('=' * columns)
    for id, key in dict.items():
        print('[%s] %s' % (id, key))
    print('=' * columns)


def py2_and_py3_input(prompt='Selected option: '):
    if version_info.major == 3:
        return input(prompt)
    elif version_info.major == 2:
        return  raw_input(prompt)


def waiting_procesor_bar(prompt='Waiting', step=1, bar='.'):
    sys.stdout.write('\033[33m' + prompt + '\033[0m')
    sys.stdout.flush()
    cur_pos = 1
    while 1:
        sys.stdout.write('%s' % bar)
        sys.stdout.flush()
        time.sleep(step)
        cur_pos += 1

def waiting_spin_procesor_bar(prompt='Waiting', step=1, blank_space=0):
    bars = ['|', '/', '-', '\\', '|', '/', '-', '\\']
    sys.stdout.write('\033[33m' + prompt + ' ' * blank_space + '\033[0m')
    sys.stdout.flush()
    while 1:
        for bar in bars:
            sys.stdout.write('\b')
            sys.stdout.write(bar)
            sys.stdout.flush()
            time.sleep(step)


if __name__ == '__main__':
    print(version_info.major, type(version_info.major))
    waiting_procesor_bar()
