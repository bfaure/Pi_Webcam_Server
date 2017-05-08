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
	sleep(2)
	Camera.resolution = (500,500)
	for filename in Camera.capture_continuous('image2.png'):
                
                if os.path.isfile("image.png"): os.remove("image.png")
                sleep(0.5)
                copy("image2.png","image.png")
		print('Capture %s' % filename)
		sleep(1)
