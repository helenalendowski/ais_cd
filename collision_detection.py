import pynmea2
from pyais import *         # https://pypi.org/project/pyais/
import socket       # socket programming library
import serial       # install pyserial
import pandas as pd
import sys
from arpaocalc import Ship, ARPA_calculations   # math functions to calculate cpa & tcpa
import time
import signal

"""
     First configure SDRAngle settings for RTLSDR-USB to receive AIS messages
     Adjust GPS port path 
     Start this ship collision avoidance script 
          Script connects to SDRAngel through UDP
          Saves receiving AIVDM messages in dataframe 
          Collects position(lat,lon), speed and heading of own ship and other vessels
          Calculates the closest time of approach (cpa) and time to closest time of approach (tcpa) of own ship to other targets
          Sends a signal if there is a possible collision

     Messages types of interest for collisions:
          1: Position Report Class A
          2: Position Report Class A (Assigned schedule)
          3: Position Report Class A (Response to interrogation)
          5: Static and Voyage Related Data 
          18: Standard Class B CS Position Report
          19: Extended Class B Equipment Position Report
          24: Static Data Report 
          
    This script supports AIS message type 1,2,3,18, and 19.
    Static and voyage related data of other vessels is not yet included, since data has to be configured by vessel owners and often isin't defined. 
     
     Columns of position reports     
          class A (1,2,3): [msg_type, repeat, mmsi, status, turn, speed, accuracy, lon, lat, course, heading, second, maneuver, spare_1, raim, radio] 
          class B (18): [msg_type, repeat, mmsi, reserved_1, speed, accuracy, lon, lat, course, heading, second, reserved_2, cs, display, dsc, band, msg22, assigned, raim, radio] 
  
    STDMA (Self Organized Time Division Multiple Access) technique ensures that report from one AIS station fits into one of 
    2250 time slots of 26.6 milliseconds established every 60 seconds on each frequency. 
    Therefore, this script listens to socket for 60 seconds before calculating the closest points of approach.
"""

dataframe = pd.DataFrame()      # to store AIS incoming messages
seconds_to_listen = 60          # to receive AIS messages for 60s before running collision test
min_distance = 0.2159827        # minimum distance in nautical mile;     0.00108 Nm = 2m         0.2159827 Nm = 400m
led_pin = 3

if sys.platform.startswith('win32'):
    # Windows-specific code here...
    import winsound
    platform = 'w'
    valid_signals = signal.valid_signals()
    print('Platform = Windows')
    print(f'Valid signals are: {valid_signals}')
    signal_insert_number = signal.SIGBREAK     # press STRG + fn to insert a new minimum distance
elif sys.platform.startswith('linux'):
    # Linux-specific code here...
    import RPi.GPIO as GPIO                 # library to control raspberry pi LED
    # TODO: RPi.GPIO unsuitable for real-time or timing critical applications
    platform = 'l'
    # signal_insert_number = signal.SIGBREAK does it exist? or signal.SIGTSTP (CRTL + Z)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(led_pin, GPIO.OUT)
    valid_signals = signal.valid_signals()
    print(valid_signals)
else:
    print('Operating system is not supported.')
    sys.exit()


def convert_pos_to_dd(lat, lat_dir, lon, lon_dir):
    """
    :param lat: has the format 'DDMM.MMMMM' string
    :param lat_dir: 'N' or 'S' (North/South)
    :param lon: has the format 'DDDMM.MMMMM' string
    :param lon_dir: 'E' or 'W' (East/West)
    :return: lat, lon in decimal degrees using the formula: decimal = degrees + minutes / 60.0 + seconds / 3600.0
    """

    direction = {'N': 1, 'S': -1, 'E': 1, 'W': -1}
    try:
        lat_degrees = int(lat[:2])
        lat_minutes = float(lat[2:])

        lat_decimal = (lat_degrees + lat_minutes / 60.0) * direction[lat_dir]
        lat_decimal = round(lat_decimal, 5)

        lon_degrees = int(lon[:3])
        lon_minutes = float(lon[3:])

        lon_decimal = (lon_degrees + lon_minutes / 60.0) * direction[lon_dir]
        lon_decimal = round(lon_decimal, 5)

        # print(f' lat_decimal: {lat_decimal}, lon_decimal: {lon_decimal}')

        return lat_decimal, lon_decimal

    except:
        print(f'Arguments (lat: {lat} of type {type(lat)} and lon: {lon}) of type {type(lon)} are not valid.')
        print(f'Arguments (lon_dir: {lat_dir} of type {type(lat_dir)} and lon: {lon_dir}) of type {type(lon_dir)}')
        return None, None


