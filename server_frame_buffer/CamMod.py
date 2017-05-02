import picamera
from time import sleep


camera = picamera.PiCamera()
camera.start_preview()

camera.capture('image1.png')
sleep(5)
camera.capture('image2.png')

camera.stop_preview()