#!/usr/bin/env python3
"""
Copyright 2015 Hippos Technical Systems BV.

@author: Larry Myerscough (aka papahippo)
"""
import sys, os, platform
from .raft import Raft
from .abcraft import AbcRaft, external
from . import (QtWidgets, dbg_print, version)
if 0:
    from .pyraft import PyRaft
    from .freqraft import FreqRaft
from .util.arghandler import ArgHandler
from . import Shared


class MusicMain(ArgHandler):
    def process_keyword_arg(self, a):
        if a in ('-X', '--external'):
            Shared.useExecsFromShare = False
            return a
        if a in ('-S', '--share'):
            Shared.useExecsFromShare = True
            return a
        if a in ('-ND', '--no-debug'):
            Shared.bitMaskDebug = False
            return a
        if a in ('-D', '--debug'):
            Shared.bitMaskDebug = True
            return a
        if a in ('-h', '--help'):
            print("GUI to edit sheet music built around the abcplus format.\n"
                  "syntax:  musicraft.py [options]\n"
                  "special options for musicraft.py are: (shown quoted but can and should be entered unquoted in most cases!)\n"
                  "'--external'     or equivalently '-X'\n"
                  "\tmeans use 'external' pre-installed versions of abcm2ps, abc2midi, etc.\n"
                  "\n"
                  "'--share'     or equivalently '-S'\n"
                  "\tmeans use the shared versions of abcm2ps, abc2midi, etc. which came bundled with musicraft.\n\n"
                  "\n"
                  "'--no-debug'   or equivalently '-ND'\n"
                  "\tmeans DO NOT provide debugging information.\n"
                  "\n"
                  "'--debug'   or equivalently '-D'\n"
                  "\tmeans DO provide debugging information.\n"
                  "\n"
                  )  # ... and return None to effectively follow through to show generic help blurb!
        return ArgHandler.process_keyword_arg(self, a)

    def main(self, Plugins=()):
        app = QtWidgets.QApplication(sys.argv)
        self.process_all_keyword_args()
        if Shared.useExecsFromShare:
            print("bundled shared executables will be used...")

        files = self.argv  # all remaining args are taken to be filenames
        raft = Raft()
        Shared.plugins = []
        for Plugin in Plugins:
            try:
                Shared.plugins.append(Plugin())
            except TypeError as exc:
                print(exc, file=sys.stderr)

        raft.start(files=files)
        try:
            sys.exit(app.exec_())
        except:
            pass


if __name__ == '__main__':
    musicMain = MusicMain()
    musicMain.main( Plugins=(AbcRaft,))  # PyRaft, FreqRaft))
