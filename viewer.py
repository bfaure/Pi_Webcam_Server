# Python 2.7

# standard imports 
import os,sys,time

# gui imports 
from PyQt4.QtCore import * 
from PyQt4.QtGui import *

# networking imports 
from socket import * 

class connection_manager(object):

	def __init__(self,parent=None):
		self.parent=parent 

class frame_manager(QThread): # handles updating the gui
	update_gui = pyqtSignal()

	def __init__(self,parent,refresh_after=0.2):
		QThread.__init__(self,parent)
		self.refresh_after=refresh_after
		self.stop=False
		self.connect(self,SIGNAL("update_gui()"),parent.repaint)

	def run(self): # send update signal to gui window periodically
		while True:
			if self.stop: break 
			self.update_gui.emit()
			time.sleep(self.refresh_after)

class main_window(QWidget): 

	def __init__(self):
		super(main_window,self).__init__() 
		self.init_vars()
		self.init_ui()

	def init_vars(self):
		self.current_frame = QPixmap("resources/test_images/test.png")
		self.connection = connection_manager(self)

	def init_ui(self):

		self.min_width=600
		self.min_height=600

		self.window_layout = QVBoxLayout(self) # control layout of widgets on window

		self.main_image = QLabel() # will push image stream to this widget 

		self.window_layout.addWidget(self.main_image) # add to layout

		toolbar = QMenuBar(self) # top menu bar
		toolbar.setFixedWidth(self.min_width)

		file_menu = toolbar.addMenu("File")
		#file_menu.addAction("Test video",self.test_video)
		file_menu.addAction("Quit",self.quit,QKeySequence("Ctrl+Q"))

		connection_menu = toolbar.addMenu("Connection")
		connection_menu.addAction("Connect...",self.connect_to_server)
		connection_menu.addAction("Disconnect",self.disconnect_from_server)

		self.resize(self.min_width,self.min_height) # resize window
		self.show()

		self.fps_manager = frame_manager(self) # separate thread to handle updating window
		self.fps_manager.start() # start manager thread

	def paintEvent(self,e):
		qp = QPainter()
		qp.begin(self)
		self.drawWidget(qp)
		qp.end()

	def drawWidget(self,qp):
		self.main_image.setPixmap(self.current_frame)

	def connect_to_server(self):
		pass # not yet implemented

	def disconnect_from_server(self):
		pass # not yet implemented

	def quit(self):
		self.fps_manager.stop=True # tell fps manager to terminate
		self.disconnect_from_server() # handle disconnecting from video stream
		sys.exit(1) # terimate process

	def closeEvent(self,e): # catch signal when user tries to exit by clicking window button
		self.quit() # re-route to our quit function


def main():
	pyqt_app = QApplication(sys.argv) # need to pass something to QApplication constructor
	app_window = main_window() # create window object
	sys.exit(pyqt_app.exec_()) # exit upon quit of application

if __name__ == '__main__':
	main()