class SerialGPS:
    """
        Serial GPS class. To connect to usb device find out the port and baud rate of your device.
        My gps device: NL-8012U (NaviLock)
        E.g., port path: '/dev/ttyUSB0' on Linux or 'COM6' on Windows
        E.g., typical baud rates: 75, 110, 300, 1200, 2400, 4800, 9600, 19200, 38400, 57600 and 115200 bit/s
    """
    def __init__(self, port, baudrate):
        self.port = serial.Serial(port, baudrate)
        if not self.port.isOpen():
            self.port.open()

    def port_open(self):
        if not self.port.isOpen():
            self.port.open()
            print('Serial port is open.')

    def port_close(self):
        self.port.close()
        print('Serial port is closed.')

    def serial_reader(self):
        while True:
            try:
                data = self.port.readline()
                msg = data.decode(encoding='latin1').replace("\n", "").replace("\r", "")
                if (msg.startswith("$GNRMC")):
                    gnrmc = pynmea2.parse(msg)
                    # print(repr(gnrmc))

                    if gnrmc.spd_over_grnd is None:               # if speed is not defined set speed to zero
                        speed = 0.0000
                    else:
                        speed = float(gnrmc.spd_over_grnd)      # TODO: serial gps speed is greater 0.1 without moving

                    if gnrmc.true_course is None:                 # if course is not defined set course to zero
                        course = 0.0000
                    else:
                        course = float(gnrmc.true_course)

                    lat, lon = convert_pos_to_dd(gnrmc.lat, gnrmc.lat_dir, gnrmc.lon, gnrmc.lon_dir)

                    if lat is None:
                        print(f'Input lat = {gnrmc.lat}; lon = {gnrmc.lon} are not valid for convert_pos_to_dd()')
                        continue
                    else:
                        return {'lat': lat, 'lon': lon, 'speed': speed, 'course': course}

            except serial.SerialException as e:
                print('Device error: {}'.format(e))
                break
            except pynmea2.ParseError as e:
                print('Parse error: {}'.format(e))
                continue


def socket_reader(seconds):
    """
    :param seconds: seconds to listen to UDP socket
    :return: none

    Function to receive NMEA AIS sentences (!AIVDM/!AIVDO) from SDRAngle via UDP socket.
    In SDRAnge enable UDP via '127.0.0.1 : 5005' and select Format: 'NMEA'
    Stores incoming ship data in global dataframe.
    """
    global dataframe
    global sock
    t_end = time.time() + seconds
    supported_msg_types = [1, 2, 3, 18, 19]         # AIS message types that are position reports

    while time.time() < t_end:                      # run for a defined amount of seconds
        try:
            # receive AIS NMEA sentences
            data, address = sock.recvfrom(1024)     # reserve bits for data
            # print(f'Data: {data}; Address: {address}')
            msg = data.decode(encoding='latin1').replace("\n", "").replace("\r", "")
            decoded = decode(msg)           # pyais decode message function
            data_dict = decoded.asdict()

            df = pd.DataFrame(data_dict, index=[0])
            df.set_index('mmsi', inplace=True)  # use the Maritime Mobile Service Identity (MMSI) number of the vessel or base station as index

            if decoded.msg_type in supported_msg_types:
                # print('Position report class A or class B')

                if not len(dataframe.index) == 0:  # if not dataframe.empty
                    if decoded.mmsi in dataframe.index:  # check if ship is already in dataframe
                        # print('Ship is already in database. Delete old ship entry.')
                        dataframe = dataframe.drop(decoded.mmsi)

                dataframe = pd.concat([dataframe, df])  # append dataframe with new ship entry

        except KeyboardInterrupt:
            # TODO: Windows Socket.recv() does not raise KeyboardInterrupt for SIGINT;
            #  improve exit handling see https://github.com/codypiersall/pynng/issues/49
            break
        except:
            print('Pyais error. Invalid NMEA message.')
            continue


def check_collision(cpa, tcpa):
    """
    :param cpa: closest point of approach in nautical miles
                value is positive or negative corresponding to CPA position ahead or astern the ship's beam
    :param tcpa: time to closest point of approach in minutes
    :return: collision true: 1 or false: 0
    """
    global min_distance              # minimum distance to other vessels in nautical mile

    # if (0 <= cpa < min_distance):  # if you only want a warning if a ship is getting close ahead of your ship
    if(abs(cpa) < min_distance):   # if you also want a warning if a ship is getting close astern your ship
        print('Collision detected in ', tcpa, 'minutes.')
        return 1
    else:
        return 0


