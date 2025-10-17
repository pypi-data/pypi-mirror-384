import re

from log_translate.data_struct import Log, Level
from log_translate.globals import remember_dict, remember_current_pid, remember_list
from log_translate.log_translator import TagPatternTranslator

anr_patten = (r" *(PID|Reason|Parent|Frozen|Load):.*|CPU usage from.*| *\d+% \d+/.*"
              r"| *\d+% TOTAL:.*|.*?Output from /.*| *(some|full) avg.*")


class CrashPatternTranslator(TagPatternTranslator):
    def __init__(self):
        super().__init__({
            r"AndroidRuntime|System.err.*|DEBUG.?": CrashLogMsgTranslator(),
            "ActivityManager": ActivityManager(),
            "StrictMode": StrictMode,
            "Process": Process,
            r"am_(anr|kill|freeze|crash|proc_start|proc_died)": event_crash
        })


def Process(tag, msg):
    # Process : Quit itself,  Pid:30978  StackTrace:com.example.myapplication.base.app.t.o:39 com.example.myapplication
    if "Quit itself" in msg:
        for pkg in remember_dict["packages"]:
            if pkg in msg:
                return Log(translated=f" {tag} 𓆣 {msg} ", level=Level.e)
    return None


def StrictMode(tag, msg):
    # StrictMode 严苛模式
    # StrictMode: 	at android.os.StrictMode$AndroidCloseGuardReporter.report(StrictMode.java:1987)
    if remember_current_pid() in remember_list("sys_err_pids"):
        return Log(translated=f" {tag} 𓆣 {msg} ", level=Level.w)
    return None


# https://source.android.com/docs/core/tests/debug/understanding-logging?hl=zh-cn
# 含义文档
# https://android.googlesource.com/platform/frameworks/base/+/20e7227/services/java/com/android/server/am/EventLogTags.logtags
def event_crash(tag, msg):
    # 第二个是pid
    # am_proc_died (User|1|5),(PID|1|5),(Process Name|3),(OomAdj|1|5),(ProcState|1|5)
    # am_proc_start (User|1|5),(PID|1|5),(UID|1|5),(Process Name|3),(Type|3),(Component|3)
    # am_kill (User|1|5),(PID|1|5),(Process Name|3),(OomAdj|1|5),(Reason|3)
    result = re.search(r"(\d+,)+(.*?),", msg)
    if result:
        if result.group(2) in remember_dict["packages"]:
            return Log(translated=f" {tag} 𓆣 {msg} ", level=Level.e)
    return None


class ActivityManager:
    def __init__(self):
        self.msg_check = None

    def translate(self, tag, msg):
        if "ANR in" in msg:
            #     ActivityManager: ANR in com.example.myapplication (com.example.myapplication/.MainActivity)
            result = re.search("in (.*?) ", msg)
            if result:
                if result.group(1) in remember_dict["packages"]:
                    self.msg_check = lambda x: True if re.match(anr_patten, x, re.IGNORECASE) else False
                    return Log(translated=f"{tag} 𓆣 {msg} ", level=Level.e)
                else:
                    self.msg_check = None
                    return None
        if "Start proc" in msg:
            self.msg_check = None
            for pkg in remember_dict["packages"]:
                if pkg in msg:
                    return Log(translated=f"{tag} 𓆣 {msg} ", level=Level.w)
            # result = re.search(":(.*?)/", msg)
            # if result:
            #     if result.group(1) in remember_dict["packages"]:
            #         return Log(translated=f"{tag} 𓆣 {msg} ", level=Level.w)
        if any([("Killing" in msg), ("Force stopping" in msg), ("Process" in msg and "has died" in msg)]):
            self.msg_check = None
            # Process com.example.myapplication (pid 12383) has died
            # 应用详情中强制停止
            # Force stopping com.example.myapplication appid=10003 user=0: from pid 2276|40|F|M:0,0
            # ActivityManager: Process com.example.myapplication has crashed too many times, killing! Reason: crashed quickly
            # ActivityManager: Killing 12939:com.example.myapplication/u0a3 (adj 700): stop com.example.myapplicati
            for pkg in remember_dict["packages"]:
                if pkg in msg:
                    return Log(translated=f"{tag} 𓆣 {msg} ", level=Level.e)
        if self.msg_check:
            if self.msg_check(msg):
                return Log(translated=f"{tag} 𓆣 {msg} ", level=Level.e)
        return None


class CrashLogMsgTranslator:
    def translate(self, tag, msg):
        # DEBUG   : Process name is com.example.myapplication, not key_process
        if "Process name is " in msg:
            result = re.search("is (.*), ", msg)
            if result:
                if result.group(1) in remember_dict["packages"]:
                    remember_list("crash_pids", remember_current_pid())
                    return Log(translated=f"{tag} 𓆣 {msg} ", level=Level.e)
        # AndroidRuntime: Process: com.example.myapplication, PID: 30260
        if "Process: " in msg:
            # 开始需要收集日志
            result = re.search("Process: (.*), ", msg)
            if result:
                if result.group(1) in remember_dict["packages"]:
                    remember_list("crash_pids", remember_current_pid())
                    return Log(translated=f"{tag} 𓆣 {msg} ", level=Level.e)
        if remember_current_pid() in remember_list("crash_pids"):
            return Log(translated=f"{tag} 𓆣 {msg} ", level=Level.e)
        if tag.startswith("System.err") and remember_current_pid() in remember_list("sys_err_pids"):
            if "POLICY_DEATH" in msg:
                # StrictMode VmPolicy violation with POLICY_DEATH; shutting down.
                return Log(translated=" %s ⚠ %s " % (tag, msg), level=Level.e)
            # system.err不会导致奔溃，在能解析日志的进程有此日志都打印
            return Log(translated=" %s ⚠ %s " % (tag, msg), level=Level.w)
        return None


# 保存需要解析system.err日志的进程，比如你应用的进程
def remember_system_err_pid():
    remember_list("sys_err_pids", remember_current_pid())


if __name__ == '__main__':
    print(re.compile(".*Task").match("aaTas8km"))
    print(CrashPatternTranslator().translate("FATAL EION", "你好"))
    ss = "[0,12735,com.example.myapplication,"
    print(re.search(r"(\d+,)+(.*?),", ss).group(2))
