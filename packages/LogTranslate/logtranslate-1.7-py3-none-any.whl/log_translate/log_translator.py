import re
from abc import abstractmethod
from builtins import str

import log_translate.globals
from log_translate.globals import remember_list, remember_current_pid, remember_value, \
    remember_value_force, equal_len

pid_len = 5


# 第二层日志翻译 从已解析出的tag中 根据正则表达式和tag匹配做对应的翻译
# 通过正则表达式匹配tag解析
# :param pattern_translators 是数据[tag,fun(tag, msg)] fun参数必须是(tag, msg)
class TagPatternTranslator(object):
    def __init__(self, pattern_translators):
        # self.pattern_translators = pattern_translators
        self.pattern_translators = {re.compile(key, re.IGNORECASE): value for key, value in pattern_translators.items()}

    def translate(self, tag, msg):
        for pattern in self.pattern_translators:
            match = pattern.fullmatch(tag)
            if match:
                translator = self.pattern_translators[pattern]
                if callable(translator):
                    return translator(tag, msg)
                else:
                    return translator.translate(tag, msg)
        return None


# 第二层日志翻译 从已解析出的tag中 根据字符串和tag匹配做对应的翻译
# 字符串匹配tag  建议使用 TagPatternTranslator 例子参考 BluetoothTranslator
# :param str_translators是数组[tag, fun(msg)] fun方法参数是 (msg)
class TagStrTranslator(object):
    def __init__(self, str_translators):
        self.str_translators = str_translators

    def translate(self, tag, msg):
        if tag in self.str_translators:
            translator = self.str_translators[tag]
            if callable(translator):
                return translator(msg)
            else:
                return translator.translate(msg)
        return None


# 第三层解析 在第二次过滤指定tag之后 进一步解析
# 场景为 一个大模块统一用tag 但是不同功能 在msg用格子的小tag
class SubTagTranslator(TagPatternTranslator):
    """
    :param father表示上一级tag
    :param tag_from_str_fun 从字符串解析tag的方法 返回正则 (str)->re.Match
    :param tag_translators 用来解析二级tag的translator 是个数组必须是TagStrTranslator|TagPatternTranslator
    """

    def __init__(self, father: str, tag_from_str_fun: re.Pattern, tag_translators):
        super().__init__({
            father: self.translate_sub_tag
        })
        self.tag_from_str_fun = tag_from_str_fun
        self.tag_translators = tag_translators

    def translate_sub_tag(self, tag, msg):
        log = self.tag_from_str_fun.search(msg)
        if log:
            sec_tag = log.group("tag")
            sec_msg = log.group("msg")
            for translator in self.tag_translators:
                result = translator.translate(sec_tag, sec_msg)
                if result:
                    return result
        return None


# 第一层解析 将原始日志解析出 time pid tag msg
# 日志文件中日志格式不一定一样，主要分为 系统日志格式解析，logcat日志格式解析，其他日志格式
class StringTranslator(object):
    def __init__(self, tag_translators=None):
        # 这里是 TagStrTranslator
        if tag_translators is None:
            tag_translators = []
        self.tag_translators = tag_translators

    def translate(self, string):
        # 系统日志
        # 03-21 21:31:45.534 12980 15281 I ActivityManager   : START 0 ooooo:
        log = self.tag_from_str(string)
        if log:
            tag = log.group("tag")
            msg = log.group("msg")
            time = log.group("time")
            try:
                pid = log.group("pid")
                if len(pid) < pid_len:
                    pid = pid.ljust(pid_len)
            except:
                pid = "0000"
            remember_current_pid(pid)
            # <editor-fold desc="过滤一次已经翻译过的原始字符串msg">
            last_translated_origin_msg = remember_value("last_translated_origin_msg")
            if equal_len(last_translated_origin_msg, msg):
                return None
            # </editor-fold>
            for translator in self.tag_translators:
                show = translator.translate(tag, msg)
                if show:
                    remember_value_force("last_translated_origin_msg", msg)
                    # <editor-fold desc="翻译结果过滤一次防止连续显示同一个翻译结论">
                    if not remember_value("last_translated_msg", show.translated):
                        # False 表示数据一致
                        return None
                    # </editor-fold>
                    show.time = time
                    show.original = msg
                    show.process = pid
                    # 解析到的才显示，此进程才是要打印错误信息的进程
                    remember_list("pids", pid)
                    return show
                if log_translate.globals.lou_wang_zhi_yu and pid in remember_list("sys_err_pids"):
                    # 是要关注error信息的进程，比如你应用的进程
                    yu = log_translate.globals.lou_wang_zhi_yu(pid, tag, msg)
                    if yu:
                        yu.time = time
                        yu.original = msg
                        yu.process = pid
                        return yu
        return None

    @abstractmethod
    def tag_from_str(self, string):
        pass


class SysLogTranslator(StringTranslator):
    def __init__(self, tag_translators=None):
        super().__init__(tag_translators)
        self.patten = re.compile(r"(?P<time>\d+.*\.\d{3,}) +(?P<pid>\d+).*? [A-Z] (?P<tag>.*?) *:(?P<msg>.*)")

    def tag_from_str(self, string):
        # 04-29 10:01:16.788935  1848  2303 D OGG_Detector: D:done mCurrStatus: 0
        # 09-22 20:46:51.371  2276  2333 I am_kill : [0,12735,com.example.myapplication,900,remove task]
        return self.patten.search(string)


class LogcatTranslator(StringTranslator):

    def tag_from_str(self, string):
        pass


if __name__ == '__main__':
    result = re.search("device: (.*?),", "connect() - device: 34:47:9A:31:52:CF, auto: false, eattSupport: false")
    print(result.group(1))
    result = re.search(r"(?<=\*).*", "onReCreateBond: 24:*:35:06")

    # (?<=A).+?(?=B) 匹配规则A和B之间的元素 不包括A和B
    print(result.group())

    str = "04-29 10:01:16.788935  1848  2303 D OGG_Detector: D:done mCurrStatus: 0"
    f = re.search(r"(?P<time>\d+.*\.\d{3,}) +(?P<pid>\d+).* [A-Z] (?P<tag>.*?) *:(?P<msg>.*)", str)
    print(f.group("pid"))
    print(f.group("tag"))

    print(re.compile("testb", re.IGNORECASE).fullmatch("testb").group())
    string = "09-22 20:46:51.371  2276  2333 I am_kill : [0,12735,com.example.myapplication,900,remove task]"
    print(re.search(r"(?P<time>\d+.*\.\d{3,}) +(?P<pid>\d+).* [A-Z] (?P<tag>.*?) *:(?P<msg>.*)", string))
