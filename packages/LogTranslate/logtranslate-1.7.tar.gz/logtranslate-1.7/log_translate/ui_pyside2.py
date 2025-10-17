import sys
import traceback

import keyboard as keyboard
import pkg_resources
from PySide6.QtGui import QIcon, QFont, QAction, QColor
from PySide6.QtWidgets import QMainWindow, QListWidget, QAbstractItemView, QApplication, QListWidgetItem
from qt_material import apply_stylesheet

from log_translate.data_struct import Log, Level
from log_translate.read_log_file import LogReader


# 𐐘💥╾━╤デ╦︻ඞා
# https://emojidb.org/bug-emojis

class PySide6Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🤖日志解析")
        # self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        ico = pkg_resources.resource_filename('log_translate', 'res/log_logo.ico')
        self.setWindowIcon(QIcon(ico))
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setCentralWidget(self.list_widget)
        self.setAcceptDrops(True)
        self.create_menu()
        self.log_reader = LogReader()
        self.data_item_logs = {
            Level.d.value: [],
            Level.i.value: [],
            Level.w.value: [],
            Level.e.value: [],
        }
        self.show_level = Level.e.value
        self.show_origin = False
        self.theme_dark = True
        self.log_reader.log_stream.subscribe_(lambda log: {
            self.collect_logs_and_show(log),
        })
        if len(sys.argv) <= 1:
            self.list_widget.addItem(" 💭 把文件拖入到窗口开始解析日志 💭 ")
            return
        else:
            self.do_to_read_file(sys.argv[1])

    def create_menu(self):
        menu_bar = self.menuBar()
        action = menu_bar.addMenu("操作")

        filter_action = QAction("Level_D", self)
        filter_action.setShortcut('Ctrl+D')
        filter_action.triggered.connect(self.filter_logs_d)
        action.addAction(filter_action)

        filter_action = QAction("Level_I", self)
        filter_action.setShortcut('Ctrl+I')
        filter_action.triggered.connect(self.filter_logs_i)
        action.addAction(filter_action)

        filter_action = QAction("Level_W", self)
        filter_action.setShortcut('Ctrl+W')
        filter_action.triggered.connect(self.filter_logs_w)
        action.addAction(filter_action)

        filter_action = QAction("Level_E", self)
        filter_action.setShortcut('Ctrl+E')
        filter_action.triggered.connect(self.filter_logs_e)
        action.addAction(filter_action)

        keyboard.add_hotkey('Ctrl+O', self.log_show_origin)
        keyboard.add_hotkey('Ctrl+Up', self.font_zoom_in)
        keyboard.add_hotkey('Ctrl+Down', self.font_zoom_out)
        keyboard.add_hotkey('Ctrl+R', self.log_clear)
        keyboard.add_hotkey('Ctrl+T', self.theme_change)

    def theme_change(self):
        if self.theme_dark:
            self.theme_dark = False
            apply_stylesheet(app, theme='light_lightgreen.xml', invert_secondary=True)
        else:
            self.theme_dark = True
            apply_stylesheet(app, theme='dark_lightgreen.xml', invert_secondary=True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            if not self.isMaximized():
                self.showMaximized()
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        self.data_item_logs = {
            Level.d.value: [],
            Level.i.value: [],
            Level.w.value: [],
            Level.e.value: [],
        }
        for url in event.mimeData().urls():
            file = url.toLocalFile()
            self.do_to_read_file(file)

    def do_to_read_file(self, file):
        # f-string 可以使用 {变量} 语法将表达式嵌入到字符串中
        self.list_widget.clear()
        self.list_widget.addItem(f"\n👇👇👇👇👇👇👇👇 {file} 💥 日志解析如下 👇👇👇👇👇👇👇👇")
        try:
            self.log_reader.concurrency([file])
        except:
            item = QListWidgetItem(traceback.format_exc())
            item.setForeground(QColor("red"))
            self.list_widget.addItem(item)
        # for i in range(100):

    def show_log_on_finish(self):
        if len(self.data_item_logs[self.show_level]) == 0:
            for level in range(self.show_level - 1, 0, -1):
                if len(self.data_item_logs[level]) > 0:
                    self.filter_logs(Level(level))
                    return None

    def collect_logs_and_show(self, log: Log):
        if log.translated is None:
            # 文件读取到最后
            self.show_log_on_finish()
            return

        for log_level in self.data_item_logs:
            if log.level.value >= log_level:
                self.data_item_logs[log_level].append(log)
        if log.level.value >= self.show_level:
            self.list_widget.addItem(self.log_to_list_item(log))

    def log_to_list_item(self, log: Log):
        if self.show_origin:
            log_str = log.str_with_origin()
        else:
            log_str = log.__str__()
        item = QListWidgetItem(log_str)
        item.setForeground(QColor(log.level.color()))
        return item

    def filter_logs_d(self):
        self.filter_logs(Level.d)

    def filter_logs_i(self):
        self.filter_logs(Level.i)

    def filter_logs_w(self):
        self.filter_logs(Level.w)

    def filter_logs_e(self):
        self.filter_logs(Level.e)

    def log_show_origin(self):
        self.show_origin = not self.show_origin
        self.filter_logs(Level(self.show_level))

    def filter_logs(self, level: Level):
        self.show_level = level.value
        first = self.list_widget.item(0).text()
        self.list_widget.clear()
        self.list_widget.addItem(first)
        show_logs = self.data_item_logs[self.show_level]
        for log in show_logs:
            self.list_widget.addItem(self.log_to_list_item(log))

    # 字体缩小
    def font_zoom_out(self):
        font: QFont = self.list_widget.font()
        new_font = QFont()
        new_font.setPointSize(font.pointSize() - 1)
        self.list_widget.setFont(new_font)

    # 字体放大
    def font_zoom_in(self):
        font: QFont = self.list_widget.font()
        new_font = QFont()
        new_font.setPointSize(font.pointSize() + 1)
        self.list_widget.setFont(new_font)

    # 清空缓存
    def log_clear(self):
        self.data_item_logs = {
            Level.d.value: [],
            Level.i.value: [],
            Level.w.value: [],
            Level.e.value: [],
        }
        self.showNormal()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PySide6Window()
    # 设置主题样式，theme的取值下面给出
    apply_stylesheet(app, theme='dark_lightgreen.xml')
    window.show()
    sys.exit(app.exec())

#  打包命令
# pyinstaller --name=log_translator --onefile --windowed ui_PySide6.py
# -F, --onefile   产生单个的可执行文件
# -n NAME, --name NAME   指定项目（产生的 spec）名字。如果省略该选项，那么第一个脚本的主文件名将作为 spec 的名字
# -w, --windowed, --noconsole   指定程序运行时不显示命令行窗口（仅对 Windows 有效）
# -i <FILE.ico>, --icon <FILE.ico>  指定icon

#  打包执行以下命令
# pyinstaller -n log_translator --hidden-import config -F -w -i res/log_logo.ico ui_PySide6.py
# --hidden-import 设置导入要动态加载的类 因为没被引用 所以不会导入需要手动设置

# pip install PyInstaller
# pyinstaller --name=<your_exe_name> --onefile --windowed --add-data "<your_data_folder>;<your_data_folder>" <your_script_name>.py

# 上述命令中的选项说明：
# --name: 可执行文件名称。
# --onefile: 将整个项目打包为一个单独的可执行文件。
# --windowed: 隐藏控制台窗口，将打包的应用程序显示为GUI应用程序。
# --add-data: 添加项目资源，支持文件夹和文件，前面是资源路径，后面是输出路径，用分号进行分割。
# 执行上述命令后，会在项目目录下生成一个.spec文件，这个文件会告诉PyInstaller如何将项目打包成exe文件。
