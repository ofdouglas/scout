# Robot controller for the robot "scout"
# Author: Oliver Douglas

import threading
import socket
import struct
import picamera
import time
import sys
import serial
import io


# Global signal set by kbd_io_thread to end the program
exit_signal = False

# Video screen size in pixels
DIMENSIONS = (640, 480)

# User keyboard commands
DRIVE_FORWARDS = bytes('F')
DRIVE_BACKWARDS = bytes('B')
DRIVE_LEFT = bytes('L')
DRIVE_RIGHT = bytes('R')
DRIVE_STOP = bytes('S')
SESSION_END = bytes('Q')


# This thread receives keyboard commands over UDP and sends them
# to the OpenCM9 microcontroller
def kbd_recv(port):
    global exit_signal
    
    # Attempt to open a serial connection to the OpenCM9
    try:
        ocm9 = serial.Serial(port='/dev/ocm9')
    except:
        print "Failed to open serial port"
        exit_signal = True
        return
    else:
        print "Opened serial port"

    # Accept a connection on the given port from any host IP address
    kbd_recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        kbd_recv_sock.bind(('', port))
    except:
        print "socket bind failed"
        exit_signal = True
        return
    else:
        print "Socket bound on port " + str(port)

    # Enable timeout so that we can't miss an exit_signal set by the other
    # thread by being blocked on socket.recv()
    kbd_recv_sock.settimeout(1)

    # Forward keyboard commands from the operator PC to the microcontroller.
    # Filter out redundant commands and exit commands - the MCU only
    # expects to be notified when the current command changes!
    last_char = DRIVE_STOP
    while exit_signal == False:
        try:
            data, addr = kbd_recv_sock.recvfrom(1)
        except:
            pass
            # We timed out - try again after checking exit_signal
        else:
            # We received a command
            if data == SESSION_END:
                exit_signal = True
                print "Received session end signal"
                break

            # Ignore redundant commands
            if data != last_char:
                print data
                try:
                    ocm9.write(data)
                    last_char = data
                except:
                    print "Unable to write to serial port"
                    exit_signal = True

    # Cleanup after an operator exit request or an error was detected
    print "Closing serial connection"
    ocm9.close()
    return    


# This thread captures images from the camera and sends them to the operator
# computer over TCP
def img_send(port):
  global exit_signal

  img_send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  # Tell the OS to skip the TIME_WAIT state on this cam_socket if
  # our program ends unexpectedly (so we can restart it quickly)
  img_send_sock.setsockopt(socket.SOL_SOCKET,
                                    socket.SO_REUSEADDR, 1)

  # Accept a TCP connection from any IP address
  try:
      img_send_sock.bind(('', port))
      img_send_sock.listen(1)
      print "waiting for connections on port " + str(port)
      conn, addr = img_send_sock.accept()
      print "accepted connection on " + str(addr)
  except:
      print "TCP server socket init failed"
      exit_signal = True
      return

  # Open a video stream. Have the camera image flipped because it's easier
  # (mechanically) to mount it upside down
  camera = picamera.PiCamera()
  camera.resolution = (DIMENSIONS)
  camera.vflip = True
  camera.hflip = True
  time.sleep(2)

  # Loop until we find an error or get an exit request from the other thread
  while exit_signal == False:

    # Capture the image to a file-like IO object the socket can use.
    # The 'use_video_port' option allows fast capture of still frames
    stream = io.BytesIO()
    camera.capture(stream, format='jpeg', use_video_port=True)
    stream.seek(0)

    # Convert the image to a string for network transmission
    frame = stream.read()
    try:
        conn.sendall(struct.pack('!L', len(frame)))
        conn.sendall(frame)
    except:
        print "img_send: TCP connection failed"
        exit_signal = True
        break
        
  # Close the connection
  conn.close()
  return


# Get (optional) command line argument and start both threads
# Acceptable command line invocation formats:
#
# python robot.py
# python robot.py [PORT]
#
def main():

    # Read an (optional) port number from the command line
    IP_PORT = 5000
    if len(sys.argv) == 2:
        IP_PORT = int(sys.argv[1])

    # Start the keyboard and video threads
    img_send_thread = threading.Thread(target=img_send, args=(IP_PORT,))
    kbd_recv_thread = threading.Thread(target=kbd_recv, args=(IP_PORT+1,))
    img_send_thread.start()
    kbd_recv_thread.start()

    # Exit immediately because we have nothing else to do
    exit()

    
if __name__ == "__main__":
  main()
