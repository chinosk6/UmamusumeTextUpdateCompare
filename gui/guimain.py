import sys
import os
import time
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QDialog, QApplication, QMainWindow, QStyleFactory, QFileDialog
from .qtui.ui_import import MainUI
import ctypes
from threading import Thread
import uma_compare
from .user_config import user_config
import traceback

try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")
except:
    pass

local_language = ctypes.windll.kernel32.GetUserDefaultUILanguage()
sChinese_lang_id = [0x0004, 0x0804, 0x1004]  # zh-Hans, zh-CN, zh-SG
tChinese_lang_id = [0x0404, 0x0c04, 0x1404, 0x048E]  # zh-TW, zh-HK, zh-MO, zh-yue-HK

# translate = QtCore.QCoreApplication.translate

class MainDialog(QDialog):
    def __init__(self, parent=None):
        super(QDialog, self).__init__(parent)
        self.ui = MainUI()
        self.ui.setupUi(self)


class UIChange(QObject):
    show_msgbox_signal = QtCore.pyqtSignal(str, str)
    update_bar_signal = QtCore.pyqtSignal(int, int)
    set_start_button_enabled_signal = QtCore.pyqtSignal(bool)
    add_item_to_update_files_view_signal = QtCore.pyqtSignal(str)
    add_item_to_new_files_view_signal = QtCore.pyqtSignal(str)
    add_item_to_error_files_view_signal = QtCore.pyqtSignal(str)

    def __init__(self):
        QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
        QApplication.setStyle(QStyleFactory.create("windowsvista"))  # ['windowsvista', 'Windows', 'Fusion']
        super(UIChange, self).__init__()
        self.app = QApplication(sys.argv)

        self.trans = QtCore.QTranslator()
        self.load_i18n()

        self.window = QMainWindow()
        self.window.setWindowIcon(QtGui.QIcon(":/img/linqin_nawone.ico"))
        self.ui = MainUI()
        self.ui.setupUi(self.window)

        self.reg_clicked_connects()
        self.signal_reg()

        self.error_msgs = {}
        self.cache_total_files = 0

    def load_i18n(self):
        if local_language in sChinese_lang_id:
            self.trans.load(":/trans/main_ui.qm")
            self.install_trans()

        elif local_language in tChinese_lang_id:
            self.trans.load(":/trans/main_ui.qm")
            self.install_trans()

    def install_trans(self):
        self.app.installTranslator(self.trans)

    def reg_clicked_connects(self):  # 点击回调注册
        self.ui.pushButton_orig_jp.clicked.connect(self.set_path(0))
        self.ui.pushButton_orig_local.clicked.connect(self.set_path(1))
        self.ui.pushButton_new_jp.clicked.connect(self.set_path(2))
        self.ui.pushButton_orig_textdata.clicked.connect(self.set_path(3))
        self.ui.pushButton_new_textdata.clicked.connect(self.set_path(4))
        self.ui.pushButton_start_compare.clicked.connect(self.start_compare)
        self.ui.listWidget_error_files.itemSelectionChanged.connect(self.error_index_move)

    def signal_reg(self):  # 信号槽注册
        self.show_msgbox_signal.connect(self.show_message_box)
        self.update_bar_signal.connect(self.update_bar)
        self.set_start_button_enabled_signal.connect(self.ui.pushButton_start_compare.setEnabled)
        self.add_item_to_update_files_view_signal.connect(self.add_item_to_listwidget(self.ui.listWidget_updated_files))
        self.add_item_to_new_files_view_signal.connect(self.add_item_to_listwidget(self.ui.listWidget_new_files))
        self.add_item_to_error_files_view_signal.connect(self.add_item_to_listwidget(self.ui.listWidget_error_files))
        self.ui.listWidget_updated_files.doubleClicked.connect(
            lambda *x: self.open_file_path(self.ui.listWidget_updated_files.selectedItems())
        )
        self.ui.listWidget_new_files.doubleClicked.connect(
            lambda *x: self.open_file_path(self.ui.listWidget_new_files.selectedItems())
        )
        self.ui.listWidget_error_files.doubleClicked.connect(
            lambda *x: self.open_file_path(self.ui.listWidget_error_files.selectedItems())
        )

    def show_message_box(self, title, text, btn=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No):
        return QtWidgets.QMessageBox.information(self.window, title, text, btn)

    @staticmethod
    def open_file_path(checked: list):
        if checked:
            os.system(f'explorer /select, {os.path.realpath(checked[0].text())}')

    def set_path(self, path_index: int):
        indexs = [self.ui.lineEdit_orig_jp, self.ui.lineEdit_orig_local, self.ui.lineEdit_new_jp,
                  self.ui.lineEdit_orig_textdata, self.ui.lineEdit_new_textdata]

        def _():
            folder_path = QFileDialog.getExistingDirectory(self.ui, "Choose a folder")
            if folder_path != "":
                indexs[path_index].setText(folder_path)
        return _

    def update_bar(self, now_count: int, total_count: int):
        self.cache_total_files = total_count
        if total_count == 0:
            self.ui.progressBar_all.setValue(100)
        else:
            self.ui.label_progress.setText(f"{now_count}/{total_count}")
            if now_count <= total_count:
                self.ui.progressBar_all.setValue(int(now_count / total_count * 100))
            else:
                self.ui.progressBar_all.setValue(100)

    @staticmethod
    def add_item_to_listwidget(listwidget: QtWidgets.QListWidget):
        def _(value: str):
            listwidget.addItem(value)
        return _

    def files_update_callback(self, msg_type: int, file_name: str, extra_data=None):
        if msg_type == 0:
            self.add_item_to_update_files_view_signal.emit(file_name)
        elif msg_type == 1:
            self.add_item_to_new_files_view_signal.emit(file_name)
        elif msg_type == 2:
            self.add_item_to_error_files_view_signal.emit(file_name)
            if isinstance(extra_data, dict):
                self.error_msgs.update(extra_data)

    def error_index_move(self, *args):
        items = self.ui.listWidget_error_files.selectedItems()
        if len(items) >= 1:
            err_info = self.error_msgs.get(items[0].text(), "No description.")
            self.ui.textEdit_error_info.setText(err_info)

    def start_compare(self):
        self.ui.listWidget_updated_files.clear()
        self.ui.listWidget_new_files.clear()
        self.ui.listWidget_error_files.clear()
        self.ui.textEdit_error_info.clear()
        self.error_msgs.clear()

        user_config.orig_jp_path = self.ui.lineEdit_orig_jp.text().strip()
        user_config.orig_local_path = self.ui.lineEdit_orig_local.text().strip()
        user_config.new_jp_path = self.ui.lineEdit_new_jp.text().strip()
        user_config.orig_jp_textdata_path = self.ui.lineEdit_orig_textdata.text().strip()
        user_config.new_jp_textdata_path = self.ui.lineEdit_new_textdata.text().strip()
        user_config.compare_text_data = self.ui.checkBox_cmp_text_data.isChecked()
        user_config.compare_stories = self.ui.checkBox_cmp_stories.isChecked()
        user_config.save_new = self.ui.checkBox_save_new.isChecked()
        user_config.save_data()

        def _():
            self.set_start_button_enabled_signal.emit(False)
            try:
                path_orig_jp = self.ui.lineEdit_orig_jp.text().strip()
                path_orig_local = self.ui.lineEdit_orig_local.text().strip()
                path_orig_textdata = self.ui.lineEdit_orig_textdata.text().strip()
                path_new_textdata = self.ui.lineEdit_new_textdata.text().strip()
                path_new_jp = self.ui.lineEdit_new_jp.text().strip()
                if not os.path.isdir(path_orig_local):
                    self.show_msgbox_signal.emit("Error", f"Invalid path: {path_orig_local}")
                    return

                if self.ui.checkBox_cmp_text_data.isChecked():
                    if not os.path.isdir(path_orig_textdata):
                        self.show_msgbox_signal.emit("Error", f"Invalid path: {path_orig_textdata}")
                        return
                    if not os.path.isdir(path_new_textdata):
                        self.show_msgbox_signal.emit("Error", f"Invalid path: {path_new_textdata}")
                        return
                    td_text = uma_compare.TextDataCompare(path_orig_textdata, path_orig_local, path_new_textdata)
                    td_text.start_compare(progress_callback=self.update_bar_signal.emit,
                                          file_update_callback=self.files_update_callback)

                if self.ui.checkBox_cmp_stories.isChecked():
                    if not os.path.isdir(path_orig_jp):
                        self.show_msgbox_signal.emit("Error", f"Invalid path: {path_orig_jp}")
                        return
                    if not os.path.isdir(path_new_jp):
                        self.show_msgbox_signal.emit("Error", f"Invalid path: {path_new_jp}")
                        return
                    td_story = uma_compare.StoryDataCompare(path_orig_jp, path_orig_local, path_new_jp)
                    td_story.start_compare(progress_callback=self.update_bar_signal.emit,
                                           file_update_callback=self.files_update_callback,
                                           save_new_file=self.ui.checkBox_save_new.isChecked())
                time.sleep(0.5)
                self.show_msgbox_signal.emit("Success", f"Total: {self.cache_total_files}\n"
                                                        f"Update: {self.ui.listWidget_updated_files.count()}\n"
                                                        f"New: {self.ui.listWidget_new_files.count()}\n"
                                                        f"Error: {self.ui.listWidget_error_files.count()}\n")
            except BaseException:
                self.show_msgbox_signal.emit("Exception Occurred", traceback.format_exc())
            finally:
                self.set_start_button_enabled_signal.emit(True)

        Thread(target=_).start()

    def show_main_window(self):
        self.window.show()
        self.ui.lineEdit_orig_jp.setText(user_config.orig_jp_path)
        self.ui.lineEdit_orig_local.setText(user_config.orig_local_path)
        self.ui.lineEdit_new_jp.setText(user_config.new_jp_path)
        self.ui.lineEdit_orig_textdata.setText(user_config.orig_jp_textdata_path)
        self.ui.lineEdit_new_textdata.setText(user_config.new_jp_textdata_path)
        self.ui.checkBox_cmp_text_data.setChecked(user_config.compare_text_data)
        self.ui.checkBox_cmp_stories.setChecked(user_config.compare_stories)
        self.ui.checkBox_save_new.setChecked(user_config.save_new)

    def ui_run_main(self):
        self.show_main_window()
        exit_code = self.app.exec_()
        sys.exit(exit_code)
        # os._exit(self.app.exec_())
