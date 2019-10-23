#-*-coding:utf-8-*-
class Base(object):
    pass


class Color(object):
    def __init__(self):
        self._red = '\033[31m'
        self._green = '\033[32m'
        self._yellow = '\033[33m'
        self._blue = '\033[34m'
        self._fuchsia = '\033[35m'
        self._cyan = '\033[36m'
        self._white = '\033[37m'
        #: no color
        self._reset = '\033[0m'

    def color_str(self, color, s):
        return '{}{}{}'.format(
            color,
            s,
            self._reset
        )

    def print_red(self, s):
        print(self.color_str(self._red, s))

    def print_green(self, s):
        print(self.color_str(self._green, s))

    def print_yellow(self, s):
        print(self.color_str(self._yellow, s))

    def print_blue(self, s):
        print(self.color_str(self._blue, s))

    def print_fuchsia(self, s):
        print(self.color_str(self._fuchsia, s))

    def print_cyan(self, s):
        print(self.color_str(self._cyan, s))

    def print_white(self, s):
        print(self.color_str(self._white, s))

if __name__ == '__main__':
    a = Color()
    a.print_red('aaa')
    pass