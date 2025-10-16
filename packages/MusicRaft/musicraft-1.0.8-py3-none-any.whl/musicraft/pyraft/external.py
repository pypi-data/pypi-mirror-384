#!/usr/bin/python
# -*- encoding: utf8 -*-
"""
Copyright 2015 Hippos Technical Systems BV.
Module 'external' within package 'abcraft' relates to the various
command processors (abc2midi etc.) which are executed by abccraft, and to
their assocated widgets and methods.
"""
from .. import (Shared)
from ..raft.external import External

HTML_PREAMBLE = "Content-type: text/html"


class Python(External):
    """
class Python -
    """
    fmtNameIn  = '%s.py'
    fmtNameOut = '%s.html'  # ? maybe unused
    exec_dir = '/usr/bin/'
    exec_file = 'python3'

    def cmd(self, inF, outF, **kw):
        print(outF)
        Shared.pyRaft.htmlView.fileName = outF  # quick and dirty fix!
        return External.cmd(self, inF)

    def fixup(self, output, error):
        before, *afters = output.split(HTML_PREAMBLE)
        if afters:
            Shared.pyRaft.htmlView.showOutput(*afters)
            Shared.raft.displayBook.setCurrentWidget(Shared.pyRaft.htmlView)
            output = ''
        else:
            Shared.pyRaft.textView.showOutput(output)
        return output, error
