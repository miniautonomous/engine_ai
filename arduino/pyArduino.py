"""
  Decription:
    This is an optimized version of the package (pip install arduino-python3).
    It was optimized specifically for the miniAV control interface by removing for all
    unused/needed function and implementing interrupt request to read PWM since the easy
    to use Arduino pulseIn function was giving all kind of problems, see wiki.

    Author:   Francois Charette, Ph.D.
    Created:  February 21, 2020
    Modified: ...
"""
import logging
import itertools
import platform
import serial
import time
from serial.tools import list_ports

if platform.system() == 'Windows':
    import winreg as winreg
else:
    import glob

log = logging.getLogger(__name__)


def enumerate_serial_ports():
    """
    Uses the Win32 registry to return a iterator of serial
        (COM) ports existing on this computer.
    """
    path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
    except WindowsError:
        raise Exception

    for i in itertools.count():
        try:
            val = winreg.EnumValue(key, i)
            yield (str(val[1]))  # , str(val[0]))
        except EnvironmentError:
            break


def build_cmd_str(cmd, args=None):
    """
    Build a command string that can be sent to the arduino.

    Input:
        cmd (str): the command to send to the arduino, must not
            contain a % character
        args (iterable): the arguments to send to the command

    @TODO: a strategy is needed to escape % characters in the args
    """
    if args:
        args = '%'.join(map(str, args))
    else:
        args = ''
    return "@{cmd}%{args}$!".format(cmd=cmd, args=args).encode()


def find_port(baud, timeout):
    """
    Find the first port that is connected to an arduino with a compatible
    sketch installed.
    """
    if platform.system() == 'Windows':
        ports = enumerate_serial_ports()
    elif platform.system() == 'Darwin':
        ports = [i[0] for i in list_ports.comports()]
    else:
        ports = glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
    for p in ports:
        log.debug('Found {0}, testing...'.format(p))
        try:
            sr = serial.Serial(p, baud, timeout=timeout)
            # sr.setDTR(False)
            # time.sleep(1)
            # sr.flushInput()
            # sr.setDTR(True)
        except serial.serialutil.SerialException as e:
            log.debug(str(e))
            continue
        time.sleep(2)
        version = get_version(sr).decode()
        # For some reason, if the Arduino MEGA gets interrupted by using the keyboard
        # then the get_version function will return a numerical string, as if the sketch
        # is still running.
        # If there is nothing connected on the serial port, then get_version returns an
        # empty string.  There to ensure that we are connected to an Arduino, simply
        # if there is an empty string or not.  This is probably less robust than checking
        # specifically for the keyword "version" that gaurantees the right sketch is
        # running, but it is more robust in the sense to re-start an Arduino connection
        if not version:
            # if version != 'version':
            log.debug('Bad version {0}. This is not a Shrimp/Arduino!'.format(
                version))
            sr.close()
            continue
        log.info('Using port {0}.'.format(p))
        if sr:
            return sr
    return None


def get_version(sr):
    cmd_str = build_cmd_str('version')
    try:
        sr.write(cmd_str)
        sr.flush()
    except Exception:
        return None
    return sr.readline().replace("\r\n".encode(), "".encode())


class Arduino(object):

    def __init__(self, baud=9600, port=None, timeout=2, sr=None):
        """
        Initializes serial communication with Arduino if no connection is
        given. Attempts to self-select COM port, if not specified.
        """
        if not sr:
            if not port:
                sr = find_port(baud, timeout)
                if not sr:
                    raise ValueError("Could not find port.")
            else:
                sr = serial.Serial(port, baud, timeout=timeout)
        sr.flush()
        self.sr = sr
        self.SoftwareSerial = SoftwareSerial(self)
        self.Servos = Servos(self)

    def version(self):
        return get_version(self.sr)

    def steerIn(self):
        """
        Reads a pulse on pin 21 (interrupt 2, hard coded in the Arduino sketch)

        returns:
           duration : pulse length measurement
        """
        cmd_str = build_cmd_str("strg")
        try:
            self.sr.write(cmd_str)
            self.sr.flush()
        except:
            pass
        rd = self.sr.readline().replace("\r\n".encode(), "".encode())
        try:
            return float(rd)
        except:
            return -1

    def throttleIn(self):
        """
        Reads a pulse on pin 2 (interrupt 0, hard coded in the Arduino sketch)

        returns:
           duration : pulse length measurement
        """
        cmd_str = build_cmd_str("thrtl")
        try:
            self.sr.write(cmd_str)
            self.sr.flush()
        except:
            pass
        rd = self.sr.readline().replace("\r\n".encode(), "".encode())
        try:
            return float(rd)
        except:
            return -1

    def modeIn(self):
        """
        NOTES:
          * With a 3 channels remotes, this modeIn can have 3 PWMs length, i.e., short, medium
            and high.  These mode are use to scroll through the modes, Manual, autonomous and
            recordings
          * With 4 channels remote, this modeIn only has two PWMs, i.e., short and long, that is
            used to turn the autonomous mode on/off.

        Reads a pulse on pin 19 (interrupt 4, hard coded in the Arduino sketch)

        returns:
           duration : pulse length measurement
        """
        cmd_str = build_cmd_str("mode")
        try:
            self.sr.write(cmd_str)
            self.sr.flush()
        except:
            pass
        rd = self.sr.readline().replace("\r\n".encode(), "".encode())
        try:
            return float(rd)
        except:
            return -1

    def recIn(self):
        """
        NOTES:
          * This method is ONLY used with 4 channels remotes.
          * The 2 PWMs length allows to turn the recording on/off with this 4th channels

        Reads a pulse on pin 18 (interrupt 5, hard coded in the Arduino sketch)

        returns:
           duration : pulse length measurement
        """
        cmd_str = build_cmd_str("rec")
        try:
            self.sr.write(cmd_str)
            self.sr.flush()
        except:
            pass
        rd = self.sr.readline().replace("\r\n".encode(), "".encode())
        try:
            return float(rd)
        except:
            return -1

    def fullAIIn(self):
        """
        NOTES:
          * With a 3 channels remotes, this modeIn can have 3 PWMs length, i.e., short, medium
            and high.  These mode are use to scroll through the modes, Manual, autonomous and
            recordings
          * With 4 channels remote, this modeIn only has two PWMs, i.e., short and long, that is
            used to turn the autonomous mode on/off.

        Reads a pulse on pin 3 (interrupt 20, hard coded in the Arduino sketch)

        returns:
           duration : pulse length measurement
        """
        cmd_str = build_cmd_str("fullai")
        try:
            self.sr.write(cmd_str)
            self.sr.flush()
        except:
            pass
        rd = self.sr.readline().replace("\r\n".encode(), "".encode())
        try:
            return float(rd)
        except:
            return -1

    def pulseIn(self, pin, val):
        """
        Reads a pulse from a pin

        inputs:
           pin: pin number for pulse measurement
        returns:
           duration : pulse length measurement
        """
        if val == "LOW":
            pin_ = -pin
        else:
            pin_ = pin
        cmd_str = build_cmd_str("pi", (pin_,))
        try:
            self.sr.write(cmd_str)
            self.sr.flush()
        except:
            pass
        rd = self.sr.readline().replace("\r\n".encode(), "".encode())
        try:
            return float(rd)
        except:
            return -1

    def close(self):
        if self.sr.isOpen():
            self.sr.flush()
            self.sr.close()


