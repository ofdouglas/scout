#define DXL_BUS_SERIAL1 1  //Dynamixel on Serial1(USART1)  <-OpenCM9.04
#define DXL_BUS_SERIAL2 2  //Dynamixel on Serial2(USART2)  <-LN101,BT210
#define DXL_BUS_SERIAL3 3  //Dynamixel on Serial3(USART3)  <-OpenCM 485EXP

// Dynamixel speed settings
#define BASE_SPEED 600
#define TURN_SPEED 300
#define SPEED_BACKWARDS 0x400  // sign bit for speed

// Dynamixel bus ID's
#define RIGHT_MOTOR_ID 1
#define LEFT_MOTOR_ID  2

// Motion commands received over SerialUSB
#define DRIVE_FORWARDS  'F'
#define DRIVE_BACKWARDS 'B'
#define DRIVE_LEFT      'L'
#define DRIVE_RIGHT     'R'
#define DRIVE_STOP      'S'

Dynamixel Dxl(DXL_BUS_SERIAL1);
 
void setup() {
  // Initialize the dynamixel bus:
  // Dynamixel 2.0 Baudrate -> 0: 9600, 1: 57600, 2: 115200, 3: 1Mbps 
  Dxl.begin(3);
  Dxl.jointMode(BROADCAST_ID);
  Dxl.maxTorque(BROADCAST_ID, 1000);
  Dxl.complianceSlope(BROADCAST_ID, 8, 8);
 
  // Setup serial connection for commands
  SerialUSB.attachInterrupt(usbInterrupt);
  
  // LED for debugging
  pinMode(BOARD_LED_PIN, OUTPUT);
}

  
void usbInterrupt(byte* buffer, byte nCount)
{
  int left_motor_speed;
  int right_motor_speed;
  
  digitalWrite(BOARD_LED_PIN, HIGH);
  
   for (int i = 0; i < nCount; i++) {
    switch (buffer[i]) {
     case DRIVE_FORWARDS:
      left_motor_speed = BASE_SPEED;
      right_motor_speed = BASE_SPEED; 
      break;
     case DRIVE_BACKWARDS:
      left_motor_speed = BASE_SPEED | SPEED_BACKWARDS;
      right_motor_speed = BASE_SPEED | SPEED_BACKWARDS;
      break;
     case DRIVE_LEFT:
      left_motor_speed = TURN_SPEED | SPEED_BACKWARDS;
      right_motor_speed = TURN_SPEED;
      break;
     case DRIVE_RIGHT:
      left_motor_speed = TURN_SPEED;
      right_motor_speed = TURN_SPEED | SPEED_BACKWARDS;
      break;
     case DRIVE_STOP:
      left_motor_speed = 0;
      right_motor_speed = 0;
      break;
    }
    
    SerialUSB.println(buffer[i]);
   } 
   
   // Flip direction of right wheel movement to adjust for the fact that
   // its mounted backwards (relative to the left wheel)
   right_motor_speed ^= SPEED_BACKWARDS;
   
   // Send new motor speeds to the motors
   Dxl.goalSpeed(LEFT_MOTOR_ID, left_motor_speed);
   Dxl.goalSpeed(RIGHT_MOTOR_ID, right_motor_speed);
   
   digitalWrite(BOARD_LED_PIN, LOW);
}
  
void loop() 
{
}
