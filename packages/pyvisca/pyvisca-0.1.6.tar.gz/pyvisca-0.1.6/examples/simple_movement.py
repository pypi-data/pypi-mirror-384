# -*- coding: utf-8 -*-
# 
# Simple up-down and left-right movement of the PTZ camera
# ---
# By Samarthya Lykamanuella (groaking)
# Licensed under GPL-3.0

from pyvisca import visca
import time

# Replace the port value with your PTZ's detected port number in the device manager
port='COM7'

cam = visca.PTZ(port)

# Move the camera to the left for 10 seconds
cam.left()
time.sleep(10)
cam.stop()

# Move the camera to the left about 200 pixels apart
cam.set_pan_rel(-200)

# Move to the right 50 pixels apart
cam.set_pan_rel(50)

# Turn off the camera
cam.power(False)
