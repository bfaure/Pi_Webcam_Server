# Python 2.7

# standard imports 
import os,sys,time,random

# gui imports 
from PyQt4.QtCore import * 
from PyQt4.QtGui import *

# networking imports 
from socket import * 

# tftp library
import tftpy


DEFAULT_PORT_NUM=15213
MAX_WAIT_TIME=0.1
DEFAULT_BLK_SIZE=8000

FRAME_FILE="frame.png"

CLIENT_DIR = "client_frame_buffer"
SERVER_DIR = "server_frame_buffer"

REFRESH_AFTER = 0.1

# Class runs in a separate thread from the main thread, requests frame.png from server
class frame_manager(QThread): 
	update_gui = pyqtSignal() # signal used to update the main GUI window

	def __init__(self,parent): # parent is the main GUI window
		QThread.__init__(self,parent)
		self.parent=parent # save the GUI window as parent
		self.ip_address="localhost" # default 
		self.port_num=DEFAULT_PORT_NUM # set to 15213
		self.stop=False # dont quit automatically
		self.pause=True # dont start requesting until told to do so
		self.connect(self,SIGNAL("update_gui()"),parent.update_frame) # connect update_gui to GUI window function 'update_frame'

	def run(self): # send update signal to gui window periodically
		num_transmission_errors=0

		while True:
			while self.pause: # if pausing, or not yet initialized
				time.sleep(0.2)
			if self.stop: break # if told to stop
			start_time=time.time()
			# create client object for transfer
			client = tftpy.TftpClient(self.ip_address,self.port_num,options={'blksize':DEFAULT_BLK_SIZE})
			try:
				# try to download 'server_frame_buffer/frame.png' from server
				client.download(SERVER_DIR+"/"+FRAME_FILE,CLIENT_DIR+"/"+FRAME_FILE,timeout=MAX_WAIT_TIME)
				# set the path to the new frame in the parent
				self.parent.current_frame_file=CLIENT_DIR+"/"+FRAME_FILE
				# tell the parent to update with the new frame
				self.update_gui.emit()
			except:
				print("Transmission Error")
				num_transmission_errors+=1
			print("Transfer time: %0.4f"%(time.time()-start_time))
			time.sleep(REFRESH_AFTER)

# window that pops up allowing user to enter IP address
class ip_window(QWidget):
	got_ip = pyqtSignal()

	def __init__(self,parent=None):
		super(ip_window,self).__init__()
		self.parent = parent
		self.connect(self,SIGNAL("got_ip()"),self.parent.got_ip)
		self.init_vars()
		self.init_ui()

	def init_vars(self):
		self.full_ip = None 
		self.ip1 = "192"
		self.ip2 = "168"
		self.ip3 = "1"
		self.ip4 = ""

	def init_ui(self):
		self.setWindowTitle("IP Address Input")
		self.layout = QVBoxLayout(self)
		self.top_label = QLabel("Enter IP Address of Server:")
		self.layout.addWidget(self.top_label)

		ip_row = QHBoxLayout()

		self.ip1_input = QLineEdit(self.ip1)
		self.ip2_input = QLineEdit(self.ip2)
		self.ip3_input = QLineEdit(self.ip3)
		self.ip4_input = QLineEdit(self.ip4)

		ip_row.addSpacing(15)
		ip_row.addWidget(self.ip1_input)
		ip_row.addWidget(QLabel("."))
		ip_row.addWidget(self.ip2_input)
		ip_row.addWidget(QLabel("."))
		ip_row.addWidget(self.ip3_input)
		ip_row.addWidget(QLabel("."))
		ip_row.addWidget(self.ip4_input)
		ip_row.addSpacing(15)

		ok_cancel_row = QHBoxLayout()
		ok_button = QPushButton("Ok")
		cancel_button = QPushButton("Cancel")

		ok_cancel_row.addStretch()
		ok_cancel_row.addWidget(cancel_button)
		ok_cancel_row.addWidget(ok_button)
		ok_cancel_row.addStretch()

		ok_button.clicked.connect(self.ok_selected)
		cancel_button.clicked.connect(self.cancel_selected)

		self.layout.addLayout(ip_row)
		self.layout.addLayout(ok_cancel_row)
		self.layout.addSpacing(20)

		self.setFixedWidth(350)
		self.setFixedHeight(150)

	def keyPressEvent(self,e):
		if e.key() in [Qt.Key_Return,Qt.Key_Enter]:
			self.ok_selected()

	def ok_selected(self):
		self.ip1 = str(self.ip1_input.text())
		self.ip2 = str(self.ip2_input.text())
		self.ip3 = str(self.ip3_input.text())
		self.ip4 = str(self.ip4_input.text())
		self.full_ip = self.ip1+"."+self.ip2+"."+self.ip3+"."+self.ip4
		self.got_ip.emit()

	def cancel_selected(self):
		self.full_ip = None
		self.got_ip.emit()

	def closeEvent(self,e):
		self.cancel_selected()

