#!/usr/bin/env python3
"""
Copyright 2015 Hippos Technical Systems BV.
(but borrows somme code from the painting/svgviewer example of PyQt v4.x)

@author: larry
n.b. text_view.py is defunct... for now! just use normal stdout window! why not?  
"""

from .. import (dbg_print, QtWidgets, WithPrinter)

class TextView(QtWidgets.QPlainTextEdit, WithPrinter):  # , AddMenu

    menuTag = '&Text'

    def menuItems(self):
        return

    def __init__(self):
        dbg_print(1, "TextView.__init__")
        QtWidgets.QPlainTextEdit.__init__(self)
        WithPrinter.__init__(self)
        # AddMenu(self, &Text',
        #[
            #                    ('Set &Font', 'F', self.changeMyFont,),
        #])

    def showOutput(self, text_bytes):
        self.setPlainText(text_bytes)

    def showAtRowAndCol(self, row, col):
        pass  # for now!

    def locateXY(self, x, y):
        pass  # for now!
