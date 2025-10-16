#!/usr/bin/env python3
"""
Copyright 2015 Hippos Technical Systems BV.
removed stuff from git whch didnhy@author: larry
"""

import sys, os, re, time
import lxml.etree
from pdfrw import PdfReader, PdfWriter
import numpy as np
from collections import OrderedDict
from .. import (Shared, dbg_print, QtCore, QtGui, QtWebEngine, QtWebEngineWidgets, QtWidgets, WebView, DeltaOfEvent,
                WithPrinter, AddMenu, temp_dir)


class MyScene(QtWidgets.QGraphicsScene):

    def mousePressEvent(self, event):
        scP = event.scenePos()
        x = scP.x()
        y = scP.y()
        dbg_print(1, "MyScene.mousePressEvent: " +
                  # event.pos(), event.scenePos(), event.screenPos()
                  'scenePos x,y =' + str(x) + ',' + str(y), '  button =' + str(event.button()),
                  'scene width =' + str(self.width()) + ' scene height =' + str(self.height()),
                  Shared.raft.editBook.currentWidget().shortName,
                  self.parent())
        if event.button() == 1:
            self.parent().locateXY(x, y)
            event.accept()
        else:
            event.ignore()

    def wheelEvent1(self, event):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if not (modifiers & QtCore.Qt.ControlModifier):
            return QtGui.QGraphicsScene.wheelEvent(self, event)
        delta = DeltaOfEvent(event)
        factor = 1.2 ** (delta / 120.0)
        # self.scale(factor, factor)
        # self.mustApplyTransform = self.transform()
        dbg_print(1, f"MyScene.wheelEvent, {delta=}")
        event.accept()


class SvgDigest:
    ringColour = 'green'

    locatableTypes = ('N', 'R', 'Z')
    scene = None

    def __init__(self, fileName):
        self.svg_file = QtCore.QFile(fileName)
        self.quickDic = {}
        self.svg_tree = self.cursorsDad = None
        self.row_col_dict = OrderedDict()
        self.buildQuickDic()

    def AdjustForScene(self, scene):
        self.scene = scene

    def buildQuickDic(self):
        """ extract the all-imortant information from the .svg
            file which enables us to correlate locations within the
            image with locations within the source abc file.
            N.B. row/col/cursor related stuff is being gradually phased
            out from this function.
        """
        fileName = str(self.svg_file.fileName())

        for attr, dtype in (('row', np.int32), ('col', np.int32),
                            ('x', float), ('y', float),
                            ('scale', float)):
            self.quickDic[attr] = np.array([], dtype=dtype)

        self.svg_tree = lxml.etree.parse(fileName)
        self.abcEltAtCursor = self.eltCursor = dad = None
        eltHead = eltAbc = None
        scale_ = 1.0
        for elt in self.svg_tree.iter():
            if callable(elt.tag):
                continue
            tag_ = elt.tag.split('}')[1]  # get rid of pesky namespace prefix
            if (tag_ == 'abc'
                    and (elt.get('type') in self.locatableTypes)):
                eltAbc = elt  # ready to be paired up with a notehead element
            elif tag_ == 'use':
                attr, val = elt.items()[-1]
                # look for normal note heads and also the special percussion note heads
                if attr.endswith(
                        'href'):  # and val.lower() in ('#hd', '#dsh0', '#pshhd', '#pfthd', '#pdshhd', '#pdfthd'):
                    eltHead = elt  # ready to be paired up with an 'abc' element
            elif tag_ == 'g':
                tf_ = elt.get('transform')
                if not tf_:
                    continue
                scale_match = re.match(r'scale\((.*)\)', tf_)
                if scale_match:
                    try:
                        tagje = elt.getchildren()[0].tag
                    except IndexError:
                        continue
                    if (not callable(tagje)) and tagje.split('}')[1] == 'defs':  # get rid of pesky namespace prefix
                        continue  # ignore this special scaling (for "Q:" or similar)
                    try:
                        scale_ = float(scale_match.group(1))
                    except ValueError:
                        continue
                    # dbg_print(1, "SvgDigest: scale according to g encountered en passant =", scale_)
                continue
            else:
                continue
            if eltAbc is None or eltHead is None:
                continue
            # we've 'paired' a note-head and an ABC note description; hurrah!
            sx_ = eltHead.get('x')
            sy_ = eltHead.get('y')
            row_ = int(eltAbc.get('row'))
            col_ = int(eltAbc.get('col'))
            type_ = eltAbc.get('type')
            if not (sx_ and sy_):
                continue
            self.quickDic['x'] = np.append(self.quickDic['x'], scale_ * float(sx_))
            self.quickDic['y'] = np.append(self.quickDic['y'], scale_ * float(sy_))
            self.quickDic['scale'] = np.append(self.quickDic['scale'], scale_)

            self.quickDic['row'] = np.append(self.quickDic['row'], row_)
            self.quickDic['col'] = np.append(self.quickDic['col'], col_)

            self.row_col_dict.setdefault(row_, OrderedDict())[col_] = (eltAbc, eltHead)

            # avoid pairing the same notehead or abc note descripton again!
            eltAbc = eltHead = None
        return

    def insertCursor(self, eltHead, colour='green'):
        self.cursorsDad = eltHead.getparent()
        self.eltCursor = lxml.etree.Element('circle', r='7', stroke=colour,
                                            fill="none")
        self.eltCursor.set('stroke-width', '2')
        self.eltCursor.set('cx', eltHead.get('x'))
        self.eltCursor.set('cy', eltHead.get('y'))
        self.cursorsDad.insert(0, self.eltCursor)

        fileName = str(self.svg_file.fileName())
        outFile = open(fileName, 'wb')
        dbg_print(1, f"written {fileName} with ring cursor!")
        self.svg_tree.write(outFile)

    def removeCursor(self):
        if self.eltCursor is not None and self.cursorsDad is not None:
            self.cursorsDad.remove(self.eltCursor)
            self.eltCursor = None

    def rowColAtXY(self, x, y):
        x_dist = x - self.quickDic['x']
        y_dist = y - self.quickDic['y']
        a_dist = x_dist * x_dist + y_dist * y_dist
        am = np.argmin(a_dist)
        row = self.quickDic['row'][am]
        col = self.quickDic['col'][am]
        return row, col


