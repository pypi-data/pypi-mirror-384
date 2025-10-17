#!/usr/bin/env python
#!/usr/bin/env python
"""
Play MIDI file on output port.

Run with (for example):

    ./play_midi_file.py 'SH-201 MIDI 1' 'test.mid'
"""

import sys
from .. import (Shared, Signal, dbg_print, QtCore, QtGui, QtWidgets, AddMenu, mido)

def stuffer_func(func, *stuff):
    def fn(*p, **kw):
        return func(*(stuff+p), *kw)
    return fn

class MidiOutputDialog(QtWidgets.QDialog):

    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)

        self.setWindowTitle("Select MIDI output")

        # QBtn = QtWidgets.QDialogButtonBox.Apply | QtWidgets.QDialogButtonBox.Cancel
        QBtn = QtWidgets.QDialogButtonBox.Cancel

        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout = QtWidgets.QVBoxLayout()
        for name in [None] + mido.get_output_names():
            rb = QtWidgets.QRadioButton(name or 'default')
            self.layout.addWidget(rb)
            rb.toggled.connect(stuffer_func(parent.open_output, name))
            if name == parent.midiPort:
                rb.setChecked(True)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


class MidiPlayer(QtWidgets.QWidget):
        
    lineAndCol = Signal(int, int)

    output = None
    midiPort = None

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        if not mido:
            print("module 'mido' not found; midi playing within musicraft will not be possible.")
            return  # mido package not available
        self.lineAndCol.connect(Shared.abcRaft.score.showAtRowAndCol)
        try:
            self.midiPort = mido.get_output_names()[-1]
        except IndexError:
            print("no midi hardware port present and no midi synthesizer running, so can't play midi files.")
            return
            
        self.open_output(self.midiPort)

        AddMenu(self, "&Midi",
                [
                    ("Select Midi &Output", None, self.select_midi_output_,),
                    ("Start &Midi", 'Ctrl+M', self.start_midi,),
                    ("Pause/Resume M&idi", 'Ctrl+,', self.pause_midi,),
                ]
                )

    def select_midi_output_(self):
        mod = MidiOutputDialog(self)
        mod.show()

    def open_output(self, name=None, open_not_close=True):
        if not open_not_close:
            self.output.reset()
            self.output = None
            return
        if self.output and name==self.midiPort:
            return
        try:
            self.output = mido.open_output(name)
        except IOError as exc:
            print ("sorry; couldn't setup MIDI player; exception details follow <<<", file=sys.stderr)
            print (exc, file=sys.stderr)
            print (f">>>. Perhaps changing midiPort (currently {name}) will help", file=sys.stderr)
            self.midiPort = None
        self.midiPort == name
        print(f'MidiPlayer.open_output succeeded, port="{name}".')

    def start_midi(self):
        filename = Shared.abcRaft.abc2midi.outFileName
        if not filename:
            print(f"no MIDI file aailable", file=sys.stderr)
            return
        if not self.output:
            print(f"no MIDI device selected (or none available)", file=sys.stderr)
            return
        print(f'playing midi file "{filename}".')
        self.output.reset()
        self.accum = dict([(i, 0) for i in range(110, 115)])
        self.midiFile = mido.MidiFile(filename)
        self.messages = self.midiFile.__iter__() # self.midiFile.play()
        self.pendingMessage = None
        self.paused = False
        self.cueMessage()

    def pause_midi(self):
        self.paused = not self.paused
        self.cueMessage()

    def cueMessage(self):
        if self.paused:
            return
        message = self.pendingMessage
        self.pendingMessage = None
        while True:
            if message:
                if not isinstance(message, mido.MetaMessage):
                    if message.type == 'control_change':
                        self.accum[message.control] = message.value
                    else:
                        self.output.send(message)
                        lineNo = ((self.accum[110]<<14)
                                 +(self.accum[111]<<7)
                                 + self.accum[112])
                        colNo =  ((self.accum[113]<<7)
                                 + self.accum[114])
                        self.lineAndCol.emit(lineNo, colNo-1)
            try:
                message = next(self.messages)
            except StopIteration:
                dbg_print(1, 'cue_msg; StopIteration')
                return
            dbg_print(1, message.type, message)
            if message.time != 0:
                break
        self.pendingMessage = message
        milliseconds = int(message.time * 1000)
        QtCore.QTimer.singleShot(milliseconds, self.cueMessage)

    def __del__(self):
        dbg_print(1, 'MidiPlayer:__del__',)
        #self.output.reset()

if __name__ == '__main__':
    class MainWindow(QtWidgets.QMainWindow):
        def __init__(self):
            super(MainWindow, self).__init__()
    
            self.midiPlayer = MidiPlayer()
    
            fileMenu = QtGui.QMenu("&File", self)
            quitAction = fileMenu.addAction("E&xit")
            quitAction.setShortcut("Ctrl+Q")
    
            self.menuBar().addMenu(fileMenu)
    
    
            quitAction.triggered.connect(QtGui.qApp.quit)
    
            self.setCentralWidget(self.midiPlayer)
            self.setWindowTitle("MidiPlayer")
            self.midiPlayer.lineAndCol.connect(self.showLocation)
            self.midiPlayer.play(
                (len(sys.argv)>1 and sys.argv[1]) or './MarThruAm_timp.midi')
            #self.resize(self.view.sizeHint() + QtCore.QSize(
            #    80, 80 + self.menuBar().height()))

        def showLocation(self, lineNo, colNo):
            dbg_print(1, 'showLocation(line, col)', lineNo, colNo)

    app = QtGui.QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
