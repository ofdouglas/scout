
**Scout** is a robot built for remote exploration. While Scout was originally designed to solve a maze for my ECE 499 (Robot Design) course at GMU, Scout could be used to explore any reasonably flat terrain.

**Instructions**
To use Scout, SSH into the raspberry pi and run the 'robot.py' program. Then run the 'operator.py' program on a computer with a keyboard and monitor, passing the IP address of the raspberry pi as a command line argument. Once the video feed begins, use the WASD keys to maneuver Scout. Press ESC to quit.

**Limitations**
* Scout works best on flat, hard terrain. The rear caster wheel is relatively small, and may get stuck if driven on bad terrain.
* Also, some 'torque steer' may be encountered if one of the front wheels obtains better traction than the other. While the speed of the wheels is matched, no effort was made to match the torques.