## 作用

把日志文件拖动到窗口即可解析日志

## 使用

安装

```commandline
pip install LogTranslate
```

项目根目录 创建 config.py
里面定义字段 translator数组

```commandline
translators = [SysLogTranslator(tag_translators=[BluetoothTranslator(), CrashPatternTranslator()])]
```

SysLogTranslator是将文件中每行字符串解析出 tag,time,pid,msg
SysLogTranslator的参数 tag_translators 是数组 用来解析 各种tag对应的内容
解析tag的基类有

- TagPatternTranslator 通过正则匹配tag然后解析
  ```python
  class CrashPatternTranslator(TagPatternTranslator):
       def __init__(self):
           super().__init__({
               r"AndroidRuntime|FATAL.*|System.err.*": activity_task_translator
           })
      
       def activity_task_translator(tag, msg): # 这里两个参数
           # todo 这里需要过滤包名
           return Log(translated=" ------ %s > %s----- " % (tag, msg), level=Level.e)

  ```

- TagStrTranslator 通过字符串匹配tag然后解析
   ```python
  class BluetoothTranslator(TagStrTranslator):
       def __init__(self):
           super().__init__({
               "BluetoothAdapter": bluetooth_adapter,
           })
          
       def bluetooth_adapter(msg):# 这里一个参数
           # todo 这里需要过滤包名
           return Log(translated=" ------ %s > %s----- " % (tag, msg), level=Level.e)

  ```
- SecStrTagTranslator 解析二级tag
   ```python
   class SecTagDemoTranslator(SecStrTagTranslator):
       def __init__(self):
           super().__init__("DFJ",
                            lambda string: re.search(r"(?P<tag>.*?) *:(?P<msg>.*)", string),
                            [
                                SysLogTranslator({
                                    "sec_tag": self.new_tag
                                })
                            ])

       def new_tag(self, tag, msg):# 这里两个参数
           return Log(translated=msg)
  ```

## 打包成 exe

#### 1 ，项目根目录创建 ui.py

```python

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PyQt6Window()
    window.show()
    sys.exit(app.exec())
```

#### 2， 执行打包命令

```commandline

pyinstaller -n [name] --hidden-import config -F -w [-i tools.ico] ui.py

```

### 库地址

https://pypi.org/project/LogTranslate/0.1/

读取文件-->每行文件-->
判断关键tag[每个translate先判断自己的tag满足，然后再正则解析str到通用log，解析后下一个解析的不用解析str-log]

每个translate 都要配置通用的多个tag用于判断是否需要解析然后正则，解析出通用log格式之后，
tag的正则可以创建translae对象的时候创建好re.compile("")
