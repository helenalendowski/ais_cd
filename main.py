import socket
import pynmea2
from pyais import *
import pandas as pd

'''
     First configure SDRAngle settings for RTLSDR-USB to receive AIS messages
     Start this ship collision avoidance script 
          Script connects to SDRAngel through UDP 
          Saves receiving AIVDM messages in dataframe 
          Compares positions and courses of other ships with own position and course to detect collisions

     Messages types of interest:
          1: Position Report Class A
          2: Position Report Class A (Assigned schedule)
          3: Position Report Class A (Response to interrogation)
          4: Base Station Report
          5: Static and Voyage Related Data
          18: Standard Class B CS Position Report
          24: Static Data Report 
     
     Columns of position reports     
          class A: [msg_type, repeat, status, turn, speed, accuracy, lon, lat, course, heading, second, maneuver, spare_1, raim, radio] 
          class B: [msg_type, repeat, reserved_1, speed, accuracy, lon, lat, course, heading, second, reserved_2, cs, display, dsc, band, msg22, assigned, raim, radio] 

'''

# create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('localhost', 5005)
print(f'Starting up on {server_address[0]} port {server_address[1]}')
sock.bind(server_address)

# create a dataframe to store all incoming messages
dataframe = pd.DataFrame()

while True:
     try:
          data, address = sock.recvfrom(1024)
          #print(f'Data: {data}; Address: {address}')
          msg = data.decode(encoding='latin1').replace("\n", "").replace("\r", "")
          decoded = decode(msg)
          data_dict = decoded.asdict()
          #print(f'MMSI: {decoded.mmsi}')
          #print(f'Type: {decoded.msg_type}')

          df = pd.DataFrame(data_dict, index=[0])
          df.set_index('mmsi', inplace=True)                # use the Maritime Mobile Service Identity (MMSI) number of the vessel or base station as index

          if not len(dataframe.index) == 0: # or if not dataframe.empty:
               if decoded.mmsi in dataframe.index:             # check if ship is already in database
                    print('Ship is already in database')
                    dataframe = dataframe.drop(decoded.mmsi)     # delete old ship entry
                    print(dataframe)

                    # TODO update ship entry in database according to received message type
                    '''
                    if (decoded.msg_type <= 3):  # position data report class A
                         print('Position Report Class A')
                    if (decoded.msg_type == 18):
                         print('Standard Class B CS Position Report')
                    '''
          dataframe = pd.concat([dataframe, df])       # append dataframe with new ship entry
          print(dataframe)

     except:
          print('No valid data received.')
          continue