class Score(QtWidgets.QGraphicsView, WithPrinter):
    ringColour = 'red'
    def __init__(self):
        dbg_print(1, "Score.__init__")
        QtWidgets.QGraphicsView.__init__(self)
        self.setMinimumWidth(640)
        # self.setFixedHeight(1024)
        dbg_print(1, '**** Score', self.height(), self.width())
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.which = 0  # default to show first generated svg until we know better.
        self.fx = self.fy = 0.0
        self.svgDigests = []
        Shared.raft.editBook.settledAt.connect(self.showAtRowAndCol)

        self.svgView = WebView()
        self.svgView.settings().setAttribute(QtWebEngineWidgets.QWebEngineSettings.WebAttribute.ShowScrollBars, False)
        self.pdf_fileNames = None
        page = self.svgView.page()
        page.pdfPrintingFinished.connect(self.printedOnePDF)
        self.svgView.loadFinished.connect(self.svgLoaded)
        self.setScene(MyScene(self))
        self.scene().clear()
        self.proxyWidget = QtWidgets.QGraphicsProxyWidget()
        self.proxyWidget.setWidget(self.svgView)
        self.proxyWidget.setMinimumHeight(1024)
        self.proxyWidget.setMinimumWidth(1024)
        self.scene().addItem(self.proxyWidget)
        #dbg_print(1, '**** Proxy', self.proxyWidget.height(), self.proxyWidget.width())
        self.scene().update()
        dbg_print(1, '**** Scene', self.scene().height(), self.scene().width())
        AddMenu(self, '&Score',
                [
                    ("&Reset Zoom", 'Ctrl+R', self.resetZoom,),
                    ("&First Page", 'Ctrl+1', self.showWhichPage,),
                    ("&Next Page", 'Ctrl+PgDown', self.showNextPage,),
                    ("Pre&vious Page", 'Ctrl+PgUp', self.showPreviousPage,),
#                    ('&Print', 'Ctrl+P', self.printAll,),
                    ('Export &current page to PDF', 'Ctrl+Alt+C', self.printCurrentPageToPDF,),
                    ('E&xport all pages to PDF', 'Ctrl+Alt+X', self.printAllToPDF,),
                ]
                )
        WithPrinter.__init__(self)
        dbg_print(1, "!Score.__init__")

    def printAllToPDF(self):  # <<<<<<<<<<<<<<<<<<<<<< MENU ACTION
        combinedPdfName = self.getPdfOutName("export all pagegs to one PDF",
            os.path.splitext(Shared.raft.editBook.currentWidget().shortName)[0] + '_all_pages.pdf'
        )
        if not combinedPdfName:
            dbg_print(1, f"printing aborted!")
            return
        if len(self.svgFileNames)== 1:
            self.pdf_fileNames = None
            self.printThisPageToPdf(pdfName=combinedPdfName,dir_='')
        else:
            self.combinedPdfName = combinedPdfName
            self.pdf_fileNames = []
            self.printThisPageToPdf(pdfName=None, dir_=temp_dir)

    def printCurrentPageToPDF(self):    # <<<<<<<<<<<<<<<<<<<<<< MENU ACTION
        self.pdf_fileNames = None
        pdfName = self.getPdfOutName("export this page to a PDF", self.getThisPagesPdfName())
        if not pdfName:
            dbg_print(1, f"printing aborted!")
            return
        self.printThisPageToPdf(pdfName=pdfName)

