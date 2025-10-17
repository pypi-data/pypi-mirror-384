from . import  (QtPrintSupport, QtWidgets, QtGui)
import os
from ast import literal_eval

class Shared:
    bitMaskDebug = literal_eval(os.getenv('MUSICRAFT_DBG', '0'))
    useExecsFromShare = True

def dbg_print(bitMask, *pp, **kw):
    if bitMask & Shared.bitMaskDebug:
        print(*pp, **kw)


class Printer(QtPrintSupport.QPrinter):
    pageSize = QtPrintSupport.QPrinter.A4
    paperSize = QtPrintSupport.QPrinter.A5
    margins = (15, 15, 15, 15)

    def __init__(self):
        dbg_print(1, "Printer.__init__")
        QtPrintSupport.QPrinter.__init__(self, QtPrintSupport.QPrinter.HighResolution)
        self.setOrientation(QtPrintSupport.QPrinter.Portrait)
        self.setPageSize(self.pageSize)
        self.setPaperSize(self.paperSize)
        self.setPageMargins(*self.margins, QtPrintSupport.QPrinter.Millimeter)
        dbg_print(1, "!Printer.__init__")


class WithPrinter(object):

    def __init__(self):
        self.printer = Printer()
        self.compositeName = 'temp'  # under review, like so much!



    def printAll(self, toPDF=False):
        # fileName = self.compositeName +'.pdf'
        fileName = os.path.splitext(Shared.raft.editBook.currentWidget().fileName)[0] + '.pdf'
        print(fileName)
        if toPDF:
            files = QtWidgets.QFileDialog.getSaveFileName(self,
                "write PDF to file", fileName, '*.pdf')
            fileName = files[0]
            if not fileName:
                return
        self.printer.setDocName(fileName)
        self.printer.setOutputFileName(toPDF and fileName or '')
        self.renderAll(QtGui.QPainter(self.printer))

    def renderAll(self, painter):
        self.scene().render(painter)

    def printAllToPDF(self):
        self.printAll(toPDF=True)

def MyQAction(owner, menuText, shortcut=None, triggered=None, enabled=None,
              checkable=None, checked=None):
    action = QtWidgets.QAction(menuText, owner)
    if shortcut:
        action.setShortcut(shortcut)
    if triggered:
        action.triggered.connect(triggered)
    if enabled is not None:
        action.setEnabled(enabled)
    if checkable is not None:
        action.setCheckable(checkable)
    if checked is not None:
        action.setChecked(checked)
    return action

def AddMenu(owner, menuTag, menuItems, corner=None):
    menuBar = mainMenuBar = Shared.raft.menuBar()
    if corner:
        menuBar = QtWidgets.QMenuBar(mainMenuBar)
        mainMenuBar.setCornerWidget(menuBar, corner=corner)
    menu = menuBar.addMenu(menuTag)
    for tag, shortcut, func in menuItems:
        action = MyQAction(owner, tag, shortcut=shortcut, triggered=func)
        menu.addAction(action)



