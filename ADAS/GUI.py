import numpy as np
import cv2
import zmq
cap = cv2.VideoCapture(4)

context = zmq.Context()

#  Socket to talk to server
print("Connecting to fusion engine")
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5558")

print("Entering GUI Loop...")

while(True):
	message = socket.recv_string()
	data = message.split('/')
	camera_data = data[0]
	radar_data = data[1]
	lidar_data = data[2]
	#print(data)
	print(camera_data)
	print(radar_data)
	print(lidar_data)
	print("-----------------------")
	socket.send(b"world")
	ret, frame = cap.read()
	
	modf_frame = frame
	
	#breakdown the aggregated camera_data into individual rectangles, then draw rectangles on the frame. 
	while len(camera_data)>20:
		px1 = int(camera_data[0:4])
		py1 = int(camera_data[4:8])
		px2 = int(camera_data[8:12])
		py2 = int(camera_data[12:16])
		camera_certainty = float(camera_data[16:21])
		camera_data = camera_data[21:]
		modf_frame = cv2.rectangle(modf_frame, (px1, py1), (px2, py2), (255,0,0), 2)
	
	#breakdown the aggregated camera_data into individual rectangles, then draw rectangles on the frame. 
	while len(radar_data)>7:
		px = int(radar_data[0:4])
		py = int(radar_data[4:8])
		radar_data = radar_data[8:]
		modf_frame = cv2.rectangle(modf_frame, (px, py), (px+10, py+10), (0,0,255), 2)
	
	#gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	#cv2.imshow('frame',gray)
	
	cv2.imshow('frame',modf_frame)
	
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break
		
cap.release()
cv2.destroyAllWindows()
