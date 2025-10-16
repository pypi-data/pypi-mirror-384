#!/usr/bin/python3
"""
Copyright 2016 Hippos Technical Systems BV.

@author: larry
"""
import sys
from .editbook import EditBook
from .. import (Shared, QtCore, QtWidgets, WithPrinter, Printer, dbg_print, AddMenu)
from .external import (StdOut, StdErr, External)
#import qdarkstyle

class StdBook(QtWidgets.QTabWidget):
    headerText = 'error/diagnostic output'
    whereDockable   = QtCore.Qt.AllDockWidgetAreas
    whereToDock = QtCore.Qt.LeftDockWidgetArea

    def __init__(self, dock=None):
        QtWidgets.QTabWidget.__init__(self)

class DisplayBook(QtWidgets.QTabWidget):
    headerText = 'styled output'
    whereDockable   = QtCore.Qt.AllDockWidgetAreas
    whereToDock = QtCore.Qt.RightDockWidgetArea

    def __init__(self, dock=None):
        QtWidgets.QTabWidget.__init__(self)


class Dock(QtWidgets.QDockWidget):
    def __init__(self, widgetClass, visible=True):
        QtWidgets.QDockWidget.__init__(self, widgetClass.headerText)
        self.setAllowedAreas(widgetClass.whereDockable)
        self.widget = widgetClass(dock=self)
        self.setWidget(self.widget)
        self.setVisible(visible)


class Raft(QtWidgets.QMainWindow, WithPrinter):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Shared.raft = self
        #self.resize(1024, 768)
        self.editBookDock = Dock(EditBook, True)
        self.addDockWidget(EditBook.whereToDock, self.editBookDock)
        self.editBook = self.editBookDock.widget
        self.stdBook = Dock(StdBook,  True)
        self.stdBook.setMinimumHeight(240)
        self.addDockWidget(StdBook.whereToDock, self.stdBook)
        if not Shared.bitMaskDebug:
            sys.stdout = StdOut()
            sys.stderr = StdErr()
        dbg_print(1, "testing stdout...", file=sys.stdout)
        dbg_print(1, "testing stderr...", file=sys.stderr)
        self.displayBookDock = Dock(DisplayBook)
        self.displayBook = self.displayBookDock.widget
        self.addDockWidget(DisplayBook.whereToDock, self.displayBookDock)
        WithPrinter.__init__(self)
        AddMenu(self,  '&File',
                [
                    ('&New', 'Ctrl+N', self.editBook.newFile,),
                    ('&Open', 'Ctrl+O', self.editBook.loadAnyFile,),
                    ('&Close', 'Ctrl+W', self.editBook.closeFile,),
                    ('Open in new &Instance', 'Ctrl+I', self.editBook.cloneAnyFile,),
                    ('&Reload', 'Ctrl+R', self.editBook.reloadFile,),
                    # neds attention... ('R&estart', 'Ctrl+E', self.editBook.restart,),
                    ('&Save', 'Ctrl+S', self.editBook.saveFile,),
                    ('Save &As', None, self.editBook.saveFileAs,),
                    ('E&xit', 'Ctrl+Q', self.editBook.exit_etc),
                    ('&Transpose', 'Ctrl+T', self.editBook.transpose,),
                ]
                )
        self.editBook.addMyMenu()

        AddMenu(self,  "&Help",
                [
                    ("About &Raft", None, self.about,),
                    # ("About &Qt", None, QtWidgets.qApp.aboutQt,),
                ], corner=QtCore.Qt.TopRightCorner)

    def start(self, files=()):
        self.show()
        try:
            self.editBook.openThemAll(files, force=True)
        except FileNotFoundError:
            print("warning: couldn't open initial file(s)!", file=sys.stderr)

    def about(self):
        QtWidgets.QMessageBox.about(self, "About 'Raft'",
                "<p>To be updated!.</p>"
                "<p></p>")

    def closeEvent(self, e):
        self.editBook.exit_etc()

    def menuItems(self):
        return
