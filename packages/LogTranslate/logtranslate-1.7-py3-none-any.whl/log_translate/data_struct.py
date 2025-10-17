from enum import Enum

from typer.colors import RED, BLACK, GREEN, MAGENTA

dot = "▫️"
LOG_RED = "\033[91m"
GREEN_BG_YELLOW = "\033[43;32m"
LOG_YELLOW = "\033[93m"
LOG_ORANGE = "\033[38;5;208m"
LOG_GREEN = "\033[92m"
LOG_RESET = "\033[0m"


class Level(Enum):
    d = 0
    i = 1
    w = 2
    e = 3

    def color(self):
        # return self.value
        # match self.value:
        #     case 0:
        #         return BLACK
        #     case 1:
        #         return GREEN
        #     case 2:
        #         return MAGENTA
        #     case 3:
        #         return RED
        if self.value == 0:
            return BLACK
        if self.value == 1:
            return GREEN
        if self.value == 2:
            return MAGENTA
        if self.value == 3:
            return RED


class Log(object):
    def __init__(self, time="", process="", original="", translated="", level: Level = Level.d, type=""):
        self.time = time
        self.process = process
        self.original = original
        self.translated = translated
        self.level = level
        self.type = type

    def __str__(self):
        return f"{self.time} {dot} {self.process} {dot} {self.translated}"

    def str_with_origin(self):
        show = f"{self.time} {dot} {self.process} {dot} {self.translated}\n{self.original}"
        return show

    def print(self):
        if self.level == Level.e:
            log_e(self.__str__())
        if self.level == Level.w:
            log_w(self.__str__())
        if self.level == Level.i:
            log_i(self.__str__())
        if self.level == Level.d:
            log(self.__str__())


def log_e(log):
    print(LOG_RED + log + LOG_RESET)


def log_w(log):
    print(LOG_ORANGE + log + LOG_RESET)


def log_i(log):
    print(LOG_GREEN + log + LOG_RESET)


def log_o(log):
    print(LOG_YELLOW + log + LOG_RESET)


def log(log):
    print(log)


if __name__ == '__main__':
    log_i("9090")
    print(Level.d.value)
    print(Level(Level.d))
    print(Level(3))
