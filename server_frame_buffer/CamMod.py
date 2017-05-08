import picamera
from time import sleep
from datetime import datetime, timedelta
from shutil import copy
import os

'''
    Imported Camera library for raspberry pi
    set the camera as an object, and set the resolution
    While the camera is opened it will take continuous shots
    until connection is terminated
    image is copied to a temp file, so new image can be taken


'''
with picamera.PiCamera() as Camera:
	sleep(1)
	Camera.resolution = (100,100)
	for filename in Camera.capture_continuous('image2.png'):
                
                if os.path.isfile("image.png"): os.remove("frame.png")
                ##sleep(0.05)
                copy("image2.png","frame.png")
		print('Capture %s' % filename)
		'''sleep(0.03)'''
