import time
import zmq
import subprocess
import _thread
import datetime
from threading import Lock

import numpy as np
import math
import mkmath as mk
import cv2



PORT_CAMERA = "5555"
PORT_LIDAR = "5556"
PORT_RADAR = "5557"
PORT_GUI = "5558"

radar_data = list()
camera_data = list()

camera_data_mutex = Lock()
radar_data_mutex = Lock()


#Radar Configuration
RT=np.matrix('1 0 0 0;0 0 1 0;0 1 0 0;0 0 0 1') #based on corrected axes
fy=863.1305
fx=882.0941
cx=981
cy=330
Sx=16
Sy=10

#pixel buffer for radar
radar_pixel=[]



def thread_camera():

	while True:
		#  Wait for next request from client
		message_camera = socket_camera.recv()
		#parse camera data
		
		camera_data_mutex.acquire()
		camera_data.clear()
		while len(message_camera)>19:
			px1 = int(message_camera[0:4])
			py1 = int(message_camera[4:8])
			px2 = int(message_camera[8:12])
			py2 = int(message_camera[12:16])
			camera_certainty = float(message_camera[16:20])/10000
			camera_data.append((px1, py1, px2, py2, camera_certainty))
			message_camera = message_camera[20:]
	
		
		while (len(camera_data)>=10):
			del camera_data[0]	
		camera_data_mutex.release()

		socket_camera.send(b"Ack_Cam")
		
		
		#print("Received camera request: %s" % message_camera)
	
	
def thread_radar():
	
	while(True):  
	#Blocking receive
		message = socket_radar.recv()
		
		radar_data.clear()
		
		socket_radar.send(b"200")
		
		#calculation of loop params	
		number_of_obj= (len(message)-1)/15
		#print("Number of detected Objects:")
		#print(number_of_obj)
		#counters	
		count=0
		#position on string
		index=0 
	
		while(count<number_of_obj):
			
			#print("Entered loop no",count)
			x = int(message[index:index+4+1])/100
			y = int(message[index+5:index+9+1])/100
			z = int(message[index+10:index+14+1])/100
			
			#calculating radius for scaling circle radius
			r = math.sqrt(math.pow(x,2)+math.pow(y,2)+pow(z,2))
			index = index+15
			count = count+1
			
			#radius
			rad=10
			if(r<1):
				rad=20
			elif(r>10):
				rad=5
			else:
				rad=5+15/9*r
			
			#pixel conversion
			uv= mk.convertWorldCordsToPixelsRadar(x,y,z,fx,fy,cx,cy,RT,Sx,Sy)
			radar_data.append(uv)
			
			#TODO: are we keeping history here?
			while (len(radar_data)>=10):
				del radar_data[0]
			
			#print("Calculated pixel coords")
			#print(uv)
		
		#resetting loop params	
		index=0
		count=0
		
		



#############################################
########## INITALIZATION ###################
###########################################

#create camera vision socket
context_camera = zmq.Context()
socket_camera = context_camera.socket(zmq.REP)
socket_camera.bind("tcp://*:" + PORT_CAMERA)

#create radar socket
context_radar = zmq.Context()
socket_radar = context_radar.socket(zmq.REP)
socket_radar.bind("tcp://*:" + PORT_RADAR)



print("Initializing Camera Feed...")
pid_camera = subprocess.Popen(["/home/nvidia/jetson-inference/jetson-inference/build/aarch64/bin//detectnet-camera", "pednet"])
print("Configuring Radar to start producing data...")
pid_radar_config = subprocess.Popen(["/home/nvidia/Documents/radar_cfgs/reader_writer"])
print("Starting Radar incoming data parser ")
pid_radar_data = subprocess.Popen(["/home/nvidia/Documents/radar_cfgs/dataport_reader_zmq"])
print("Starting GUI...")
pid_GUI = subprocess.Popen(["python3", "/home/nvidia/Documents/ADAS/GUI.py"])

#create GUI socket
context_gui = zmq.Context()
socket_gui = context_gui.socket(zmq.REQ)
socket_gui.connect("tcp://localhost:" + PORT_GUI)	

#############################################
########## END INITALIZATION ###################
###########################################


try: 
	_thread.start_new_thread(thread_camera, ())
	_thread.start_new_thread(thread_radar, ())
except:
	print("Error: Unable to start thread")
	
print("Entering loop")

while 1:
	
	camera_data_mutex.acquire()

	#print("==========")
		
	#print(datetime.datetime.now().time())
	#print("Camera Data")
	camera_buffer = ""
	for x1, y1, x2, y2, cert in camera_data:
		camera_buffer += "{0:04d}{1:04d}{2:04d}{3:04d}{4:5.3f}".format(x1, y1, x2, y2, cert)
		
		#cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3) 
		#print(x1, y1, x2, y2, e)
		
	#print("Radar Data")
	radar_buffer = ""
	#FIX THIS: radar_data is not in x,y,z
	#for x, y, z in radar_data:
	for u, v, w in radar_data:
		#radar_buffer += "{0:03d}{1:03d}{2:03d}".format(x, y, z)
		radar_buffer += "{0:04d}{1:04d}".format(u, v)
		#cv2.circle(frame, (x, y), 40, (0, 0, 255), 3)
		#print(x, y, z)
		#fusion algorithm
		
		
	#print("==========")
	
	#crafting a single message to send to GUI, using '/' delimiters.
	fusion_message = "{}/{}/{}".format(camera_buffer, radar_buffer, "c")
	socket_gui.send_string(fusion_message)
	gui_message = socket_gui.recv()
    #print("Received reply")
	
	
	camera_data_mutex.release()
	
	
	
	pass






#########################################
############ HELPER FUNCTIONS ###########
#########################################





 
    
