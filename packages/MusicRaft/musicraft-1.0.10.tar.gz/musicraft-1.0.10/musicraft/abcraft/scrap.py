import sys
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QGraphicsScene, QGraphicsView
from PyQt5.QtCore import QUrl

app = QApplication(sys.argv)
webView = QWebEngineView()
webView.setMinimumWidth(1024)
webView.setMinimumHeight(1024)
scene = QGraphicsScene()
proxy = scene.addWidget(webView)
# Variant 1: Reasonably fast
webView.load(QUrl('file:////home/gill/tmp/work/highland_cathedral_page_001.svg'))
view = QGraphicsView(scene)
view.show()
sys.exit(app.exec_())