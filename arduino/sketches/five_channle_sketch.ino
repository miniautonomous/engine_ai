/*
  Description:
    This is an optimized version of the package (pip install arduino-python3).
    It was optimized specifically for the python control interface by removing all
    unused functions and implementing external interrupt request to read PWM since the
    easy way of using the Arduino pulseIn function was giving noise and delay problems.

    Original author of arduino-python3:   Morten Kals
*/
#include <SoftwareSerial.h>
#include <Servo.h>

SoftwareSerial *sserial = NULL;
Servo servos[8];
int servo_pins[] = {0, 0, 0, 0, 0, 0, 0, 0};
boolean connected = false;

// For reading PWM correctly using external interrupts
// The Arduino Mega2560 has 6 interrupts as follow;
//
// interrupt 0 => pin 2, used for throttle
byte PWM_THROTTLE = 0;
volatile int thrtlPWM = 0;
volatile int thrtlPrevTime = 0;
//
// interrupt 1 => pin 3
/* NOT currently used*/
//
// interrupt 2 => pin 21, used for steering
byte PWM_STEERING = 2;
volatile int steerPWM = 0;
volatile int steerPrevTime = 0;
//
// interrupt 3 => pin 20, used for throttle+steering by DNN
byte PWM_FULLAI = 3;
volatile int fullaiPWM = 0;
volatile int fullaiPrevTime = 0;
//
// interrupt 4 => pin 19 (Mode button)
byte PWM_MODE = 4;
volatile int modePWM = 0;
volatile int modePrevTime = 0;
//
// interrupt 5 => pin 18, (Record button)
byte PWM_REC = 5;
volatile int recordPWM = 0;
volatile int recordPrevTime = 0;


void thrtlRising() {
  attachInterrupt(PWM_THROTTLE, thrtlFalling, FALLING);
  thrtlPrevTime = micros();
}
 
void thrtlFalling() {
  attachInterrupt(PWM_THROTTLE, thrtlRising, RISING);
  thrtlPWM = micros()-thrtlPrevTime;
}

void getThrottlePWM() {
  Serial.println(thrtlPWM);
}

void steerRising() {
  attachInterrupt(PWM_STEERING, steerFalling, FALLING);
  steerPrevTime = micros();
}
 
void steerFalling() {
  attachInterrupt(PWM_STEERING, steerRising, RISING);
  steerPWM = micros()-steerPrevTime;
}

void getSteeringPWM() {
  Serial.println(steerPWM);
}

void recordRising() {
  attachInterrupt(PWM_REC, recordFalling, FALLING);
  recordPrevTime = micros();
}
 
void recordFalling() {
  attachInterrupt(PWM_REC, recordRising, RISING);
  recordPWM = micros()-recordPrevTime;
}

void getRecordPWM() {
  Serial.println(recordPWM);
}

void modeRising() {
  attachInterrupt(PWM_MODE, modeFalling, FALLING);
  modePrevTime = micros();
}
 
void modeFalling() {
  attachInterrupt(PWM_MODE, modeRising, RISING);
  modePWM = micros()-modePrevTime;
}

void getModePWM() {
  Serial.println(modePWM);
}

void fullaiRising() {
  attachInterrupt(PWM_FULLAI, fullaiFalling, FALLING);
  fullaiPrevTime = micros();
}

void fullaiFalling() {
  attachInterrupt(PWM_FULLAI, fullaiRising, RISING);
  fullaiPWM = micros()-fullaiPrevTime;
}

void getFullAIPWM() {
  Serial.println(fullaiPWM);
}

int Str2int (String Str_value)
{
  char buffer[10]; //max length is three units
  Str_value.toCharArray(buffer, 10);
  int int_value = atoi(buffer);
  return int_value;
}

void split(String results[], int len, String input, char spChar) {
  String temp = input;
  for (int i=0; i<len; i++) {
    int idx = temp.indexOf(spChar);
    results[i] = temp.substring(0,idx);
    temp = temp.substring(idx+1);
  }
}

