#!/usr/bin/python
"""
Copyright 2015 Hippos Technical Systems BV.

@author: larry
"""
import os
from .. import (Shared, QtWidgets, Printer, dbg_print, version)
from .score import Score
from .syntax import AbcHighlighter

from .external import (Abc2midi, Abcm2svg, Svg2PDF, Abc2abc, Abcm2ps, Ps2PDF)

from .midiplayer import MidiPlayer


class AbcRaft(object):

    myExts = ('.abc',)

    def __init__(self):
        Shared.abcRaft = self
        self.score = Score()
        self.abc2abc = Abc2abc()
        self.abc2midi = Abc2midi()
        self.svg2PDF = Svg2PDF()
        self.abcm2svg = Abcm2svg()
        self.abcm2ps = Abcm2ps()
        self.ps2PDF = Ps2PDF()

        Shared.raft.setWindowTitle(f"Musicraft version {version}")
        Shared.raft.displayBook.addTab(self.score, "Score")
        #Share.raft.displayBook.setFixedWidth(800)
        Shared.raft.editBook.fileLoaded.connect(self.checkLoadedFile)
        Shared.raft.editBook.fileSaved.connect(self.processSavedFile)

        self.midiPlayer = MidiPlayer()
        Shared.raft.menuBar().show()

    def forMe(self, filename):
        return os.path.splitext(filename)[1].lower() in self.myExts

    def checkLoadedFile(self, editor, filename):
        dbg_print(1, 'checkLoadedFile', filename)
        if not self.forMe(filename):
            return
        dbg_print(1, "we expect ABC syntax in " + filename)
        editor.highlighter = syntax.AbcHighlighter(editor.document(), editor)

    def processSavedFile(self, editor, filename,  dirName):
        if not self.forMe(filename):
            return
        cmd_processors = [
            Shared.abcRaft.abcm2ps,
            Shared.abcRaft.abcm2svg,
            Shared.abcRaft.abc2midi,
            Shared.abcRaft.abc2abc,
        ]
        self.makePdfOf = (not dirName) and filename  # don't make pdf when autosavin
        if not self.makePdfOf:
            # don't produce PDF unless we're maybe going to generate a PDF from it!
            cmd_processors = cmd_processors[1:]
        for c_p in cmd_processors:
            c_p.process(filename)
        editor.handleLull(forceSave=False, forceCursor=True)