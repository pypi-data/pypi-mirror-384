from log_translate.business.AndroidCrashPattern_translator import CrashPatternTranslator
from log_translate.business.bluetooth_translator import BluetoothTranslator
from log_translate.globals import remember_dict
from log_translate.log_translator import SysLogTranslator

remember_dict["packages"] = ["com.example.myapplication"]
translators = [SysLogTranslator(tag_translators=[BluetoothTranslator(), CrashPatternTranslator()])]

# log_translate.globals.log_watcher = lambda log: {
#     print("覆盖默认的log_watcher,默认为控制台输出"),
#     log.print()
# }

# def louwang(pid, tag, msg):
#     return Log(translated=f"漏网之鱼 {msg} ", level=Level.w)
#
#
# globals.lou_wang_zhi_yu = louwang