# Widget class for buttons with pictures
class PicButton(QAbstractButton):
	def __init__(self,pic_path,parent=None):
		super(PicButton,self).__init__(parent)
		self.pixmap = QPixmap(pic_path)

	def paintEvent(self,event):
		painter = QPainter(self)
		painter.drawPixmap(event.rect(),self.pixmap)

	def sizeHint(self):
		return self.pixmap.size()

# Main GUI class
class main_window(QWidget): 
	def __init__(self):
		super(main_window,self).__init__() 
		self.ip_dialog_window = ip_window(self)
		self.init_vars()
		self.init_ui()

	def init_vars(self):
		self.current_frame_file=None # path to current frame
		self.ip=None # string ip address (xxx.xxx.xxx.xxx)

	def init_ui(self):

		self.setWindowTitle("Not Connected")

		self.min_width=600
		self.min_height=600

		self.window_layout = QVBoxLayout(self) # control layout of widgets on window

		self.main_image = QLabel() # will push image stream to this widget 

		main_row = QHBoxLayout()
		main_row.addStretch()
		main_row.addWidget(self.main_image)
		main_row.addStretch()
		self.window_layout.addLayout(main_row,2)

		button_row = QHBoxLayout()

		play_button = PicButton("resources/play_icon.png")
		play_button.setFixedWidth(30)
		play_button.setFixedHeight(30)
		play_button.clicked.connect(self.play_button_pressed)

		stop_button = PicButton("resources/stop_icon.png")
		stop_button.setFixedHeight(30)
		stop_button.setFixedWidth(30)
		stop_button.clicked.connect(self.stop_button_pressed)

		connect_button = PicButton("resources/connect_icon.png")
		connect_button.setFixedWidth(30)
		connect_button.setFixedHeight(30)
		connect_button.clicked.connect(self.connect_button_pressed)

		pause_button = PicButton("resources/pause_icon.png")
		pause_button.setFixedWidth(30)
		pause_button.setFixedHeight(30)
		pause_button.clicked.connect(self.pause_button_pressed)

		button_row.addStretch()
		button_row.addWidget(pause_button)
		button_row.addWidget(play_button)
		button_row.addWidget(stop_button)
		button_row.addSpacing(100)
		button_row.addWidget(connect_button)
		button_row.addStretch()

		self.window_layout.addLayout(button_row)

		toolbar = QMenuBar(self) # top menu bar
		toolbar.setFixedWidth(self.min_width)

		file_menu = toolbar.addMenu("File")
		file_menu.addAction("Quit",self.quit,QKeySequence("Ctrl+Q"))

		connection_menu = toolbar.addMenu("Connection")
		connection_menu.addAction("Connect...",self.connect_to_server,QKeySequence("Ctrl+C"))
		connection_menu.addAction("Disconnect",self.disconnect_from_server,QKeySequence("Ctrl+D"))
		connection_menu.addSeparator()
		connection_menu.addAction("Refresh Rate...",self.set_refresh_rate,QKeySequence("Ctrl+R"))

		self.resize(self.min_width,self.min_height) # resize window
		self.show()

		self.fps_manager = frame_manager(self) # separate thread to handle updating window
		self.fps_manager.start() # start manager thread

	def stop_button_pressed(self):
		self.disconnect_from_server()

	def pause_button_pressed(self):
		self.fps_manager.pause=True 

	def connect_button_pressed(self):
		self.connect_to_server()

	def play_button_pressed(self):
		if self.ip!=None: self.fps_manager.pause=False
		else: self.connect_to_server()

	def set_refresh_rate(self):
		global REFRESH_AFTER
		input_rate,ok = QInputDialog.getText(self,"Change Refresh Rate","Enter wait time (seconds): ")
		if ok: REFRESH_AFTER = float(input_rate)

	def update_frame(self):
		if self.current_frame_file==None: return # skip if we dont have a frame
		print("Loading new frame")
		try:
			self.current_frame = QPixmap(self.current_frame_file)
			self.current_frame = self.current_frame.scaled(555,520)
			self.main_image.setPixmap(self.current_frame)
		except:
			print("Could not load new frame")

	def got_ip(self):
		self.ip_dialog_window.hide()
		self.show()
		self.connect_to_server(ip=self.ip_dialog_window.full_ip)

	def connect_to_server(self,ip=None):
		self.ip=ip
		if ip==None:
			self.hide()
			self.ip_dialog_window.show()
			return
		print("Connecting to %s"%ip)
		self.fps_manager.ip_address=ip
		self.fps_manager.port_num=DEFAULT_PORT_NUM
		self.fps_manager.pause=False 
		self.setWindowTitle("Connected to %s"%ip)

	def disconnect_from_server(self):
		self.fps_manager.pause=True
		self.ip=None 
		self.setWindowTitle("Not Connected")

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
