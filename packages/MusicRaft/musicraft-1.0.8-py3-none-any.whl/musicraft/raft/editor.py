#!/usr/bin/env python3
#partially based on: http://john.nachtimwald.com/2009/08/15/qtextedit-with-line-numbers/ (MIT license)
import sys, os, subprocess
from .. import (Shared, Signal, dbg_print, QtCore, QtGui, QtWidgets,
                temp_dir, packagePathName, NameFromDialog, DeltaOfEvent)


class Editor(QtWidgets.QPlainTextEdit):

    headerText = 'Editor'

    saveStateIconFilenames = (
            'lightgreen.png',
            'yellow.png',
            'red.png'
    )
    (SAVED, UNSAVED, BUSY) = range(3)  # indices within above. (ought I to use enums like normal coders?)
    saveState = BUSY
    prevCursorPos = -1
    currentLineColor = None
    editBecomesActive = Signal()
    fileName = None
    highlighter = None
    pointSizeF = 11.0
    cursorWidth = 8

    def __init__(self, book=None, **kw):
        self.book = book
        QtWidgets.QPlainTextEdit.__init__(self, **kw)
        self.lineNumberArea = self.LineNumberArea(self)
        self.viewport().installEventFilter(self)
        self.saveStateMarkers = [QtGui.QIcon(packagePathName(icon_file_name, 'share', 'pixmaps'))
                                 for icon_file_name in self.saveStateIconFilenames]

        self.newDocument = True
        self.path = ''
        css = '''
        QPlainTextEdit {
          font-family: monospace;
          font-size: 10;
          color: black;
          background-color: white;
          selection-color: white;
          selection-background-color: #437DCD;
        }'''
        self.setStyleSheet(css)

        font = self.font()
        font.setPointSize(int(self.pointSizeF))
        self.setFont(font)
        self.setCursorWidth(self.cursorWidth)
        self.setWindowTitle('title')
        self.textChanged.connect(self.handleTextChanged)
        self.modificationChanged.connect(self.handleModificationChanged)
        #self.editBecomesActive.connect(self.this_editor_now_active)
        self.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.cursorPositionChanged.connect(self.handleCursorMove)
        self.originalText = None
        self.haveLoadedFile = False
        self.dirName = ''

    def Quote(self):
        tC = self.textCursor()
        c0 = '#' # dummy non-match!
        while c0 not in "ABCDEFG":
            tC.movePosition(tC.Left, tC.KeepAnchor)
            sel = tC.selectedText()
            c0 = sel[0]
        tC.removeSelectedText()
        tC.insertText('"'+ sel +'"')

    def handleCursorMove(self):
        self.book.counted = self.book.latency
        return

    def moveToRowCol(self, row=1, col=0):
        block = self.document().findBlockByLineNumber (row-1)
        desiredPosition = block.position() + col
        dbg_print(1, 'AbcEditor.moveToRowCol', row, col,
               'desiredPosition', desiredPosition)
        tc = self.textCursor()
        tc.setPosition(desiredPosition)
        self.setTextCursor(tc)
        self.setFocus()
        if self.highlighter:
            self.highlighter.rehighlight()

    def highlight(self, tc):
        # n.b. unfortunate name - no relation to highlighter!
        blockNumber = tc.blockNumber()
        # Common.blockNumber = blockNumber
        col0 =  col = tc.positionInBlock()
        l = tc.block().length()
        blockText = tc.block().text()
        while col and ((col >= (l-1))
            or not (str(blockText[col]).lower() in 'abcdefg^_=')):
            col -= 1
        dbg_print(1, 'editor.highlight: row=%d, col=%d' %(blockNumber, col))
        self.book.settledAt.emit(blockNumber+1, col)

    def this_editor_now_active(self):
        dbg_print(1, f"this_editor_now_active {self.fileName}, index {self.book.currentIndex()};")
        if self.dirName:
            dbg_print(1, f" #  will chd to... '{self.dirName}'")
            os.chdir(self.dirName)
        # self.handleTextChanged()
        self.handleLull(forceSave=True, forceCursor=True)

    def setChangeState(self, saveState):
        oldState = self.saveState
        self.book.setTabIcon(self.book.currentIndex(), self.saveStateMarkers[saveState])
        self.saveState = saveState
        dbg_print(8, f"saveState: {oldState}->{saveState}")
        return oldState

    def handleTextChanged(self):
        # self.document().setModified(True) no causes looping!
        dbg_print(8, 'handleTextChanged', self.book.counted, self.saveState, self.document().isModified())
        if not self.document().isModified():
            return
        self.book.counted = self.book.latency
        if self.saveState is self.SAVED:  # n.b. not self BUSY!
            self.setChangeState(self.UNSAVED)
        if self.highlighter:
            self.blockSignals(True)
            self.highlighter.rehighlight()
            self.blockSignals(False)

    def handleModificationChanged(self, changed):  # experimental
        dbg_print(8, f"--- handleModificationChanged {changed}")

    def handleLull(self, forceSave=False, forceCursor=False):
        # there is such a thing as too much debug info!:
        #
        dbg_print(1, f"handleLull {forceSave, forceCursor}")

        if forceSave or self.document().isModified():
            dbg_print(1, "autoSave")
            self.saveFile(temp_dir)
                # fileName = temp_dir + '/autosave_' + self.shortName, temporary = True)
        tc = self.textCursor()
        position = tc.position()
        if forceCursor or position != self.prevCursorPos:
            self.prevCursorPos = position
            self.highlight(tc)

    def newFile(self, fileName='new.abc'):
        self.clear()
        self.setFileName(fileName)
        self.book.fileLoaded.emit(self, self.fileName)

    def closeFile(self):
        self.clear()
        self.haveLoadedFile = False

    def restart(self):
        self.loadFile(self.fileName)
        sys.exit(0)

    def loadFile(self, fileName, newInstance=None, row=1, col=0):
        dbg_print(1, "Editor.loadFile", fileName, newInstance, row, col)
        self.setChangeState(self.BUSY)
        self.highlighter = None  # default, half-expecting to be overwritten by per-extension handler
        self.setFileName(fileName)
        f = QtCore.QFile(self.shortName)
        dbg_print(1, os.getcwd())
        if not f.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text):
            return
        self.readAll(f)
        f.close()
        dbg_print(1, "Loaded %s" % fileName)
        self.book.fileLoaded.emit(self, self.fileName)
        #Shared.abcRaft.checkLoadedFile(self, self.fileName)
        self.moveToRowCol(row, col)  # primarily to gain focus!
        self.document().setModified(True) # force rewrite of Score
        # ?? self.book.fileSaved.emit(self, fileName)  # ???
        #self.saveFile(temp_dir)
        #self.handleLull()
        if not dir:
            self.document().setModified(False)
        self.setChangeState(self.SAVED)

    def setFileName(self, fileName=None):
        if fileName is not None:
            self.fileName = fileName
        afn = os.path.abspath(self.fileName)
        title = "%s - %s" % (self.headerText, afn)
        dbg_print(1, title)
        self.book.dock.setWindowTitle(title)
        self.dirName, self.shortName = os.path.split(afn)
        os.chdir(self.dirName)
        dbg_print(1, f"current dir is now '{self.dirName}'")
        self.haveLoadedFile = True

    def readAll(self, f):
        dbg_print(1, 'readAll', self, f)
        stream = QtCore.QTextStream(f)
        text = stream.readAll()
        self.setPlainText(text)

    def saveFile(self, dir=''):
        oldSaveState = self.setChangeState(self.BUSY)
        fileToWrite = os.path.join(dir, self.shortName)
        dbg_print(1, f"Saving file '{fileToWrite}'.  current directory is '{os.getcwd()}'" )
        out = open(fileToWrite, 'w')
        if not out:
            return
        self.writeAll(out)
        out.close()
        dbg_print(1, f"Saved file {fileToWrite}.  current directory is {os.getcwd()}" )

        # don't treat autosave as a real save. we want to warn if exit done now!
        self.setChangeState(dir and oldSaveState or self.SAVED)
        self.document().setModified(False)
        self.book.fileSaved.emit(self, fileToWrite, dir)  # ???
        # done via signal recipient... self.handleLull(forceSave=False, forceCursor=True)

    def transpose(self):
        semitones, ok = QtWidgets.QInputDialog().getInt(self,
                "Transpose (automatic clef change(s))",
                "semitones (+/- for up/down:)", 0, -50, 50, 1)
        if not ok:
            return
        newFileName, ok  = QtWidgets.QFileDialog.getSaveFileName(self, "write tansposed to file",
                            "transposed.abc",
                            "(*.abc)")
        if not ok:
            return
        transposedText = Shared.abcRaft.abc2abc.process(self.fileName, transpose=semitones)
        with open(newFileName, 'w') as transposed_file:
            transposed_file.write(transposedText)
        self.book.openThemAll((newFileName,))

    def writeAll(self, out):
        text = self.toPlainText()
        # dbg_print(1, 'len(text)=', len(text))
        out.write(text)

    def reloadFile(self):
        dbg_print(1, "ReloadFile", self.fileName)
        self.loadFile(self.shortName)

    def saveFileAs(self, fileName=None):
        """
        save the current panel contents to a new file.
        """
        fileName = NameFromDialog(
            QtWidgets.QFileDialog.getSaveFileName(self, "Save source to file as", '', '*.abc'))
        if not fileName:
            return
        self.setFileName(fileName)
        self.saveFile()
        # self.book.setTabText(self.book.currentIndex(), os.path.split(fileName)[1])
        self.book.setTabText(self.book.currentIndex(), self.shortName)

    def resizeEvent(self,e):
        self.lineNumberArea.setFixedHeight(self.height())
        QtWidgets.QPlainTextEdit.resizeEvent(self,e)

    def eventFilter(self, object, event):
        if object is self.viewport():
            self.lineNumberArea.update()
            return False
        return QtWidgets.QPlainTextEdit.eventFilter(self, object, event)

    def keyPressEvent(self, event):
        """Reimplement Qt method"""
        key = event.key()
        # print (event.nativeScanCode(), file=sys.__stderr__)
        meta = event.modifiers() & QtCore.Qt.MetaModifier
        ctrl = event.modifiers() & QtCore.Qt.ControlModifier
        shift = event.modifiers() & QtCore.Qt.ShiftModifier
        plain = not (meta or ctrl or shift)
        if key == QtCore.Qt.Key_Insert and plain:
            self.setOverwriteMode(not self.overwriteMode())
        if key == QtCore.Qt.Key_Tab and plain and self.highlighter:
            return self.autoComplete(event)
        else:
            QtWidgets.QPlainTextEdit.keyPressEvent(self, event)

    def autoComplete(self, event):
        dbg_print(1, 'autoComplete')
        tc = self.textCursor()
        snippet = self.highlighter.getSnippet(tc)
        for i, piece in enumerate(snippet):
            tc.insertText(piece)
            if i==0:
                pos = tc.position()
        tc.setPosition(pos)
        self.setTextCursor(tc) 

    def getSnippet(self, tc):    #------ Drag and drop
        col0 = col = tc.positionInBlock()
        block = tc.block()
        l = block.length()
        dbg_print(1, "ABC get snippet", l)
        blockText = block.text()
        while col and str(blockText[col - 1]) not in ' |![],(){}.-/':
            tc.deletePreviousChar()
            col -= 1
        key = blockText[col:col0]
        #dbg_print(1, "autoComplete key %d:%d '%s'" % (col, col0, key))
        print("autoComplete! key %d:%d '%s'" % (col, col0, key))
        return self.snippets.get(key, ("!%s!" % key,))

    def dragEnterEvent(self, event):
        """Reimplement Qt method
        Inform Qt about the types of data that the widget accepts"""
        source = event.mimeData()
        if source.hasUrls():

            if 1: #mimedata2url(source, extlist=EDIT_EXT):
                dbg_print(1, "dragEnterEvent", "hasUrls")
                event.acceptProposedAction()
            else:
                event.ignore()
        elif source.hasText():
            dbg_print(1, "dragEnterEvent", "hasText")
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        """Reimplement Qt method
        Unpack dropped data and handle it"""
        source = event.mimeData()
        if source.hasUrls():
            #paths = map(filenameFromUrl, source.urls())
            paths = [url.path() for url in source.urls()]
            dbg_print(1, "dropEvent", "hasUrls", source.urls(), paths)
            self.book.filenamesDropped.emit(paths)
        elif source.hasText():
            dbg_print(1, "dropEvent", "hasText")
            #editor = self.get_current_editor()
            #if editor is not None:
            #    editor.insert_text( source.text() )
        event.acceptProposedAction()

    def mousePressEvent(self, mouseEvent):
        ## if (mouseEvent.button() in (QtCore.Qt.LeftButton, QtCore.Qt.RightButton)):
        dbg_print(1, f"mouseEvent.button()={mouseEvent.button()}")
        QtWidgets.QPlainTextEdit.mousePressEvent(self, mouseEvent)
        return


    def wheelEvent(self, event):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers != QtCore.Qt.ControlModifier:
            return QtWidgets.QPlainTextEdit.wheelEvent(self, event)
        delta = DeltaOfEvent(event)
        new_sizeF = self.pointSizeF + (delta / 100.0)
        dbg_print(1, f"Editor.wheelEvent, {delta=}; new_sizeF={new_sizeF}", )
        if new_sizeF > 0:
            self.pointSizeF = new_sizeF
            self.font().setPointSizeF(new_sizeF)
            if self.highlighter:
                self.highlighter.rehighlight()
        event.accept()


    class LineNumberArea(QtWidgets.QWidget):

        def __init__(self, editor):
            QtWidgets.QWidget.__init__(self, editor)
            self.edit = editor
            self.highest_line = 0
            css = '''
            QWidget {
              font-family: monospace;
              font-size: 10;
              color: black;
            }'''
            self.setStyleSheet(css)
 
        def update(self, *args):
            width = QtGui.QFontMetrics(
                self.edit.document().defaultFont()).width(
                    str(self.highest_line)) + 10
            if self.width() != width:
                self.setFixedWidth(width)
                self.edit.setViewportMargins(width,0,0,0)
            QtWidgets.QWidget.update(self, *args)
 
        def paintEvent(self, event):
            page_bottom = self.edit.viewport().height()
            font_metrics = QtGui.QFontMetrics(
                self.edit.document().defaultFont())
            current_block = self.edit.document().findBlock(
                self.edit.textCursor().position())
 
            painter = QtGui.QPainter(self)
            painter.fillRect(self.rect(), QtCore.Qt.lightGray)
            
            block = self.edit.firstVisibleBlock()
            viewport_offset = self.edit.contentOffset()
            line_count = block.blockNumber()
            painter.setFont(self.edit.document().defaultFont())
            while block.isValid():
                line_count += 1
                # The top left position of the block in the document
                position = self.edit.blockBoundingGeometry(block).topLeft() + viewport_offset
                # Check if the position of the block is out side of the visible area
                if position.y() > page_bottom:
                    break
 
                # We want the line number for the selected line to be bold.
                bold = False
                x = self.width() - font_metrics.width(str(line_count)) - 3
                y = round(position.y()) + font_metrics.ascent()+font_metrics.descent()-1
                if block == current_block:
                    bold = True
                    font = painter.font()
                    font.setBold(True)
                    painter.setFont(font)
                    pen = painter.pen()
                    painter.setPen(QtCore.Qt.red)
                    painter.drawRect(0, y-14, self.width()-2, 20)
                    painter.setPen(pen)
                    
                # Draw the line number right justified at the y position of the
                # line. 3 is a magic padding number. drawText(x, y, text).
                painter.drawText(x, y, str(line_count))
 
                # Remove the bold style if it was set previously.
                if bold:
                    font = painter.font()
                    font.setBold(False)
                    painter.setFont(font)
 
                block = block.next()
 
            self.highest_line = line_count
            painter.end()
 
            QtWidgets.QWidget.paintEvent(self, event)