class Servos(object):
    """
    Class for Arduino servo support
    0.03 second delay noted
    """

    def __init__(self, board):
        self.board = board
        self.sr = board.sr
        self.servo_pos = {}

    def attach(self, pin, min=544, max=2400):
        cmd_str = build_cmd_str("sva", (pin, min, max))
        while True:
            self.sr.write(cmd_str)
            self.sr.flush()

            rd = self.sr.readline().replace("\r\n".encode(), "".encode())
            if rd.isdigit():
                break
            else:
                # When the Arduino Mega gets interuppted by the keyboard, it will then
                # keep returning the "version" keyword instead of a number, so reset
                # the Arduino!
                self.sr.setDTR(False)
                time.sleep(1)
                self.sr.flushInput()
                self.sr.setDTR(True)
                log.debug("trying to attach servo to pin {0}".format(pin))
        position = int(rd)
        self.servo_pos[pin] = position
        return 1

    def detach(self, pin):
        position = self.servo_pos[pin]
        cmd_str = build_cmd_str("svd", (position,))
        try:
            self.sr.write(cmd_str)
            self.sr.flush()
        except:
            pass
        del self.servo_pos[pin]

    def write(self, pin, angle):
        position = self.servo_pos[pin]
        cmd_str = build_cmd_str("svw", (position, angle))

        self.sr.write(cmd_str)
        self.sr.flush()

    def writeMicroseconds(self, pin, uS):
        position = self.servo_pos[pin]
        cmd_str = build_cmd_str("svwm", (position, uS))

        self.sr.write(cmd_str)
        self.sr.flush()

    def read(self, pin):
        if pin not in self.servo_pos.keys():
            self.attach(pin)
        position = self.servo_pos[pin]
        cmd_str = build_cmd_str("svr", (position,))
        try:
            self.sr.write(cmd_str)
            self.sr.flush()
        except:
            pass
        rd = self.sr.readline().replace("\r\n".encode(), "".encode())
        try:
            angle = int(rd)
            return angle
        except:
            return None


class SoftwareSerial(object):
    """
    Class for Arduino software serial functionality
    """

    def __init__(self, board):
        self.board = board
        self.sr = board.sr
        self.connected = False

    def begin(self, p1, p2, baud):
        """
        Create software serial instance on
        specified tx,rx pins, at specified baud
        """
        cmd_str = build_cmd_str("ss", (p1, p2, baud))
        try:
            self.sr.write(cmd_str)
            self.sr.flush()
        except:
            pass
        response = self.sr.readline().replace("\r\n".encode(), "".encode())
        if response == "ss OK":
            self.connected = True
            return True
        else:
            self.connected = False
            return False

    def write(self, data):
        """
        sends data to existing software serial instance
        using Arduino's 'write' function
        """
        if self.connected:
            cmd_str = build_cmd_str("sw", (data,))
            try:
                self.sr.write(cmd_str)
                self.sr.flush()
            except:
                pass
            response = self.sr.readline().replace("\r\n".encode(), "".encode())
            if response == "ss OK":
                return True
        else:
            return False

    def read(self):
        """
        returns first character read from
        existing software serial instance
        """
        if self.connected:
            cmd_str = build_cmd_str("sr")
            self.sr.write(cmd_str)
            self.sr.flush()
            response = self.sr.readline().replace("\r\n".encode(), "".encode())
            if response:
                return response
        else:
            return False
