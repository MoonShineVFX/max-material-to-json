'''
Created on 2020-6-9

@author: noflame.lin
'''

import os
import sys
local_path = os.path.dirname(__file__)
if local_path not in sys.path:
    sys.path.append(local_path)

from PySide2 import QtWidgets, QtCore
# import pymxs
# rt = pymxs.runtime
# import MaxPlus as MP
# import qtmax
import coordinator
reload(coordinator)


class Mat2Houdini_ui(QtWidgets.QWidget):
    do_export = QtCore.Signal(str, str)
    selected_folder = QtCore.Signal(str)

    def __init__(self, parent=None, out_folder="", filename=""):
        self.out_folder = out_folder
        self.filename = filename if filename else "untitled"
        super(Mat2Houdini_ui, self).__init__(parent)
        self.go_btn = QtWidgets.QPushButton()
        self.go_btn.setText('GO!')
        self.pick_folder_btn = QtWidgets.QPushButton()
        self.pick_folder_btn.setText('...')
        self.folder_edt = QtWidgets.QLineEdit()
        self.folder_edt.setText(self.out_folder)
        self.filename_edt = QtWidgets.QLineEdit()
        self.filename_edt.setText(filename)

        main_lay = QtWidgets.QVBoxLayout()
        h_lay1 = QtWidgets.QHBoxLayout()
        h_lay1.addWidget(QtWidgets.QLabel("Folder"))
        h_lay1.addWidget(self.folder_edt)
        h_lay1.addWidget(self.pick_folder_btn)
        
        h_lay2 = QtWidgets.QHBoxLayout()
        h_lay2.addWidget(QtWidgets.QLabel("File Name"))
        h_lay2.addWidget(self.filename_edt)
        h_lay2.addStretch()

        main_lay.addLayout(h_lay1)
        main_lay.addLayout(h_lay2)
        main_lay.addWidget(self.go_btn)
        self.setLayout(main_lay)
        self.setMinimumWidth(400)
#         self.setWindowFlags(QtCore.Qt.Window)

        self.go_btn.clicked.connect(self.emit_do_mat_to_houdini)
        self.pick_folder_btn.clicked.connect(self.select_output_folder)

    def emit_do_mat_to_houdini(self):
        self.do_export.emit(self.folder_edt.text(),
                                    self.filename_edt.text())

    def select_output_folder(self):
        pre_folder = self.folder_edt.text()
        if os.path.isdir(pre_folder) and os.path.exists(pre_folder):
            selected_directory = QtWidgets.QFileDialog.getExistingDirectory(dir=pre_folder)
        else:
            selected_directory = QtWidgets.QFileDialog.getExistingDirectory()

        if selected_directory:
            self.selected_folder.emit(selected_directory)
            self.out_folder = selected_directory
            self.folder_edt.setText(selected_directory)

    def showMessage(self, txt):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setText(txt)
        msgBox.exec_()


class Mat2Json(object):
    major = 0
    minor = 1
    fix = 0

    def __init__(self):
        file_name = coordinator.dcc_file_name()
        if file_name:
            _filename = file_name[:-4]
        else:
            _filename = 'untitled'
        export_path = coordinator.dcc_export_folder()
        self.ui = Mat2Houdini_ui(out_folder=export_path, filename=_filename)
        self.ui.do_export.connect(self.export)
        coordinator.set_parent(self.ui)
#         elf.ui.set_parent(qtmax.GetQMaxMainWindow())

    def export(self, folder, filename):
        if not os.path.isdir(folder):
            self.ui.showMessage(u"請選擇目錄")
            return
        if not os.path.exists(folder):
            self.ui.showMessage(u"目錄不存在")
            return

        output_file = os.path.join(folder, filename)
        output_file_abc = output_file + '.abc'
        output_file_json = output_file + '.json'
        output_file_table = output_file + '.table'

        try:
            coordinator.export_abc(output_file_abc)
        except Exception as e:
            self.ui.showMessage('coordinator abc Error: ' + repr(e))
        coordinator.export_mat(output_file_json)
        coordinator.export_mapping_table(output_file_table)

    def show(self):
        self.ui.show()


m2j = Mat2Json()
m2j.show()
print('ok')