void Version(){
  Serial.println("version");
}

void SS_set(String data){
  delete sserial;
  String sdata[3];
  split(sdata,3,data,'%');
  int rx_ = Str2int(sdata[0]);
  int tx_ = Str2int(sdata[1]);
  int baud_ = Str2int(sdata[2]);
  sserial = new SoftwareSerial(rx_, tx_);
  sserial->begin(baud_);
  Serial.println("ss OK");
}

void SS_write(String data) {
 int len = data.length()+1;
 char buffer[len];
 data.toCharArray(buffer,len);
 Serial.println("ss OK");
 sserial->write(buffer);
}

void SS_read(String data) {
 char c = sserial->read();
 Serial.println(c);
}

void pulseInHandler(String data){
    int pin = Str2int(data);
    long duration;
    if(pin <=0){
          pinMode(-pin, INPUT);
          duration = pulseIn(-pin, LOW);
    }else{
          pinMode(pin, INPUT);
          duration = pulseIn(pin, HIGH);
    }
    Serial.println(duration);
}

void SV_add(String data) {
    String sdata[3];
    split(sdata,3,data,'%');
    int pin = Str2int(sdata[0]);
    int min = Str2int(sdata[1]);
    int max = Str2int(sdata[2]);
    int pos = -1;
    for (int i = 0; i<8;i++) {
        if (servo_pins[i] == pin) { //reset in place
            servos[pos].detach();
            servos[pos].attach(pin, min, max);
            servo_pins[pos] = pin;
            Serial.println(pos);
            return;
            }
        }
    for (int i = 0; i<8;i++) {
        if (servo_pins[i] == 0) {pos = i;break;} // find spot in servo array
        }
    if (pos == -1) {;} //no array position available!
    else {
        servos[pos].attach(pin, min, max);
        servo_pins[pos] = pin;
        Serial.println(pos);
        }
}

void SV_remove(String data) {
    int pos = Str2int(data);
    servos[pos].detach();
    servo_pins[pos] = 0;
}

void SV_read(String data) {
    int pos = Str2int(data);
    int angle;
    angle = servos[pos].read();
    Serial.println(angle);
}

void SV_write(String data) {
    String sdata[2];
    split(sdata,2,data,'%');
    int pos = Str2int(sdata[0]);
    int angle = Str2int(sdata[1]);
    servos[pos].write(angle);
}

void SV_write_ms(String data) {
    String sdata[2];
    split(sdata,2,data,'%');
    int pos = Str2int(sdata[0]);
    int uS = Str2int(sdata[1]);
    servos[pos].writeMicroseconds(uS);
}

void SerialParser(void) {
  char readChar[64];
  Serial.readBytesUntil(33,readChar,64);
  String read_ = String(readChar);
  //Serial.println(readChar);
  int idx1 = read_.indexOf('%');
  int idx2 = read_.indexOf('$');
  // separate command from associated data
  String cmd = read_.substring(1,idx1);
  String data = read_.substring(idx1+1,idx2);

  // determine command sent
  else if (cmd == "version") {
      Version();
  }
  else if (cmd == "strg") {
      getSteeringPWM();
  }
  else if (cmd == "thrtl") {
      getThrottlePWM();
  }
  else if (cmd == "mode") {
      getModePWM();
  }
  else if (cmd == "rec") {
      getRecordPWM();
  }
  else if (cmd == "fullai"){
      getFullAIPWM();
  }
}

void setup()  {
  Serial.begin(115200);
  attachInterrupt(PWM_STEERING, steerRising, RISING);
  attachInterrupt(PWM_THROTTLE, thrtlRising, RISING);
  attachInterrupt(PWM_MODE, modeRising, RISING);
  attachInterrupt(PWM_REC, recordRising, RISING);
  attachInterrupt(PWM_FULLAI, fullaiRising, RISING);
  while (!Serial) {
  ; // wait for serial port to connect. Needed for Leonardo only
  }
}

void loop() {
   SerialParser();
   }