# -------- Menu actions above, internal PDF stuff below----------------------------------------

    def getPdfOutName(self, caption, fileNameOut):
        return QtWidgets.QFileDialog.getSaveFileName(self, caption, fileNameOut, '*.pdf')[0]

    def getThisPagesPdfName(self, dir_=''):
        return os.path.join(dir_,
                            os.path.split(os.path.splitext(self.svgFileNames[self.which])[0] + '.pdf')[1])

    def printThisPageToPdf(self, pdfName=None, dir_=''):
        if not pdfName:
            pdfName = self.getThisPagesPdfName(dir_)
        dbg_print(1, f"printing page to '{pdfName}'")
        page = self.svgView.page()
        layout = QtGui.QPageLayout()
        layout.setPageSize(QtGui.QPageSize(QtGui.QPageSize.A4))
        layout.setMode(QtGui.QPageLayout.FullPageMode)
        layout.setOrientation(layout.Portrait)
        layout.setMargins(QtCore.QMargins(0, 0, 0, 0))
        page.printToPdf(pdfName,layout=layout)

    def printedOnePDF(self, fileName, success):
        dbg_print(1, f"printing of '{fileName} {success and 'succeeded' or 'failed'}!")
        if self.pdf_fileNames is None:
            return  # just finished single page print
