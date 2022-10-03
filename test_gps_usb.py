import io
import pynmea2
import serial # install pyserial

"""
    Script to test GPS USB device 
    GPRMC
"""

#adjust path to gps usb device. For my setup in Windows 11 it's port COM6
ser = serial.Serial("COM6", 9600, timeout=5.0)
#sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))

#test pynmea2
#message = '$GNGGA,075226.00,6012.57453,N,02458.65314,E,1,07,2.08,59.3,M,17.7,M,,*7E'
#gga = pynmea2.parse(message)
#print(gga.latitude)
#print(gga.longitude)
#print(gga.timestamp)

while 1:
    try:
        line = ser.readline()
        msg = line.decode(encoding='latin1').replace("\n", "").replace("\r", "")

        #if(len(msg) != 0):  #to see all NMEA message types
         #   print(msg)
        if (msg.startswith('$GNRMC')):
        #if (msg.startswith("$GNGGA")):
            gga = pynmea2.parse(msg)
            print(repr(gga))
    except serial.SerialException as e:
        print('Device error: {}'.format(e))
        break
    except pynmea2.ParseError as e:
        print('Parse error: {}'.format(e))
        continue