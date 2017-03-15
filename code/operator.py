# Remote operator interface for 'scout' the robot
# Author: Oliver Douglas

import threading
import socket
import struct
import time
import sys
import StringIO
import pygame
from pygame.locals import *

# Global signal set by kbd_io_thread to end the program
exit_signal = False

# For unknown reasons, X11 sometimes gets angry when the screen object
# is created inside the video thread, so now it's passed from main()...
pygame_screen = None

# Video screen size in pixels
DIMENSIONS = (640, 480)

# Frequency of keyboard polling loop, in hertz
KBD_POLL_FREQ = 100

# User keyboard commands
DRIVE_FORWARDS = bytes('F')
DRIVE_BACKWARDS = bytes('B')
DRIVE_LEFT = bytes('L')
DRIVE_RIGHT = bytes('R')
DRIVE_STOP = bytes('S')
SESSION_END = bytes('Q')



# This thread sends keyboard commands to the robot, including ending
# the control session
def kbd_send(ip_string, socket_num):
   global exit_signal
   
   # Make a UDP connection to send keyboard commands
   kbd_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

   # Loop until we get a quit request or the other thread fails
   while exit_signal == False:

      # Poll the keyboard for user input at KBD_POLL_FREQ hertz
      time.sleep(1.0 / KBD_POLL_FREQ)
      pygame.event.get()
      keys = pygame.key.get_pressed()

      key = None
      if keys[K_w] == True:
         key = DRIVE_FORWARDS
      elif keys[K_s] == True:
         key = DRIVE_BACKWARDS
      elif keys[K_a] == True:
         key = DRIVE_LEFT
      elif keys[K_d] == True:
         key = DRIVE_RIGHT
      elif keys[K_ESCAPE] == True:
         key = SESSION_END
      else:
         key = DRIVE_STOP

      # Only send keyboard data if it matched one of the known commands
      if key != None:
         try:
            kbd_socket.sendto(key, (ip_string, socket_num))
         except:
            print "kbd_sender: UDP transmit error"
            exit_signal = True
         
      # User has made a quit request; signal the other thread to exit
      if key == SESSION_END:
         exit_signal = True

   # Cleanup after we got a quit request, failed, or the other thread failed
   kbd_socket.close()
   print ("Keyboard receiver closed")
   return
   


# This thread receives and displays video from the robot
def vid_recv(ip_string, socket_num):
   global exit_signal
   global pygame_screen

   # Attempt to open a TCP connection to the video source
   vid_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   try:
      vid_socket.connect((ip_string, socket_num))
   except:
      print "vid_recv: TCP connection attempt failed"
      exit_signal = True

   # Loop until we encounter an error or an exit request from the other thread
   while exit_signal == False:

      # Get the 32-bit int representing the size of the incoming image
      data = vid_socket.recv(4, socket.MSG_WAITALL)
      if data == '':
         break
      frame_size = struct.unpack('!L', data)[0]

      # Receive the full image of 'frame_size' bytes
      data = vid_socket.recv(frame_size, socket.MSG_WAITALL)

      # Draw the new image on the screen
      img = pygame.image.load(StringIO.StringIO(data))
      pygame_screen.blit(img, (0,0))
      pygame.display.update()

   # Cleanup after a failure or quit request from the other thread
   vid_socket.close()
   print ("Video connection closed")
   return


   
# Get (optional) command line args, initialize pygame, and start both threads
# Acceptable command line invocation formats:
#
# python operator.py
# python operator.py [IP_ADDR]
# python operator.py [IP_ADDR] [BASE_PORT]
#
def main():
   global pygame_screen
   
   IP_ADDR = "192.168.1.201"
   if len(sys.argv) >= 2:
      IP_ADDR = sys.argv[1]
   
   # TCP will run on BASE_PORT, UDP will run on BASE_PORT + 1
   BASE_PORT = 5000
   if len(sys.argv) >= 3:
      BASE_PORT = int(sys.argv[2])

   # Start pygame framework here, because both threads will use it
   pygame.init()
   
   # Initialize the video display so we can pass it to the video thread.
   # Doing this in main() seems to resolve the sporadic issue where X11
   # kills the pygame display and reports "unknown request in queue..." errors
   pygame_screen = pygame.display.set_mode(DIMENSIONS)
   
   # Start the keyboard and video threads
   vid_recv_thread = threading.Thread(target=vid_recv, args=(IP_ADDR, BASE_PORT))
   kbd_send_thread = threading.Thread(target=kbd_send, args=(IP_ADDR, BASE_PORT+1))
   vid_recv_thread.start()
   kbd_send_thread.start()

   # Exit immediately because we have nothing else to do 
   exit()


if __name__ == "__main__":
   main()