# advance to next page, even after last, to get back to initial 'which' page!
        self.pdf_fileNames.append(fileName)
        self.showNextPage()

    def svgLoaded(self):
        if self.pdf_fileNames is None:
            return
        if len(self.pdf_fileNames) < len(self.svgFileNames):  # more pages to print
            self.printThisPageToPdf(dir_=temp_dir)
            return
        fileNamesIn = sorted(self.pdf_fileNames)
        self.pdf_filenames = None  # don't want to accumulate  more and more PDFs if things go wrong below!
        dbg_print(1, f"now concatenate all pages: {fileNamesIn}")
        pdfWriter = PdfWriter()
        for pfn in  fileNamesIn:
            pdfReader = PdfReader(open(pfn, 'rb'))
            for pageObj in pdfReader.pages:  # presuambly one per file!
                pdfWriter.addPage(pageObj)
        pdfWriter.write(open(self.combinedPdfName, 'wb'))

    def drawBackground42(self, p, rect):
        p.save()
        p.resetTransform()
        p.drawTiledPixmap(self.viewport().rect(),
                          self.backgroundBrush().texture())
        p.restore()

    def useFiles(self, fileNames=()):
        self.svgFileNames = fileNames
        self.svgDigests = [SvgDigest(fileName) for fileName in fileNames]
        for path in fileNames:
            svg_file = QtCore.QFile(path)
            if not svg_file.exists():
                QtGui.QMessageBox.critical(self, "Open SVG File",
                                           "Could not open file '%s'." % path)
        self.showWhichPage(self.which, force=True)

    def getEltsOnRow(self, row, which=None):
        if which is True:
            which = self.which
        answer = {}
        for wh, dig in enumerate(self.svgDigests):
            if (which is not None) and (wh != which):
                continue
            answer.update(self.svgDigests[wh].row_col_dict.setdefault(row, {}))
        return answer

    def showAtRowAndCol(self, row, col):

        Shared.eltAbcCursor = None
        dbg_print(1, 'showAtRowAndCol %d %d' % (row, col))
        l = len(self.svgDigests)
        for i in range(l):
            j = (i + self.which) % l
            dictOfRow = self.getEltsOnRow(row, which=j)
            if dictOfRow:
                break
        else:
            dbg_print(1, "can't find page containing svg graphics for row %d"
                      % row)
            return
        self.svgDigests[j].removeCursor()
        for col_ in list(range(col, 0, -1)) + list(range(col, col + 5, 1)):
            eltAbc, eltHead = dictOfRow.get(col_, (None, None))
            if isinstance(eltHead, lxml.etree._Element):
                self.fx, self.fy = [float(eltAbc.get(a)) for a in ('x', 'y')]
                self.svgDigests[j].insertCursor(eltHead, colour=self.ringColour)
                break
        else:
            dbg_print(1, "can't find svg graphics correspond to row %d: col %d (page %d)"
                      % (row, col, j))
            self.fx, self.fy = 0.0, 0.0

        # experimental and ugly!
        #dbg_print(1, 'ensureVisible1 %d %d' % (self.fx, self.fy))
        #self.ensureVisible(self.fx, self.fy, 20.0, 20.0)
        # self.ensureVisible(point.x(), point.y(), 1.0, 1.0)
        self.showWhichPage(j, force=True)
        Shared.eltAbcCursor = eltAbc

    def locateXY(self, x, y):
        row, col = self.svgDigests[self.which].rowColAtXY(x, y)
        dbg_print(1, "locateXY( %d,%d > row,col %d %d" % (x, y, row, col))
        Shared.raft.editBook.moveToRowCol(row, col)

    def showNextPage(self):
        dbg_print(1, 'showNextPage')
        return self.showWhichPage(self.which + 1)

    def showPreviousPage(self):
        dbg_print(1, 'showPreviousPage')
        return self.showWhichPage(self.which - 1)

    def showWhichPage(self, which=0, force=False):
        dbg_print(1, '----- showWhichPage', which)
        which %= len(self.svgDigests)
        if (not force) and (which == self.which):
            return
        svg_file = self.svgDigests[which].svg_file
        if not svg_file.exists():
            raise IOError("'%s' does not exist!" % svg_file.filename())
        self.which = which

        # The slash reversal below is ugly; there is surely a better way. But after struggling
        # for hours with "invisible on Windows" svg's, I'm happy with anything that works!
        #
        url = 'file:///' + os.path.abspath(svg_file.fileName()).replace('\\', '/')
        self.svgView.load(QtCore.QUrl(url))
        self.svgDigests[which].AdjustForScene(self.scene())
        #self.proxyWidget.setWidget(self.svgView)
        #self.proxyWidget.update()
        #self.update()
        #self.scene().update()
        # self.proxyWidget.show()

    def resetZoom(self):
        self.resetTransform()

    def renderAll(self, painter):
        self.printing = True
        self.showWhichPage(0, force=True)

    def wheelEvent(self, event):
        delta = DeltaOfEvent(event)
        dbg_print(1, f"Score.wheelEvent, {delta=}")
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if not (modifiers & QtCore.Qt.ControlModifier):
            # return  self.scrollContentsBy(0, delta*20)
            sbar = self.verticalScrollBar()
            value = sbar.value() - delta
            if delta > 0:
                value = max(sbar.minimum(), value)
            else:
                value = min(sbar.maximum(), value)
            sbar.setValue(value)
            dbg_print(1, "%d <= vsbar=%d <= %d" % (sbar.minimum(), value, sbar.maximum()))
            self.update()
            event.accept()
            return
        factor = 1.2 ** (delta / 120.0)
        self.scale(factor, factor)
        self.update()
        # self.mustApplyTransform = self.transform()
        event.accept()


if __name__ == '__main__':
    class MainWindow(QtGui.QMainWindow):
        """
        warning: not used this '__main__' in months: probably not working!
        """

        def __init__(self):
            super(MainWindow, self).__init__()

            self.currentPath = ''

            self.score = Score()

            fileMenu = QtGui.QMenu("&File", self)
            quitAction = fileMenu.addAction("E&xit")
            quitAction.setShortcut("Ctrl+Q")

            self.menuBar().addMenu(fileMenu)

            quitAction.triggered.connect(QtGui.qApp.quit)

            self.setCentralWidget(self.score)
            self.setWindowTitle("SVG Viewer")
            self.score.useFiles(sys.argv[1:] or
                                ['test.svg'])
            self.score.resize(self.score.sizeHint() + QtCore.QSize(
                80, 80 + self.menuBar().height()))


    app = QtWidgets.QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