def give_warning():
    global platform
    print('Collision warning!')
    if platform == 'l':
        GPIO.output(led_pin, True)  # turn on LED on Raspberry Pi
    elif platform == 'w':
        winsound.Beep(440, 2000)  # on Windows creates 440Hz sound that lasts 2000 milliseconds


def remove_warning():
    global platform
    print('There are no collisions!')
    if platform == 'l':
        GPIO.output(led_pin, False)     # turn off LED on Raspberry Pi
    else:
        return


def set_min_distance():
    # Let the user define the minimum distance to other vessels
    # print('Signal handler called with signal', signum)
    global min_distance
    while True:
        value = input("Set the minimum allowed distance to other vessels before getting a collision warning."
                      "\nPlease enter a number in meters:\n")
        value = value.replace(',', '.')
        try:
            value = float(value)
            min_distance = abs(value) * 5.399568e-4
            print(f'The minimum distance is {abs(value)} meters, respectively {min_distance} nautical miles ')
            break
        except:
            print(f'Error: Your minimum distance: "{value}" of type {type(value)} is not a valid number. '
                  f'Please try again.')


# connect to gps: adjust path to gps usb device port. For my setup on Windows it's port COM6
MyGPS = SerialGPS("COM6", 9600)

# create UDP socket/ server
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('localhost', 5005)                    # define ip address and a port according to settings in SDRangle
print(f'Starting up on {server_address[0]} port {server_address[1]}')
sock.bind(server_address)


def exit_handler(signum, frame):
    global MyGPS
    global sock
    print('Exit signal handler called with signal', signum)
    MyGPS.port_close()
    sock.close()
    sys.exit()


# register signal handler 'SIGINT'(Interrupt Signal = CTRL + C, on Windows CTRL + F2) to exit the program
signal.signal(signal.SIGINT, exit_handler)
# register signal handler 'SIGBREAK'(Interrupt Signal = CTRL + C, on Windows [FN] +[B]) to change the minimum distance during runtime
# signal.signal(signal_insert_number, set_min_distance)

# create a dataframe to store all closest points of approach
all_cpa = pd.DataFrame()

# Let the user define the minimum distance to other vessels
set_min_distance()

try:

    while True:
        # receive AIS messages
        print(f'Collecting ship position reports for {seconds_to_listen} seconds.')
        socket_reader(seconds_to_listen)

        # get own ship position from serial gps
        pos_GPS = MyGPS.serial_reader()
        print(f'Own ship position data: {pos_GPS}')

        # Ship(position(longitude and latitude in decimal degrees), Speed in knots, heading in degrees)
        objectA = Ship((pos_GPS['lon'], pos_GPS['lat']), pos_GPS['speed'], pos_GPS['course'])

        for i, row in dataframe.iterrows():     # for each vessel in the dataframe check collision
            print('MMSI', i, ';', 'lat =', row['lat'], ';', 'lon =', row['lon'], ';', 'accuracy =', row['accuracy'], ';'
                  , 'speed =', row['speed'], ';', 'course =', row['course'], ';', 'heading =', row['heading'])

            if (row['heading'] == 511):     # hading: 511 = N/A, otherwise heading: 0 to 359 degrees
                heading = row['course']     # NOTE: This is mostly the case! course N/A = 360°
                # print('heading not available, set heading to course =', row['course'])
            else:
                heading = row['heading']

            objectB = Ship((row['lon'], row['lat']), row['speed'], heading)

            # ARPA_calculations returns the CPA (closest point of approach) nautical miles and
            # TCPA (time to closest point of approach) in minutes
            results = ARPA_calculations(objectA, objectB)

            collision = check_collision(results['cpa'], results['tcpa'])

            row_data = {'cpa (Nm)': results['cpa'], 'tcpa (min)': results['tcpa'], 'collision': collision}

            if (len(all_cpa.index) != 0) and (i in all_cpa.index):     # check if the ship already exists in dataframe
                all_cpa.loc[i] = row_data
                # print('Vessel entry already exists. Values updated.')
            else:
                row_dataframe = pd.DataFrame(data=row_data, columns=['cpa (Nm)', 'tcpa (min)', 'collision'], index=[i])
                all_cpa = pd.concat([all_cpa, row_dataframe])  # append dataframe with new ship entry

        print(all_cpa)

        if 1 in all_cpa.collision.values:
            give_warning()
        else:
            remove_warning()

        print('')

except KeyboardInterrupt:
    print('KeyboardInterrupt. Program exit.')
    exit_handler(None, None)
