# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
Copyright 2015 Hippos Technical Systems BV.
Created on Sun Aug 30 18:18:56 2015

@author: larry
"""
import sys, os, subprocess
from .. import (Signal, dbg_print, QtCore, QtGui, QtWidgets, WithPrinter,
                head_dir, AddMenu, NameFromDialog)
from .editor import Editor
from .find import Find


class EditBook(QtWidgets.QTabWidget, WithPrinter):
    menuTag = '&Edit'
    minimumWidth = 480
    minimumHeight =480
    interval = 100
    latency = 3
    filenamesDropped = Signal(list)
    settledAt = Signal(int, int)
    fileSaved = Signal(QtWidgets.QPlainTextEdit, str, str)
    fileLoaded = Signal(QtWidgets.QPlainTextEdit, str)

    whereDockable   = QtCore.Qt.AllDockWidgetAreas
    whereToDock = QtCore.Qt.LeftDockWidgetArea
    waitCondition = None
    latency = 8
    counted =0
    fileName = None
    minimumWidth = 400
    minimumHeight = 540 # 800
    closableTabs = True
    headerText = 'Editor'

    def __init__(self, dock=None):
        dbg_print(1, "EditBook.__init__", dock)
        #self.changeMarkers = QtGui.QIcon('/usr/share/xournal/pixmaps/pencil.png')
        self.dock = dock
        QtWidgets.QTabWidget.__init__(self)
        if self.minimumHeight:
            self.setMinimumHeight(self.minimumHeight)
        if self.minimumWidth:
            self.setMinimumWidth(self.minimumWidth)
        #self.setWidth(640)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.countDown)
        self.timer.start(self.interval)
        self.filenamesDropped.connect(self.openThemAll)
        self.currentChanged.connect(self.activateCurrent)
        self.tabCloseRequested.connect(self.closeThatEditor)
        self.setTabsClosable(self.closableTabs)
        WithPrinter.__init__(self)

    def addMyMenu(self):
        AddMenu(self, '&Edit', self.menuItems())


    def countDown(self, force=None):
        # dbg_print(1, 'countDown', self.counted)
        if force:
            self.counted = force
        if self.counted==0:
            return
        self.counted -=1
        if not self.counted:
            self.currentWidget().handleLull()

    def newFile(self):
        self.openThemAll(force=True)

    def openThemAll(self, filenames=(), force=False):
        if not self.count():
            force=True
        if force and not filenames:
            filenames = os.path.join(head_dir, 'share', 'abc', 'new.abc'),
        dbg_print(1, 'openThemAll', filenames)
        if not filenames:
            return
        for fn in filenames:
            ed = Editor(book=self)
            ed._index = self.addTab(ed, os.path.split(fn)[1])
            ed.loadFile(fn)
        self.setActiveEdit(ed)

    def setActiveEdit(self, ed):
        self.setCurrentWidget(ed)
        ed.this_editor_now_active()

    def loadAnyFile(self):
        fileName = NameFromDialog(
            QtWidgets.QFileDialog.getOpenFileName(self,
                                                  "Choose a data file",
                                                  #'.', '*.*'))
                                                  '.', '*.abc'))
        dbg_print(1, "loadAnyFile 2", fileName)
        self.openThemAll((fileName,))

    def cloneAnyFile(self):
        fileName = NameFromDialog(
            QtWidgets.QFileDialog.getOpenFileName(self,
                                                 "Choose a data file",
                                                 '', '*.abc'))
        dbg_print(1, "need to create new instance for", fileName)
        sys.argv[1:] = fileName,
        subprocess.Popen(sys.argv)
        return


    def activateCurrent(self, ix):
        if ix == -1:
            return  # presumabnley closing down!
        dbg_print(1, 'activateCurrent', ix)
        activeEdit = self.widget(ix)
        if not activeEdit.fileName:
            return
        self.setActiveEdit(activeEdit)
        # quick fix below needs to be improved!
        activeEdit.this_editor_now_active()
        activeEdit.handleLull()
        return activeEdit

    def transpose(self):
        self.currentWidget().transpose()

    def reloadFile(self):
        self.currentWidget().reloadFile()

    def saveFile(self):
        self.currentWidget().saveFile()

    def saveFileAs(self):
        self.currentWidget().saveFileAs()

    def closeFile(self, editor=None, ix=None, exit_pending=False):
        if editor is None:
            editor = self.currentWidget()
        if ix is None:
            ix = self.indexOf(editor)
        dbg_print(8, editor.saveState, editor.document().isModified())
        ret = editor.saveState == self.currentWidget().UNSAVED and QtWidgets.QMessageBox.warning(self,
                        "Close File" + (exit_pending and (" (on exit)") or ""),
                        f"There are unsaved changes in {self.currentWidget().fileName};\n"
                        f"Do you want to save your changes?",
                                                                                                 QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard |
                                                                                                 QtWidgets.QMessageBox.Cancel)
        if ret == QtWidgets.QMessageBox.Cancel:
            return ret
        if ret == QtWidgets.QMessageBox.Save:
            editor.saveFile()
        self.removeTab(ix)
        if not exit_pending:
            self.openThemAll()  # don't leave empty book!

    def restart(self):
        self.currentWidget().restart()

    def moveToRowCol(self, *location):
        self.currentWidget().moveToRowCol(*location)

    def closeThatEditor(self, ix):
        self.closeFile(ix=ix, editor=self.widget(ix))
        self.openThemAll()

    def exit_etc(self):
        while self.count():
            ret = self.closeFile(exit_pending=True)
            if ret == QtWidgets.QMessageBox.Cancel:
                return False
        sys.exit()

    def findReplace(self):
        pass

    def menuItems(self):
        return [
                    ('&Find/Replace',           'Ctrl+F', Find(self).show,),

        ]
