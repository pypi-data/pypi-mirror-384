#!/usr/bin/env python3
"""
Copyright 2015 Hippos Technical Systems BV.

@author: larry
"""
import os
from .. import (Shared, dbg_print)
from .html_view import HtmlView
from .text_view import TextView
from .external import Python
from .syntax import PythonHighlighter


class PyRaft(object):

    myExts = ('.py', '.pyw')

    def __init__(self):
        Shared.pyRaft = self
        self.htmlView = HtmlView()
        Shared.raft.displayBook.addTab(self.htmlView, "Html")
        # defunct!?
        self.textView = TextView()
        Shared.raft.displayBook.addTab(self.textView, "Text")
        self.python = Python()
        Shared.raft.editBook.fileLoaded.connect(self.checkLoadedFile)
        Shared.raft.editBook.fileSaved.connect(self.processSavedFile)

    def forMe(self, filename):
        return os.path.splitext(filename)[1].lower() in self.myExts

    def checkLoadedFile(self, editor, filename):
        dbg_print(1, 'checkLoadedFile', filename)
        if not self.forMe(filename):
            return
        editor.highlighter = syntax.PythonHighlighter(editor.document())

    def processSavedFile(self, editor, filename,  dirName):
        if not self.forMe(filename):
            return
        cmd_processors = [
            self.python,
        ]
        for c_p in cmd_processors:
            c_p.process(filename)
        editor.handleLull(forceSave=False, forceCursor=True)