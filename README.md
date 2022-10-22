# ais_cd

Project description:
    This project implements a simple vessel collision warning system based on AIS data. 
    The script connects to SDRAngel through a UDP socket and saves receiving AIVDM/AIVDO messages in a dataframe. 
    Decoding messages with the pyais library (https://pypi.org/project/pyais/) to collect position(lat,lon), speed and heading of other vessels.
    Receiving the own ship data from a gps dongle and decode with pynmea2 (https://pypi.org/project/pynmea2/).
    Calculates the closest time of approach (cpa) and time to closest time of approach (tcpa) of own ship to other targets with 
    the ARPAoCALC Python library (https://github.com/nawre/arpaocalc) 
    Sends a collision warning if there are possible collisions. 

    Hardware requirements: SDR dongle (e.g, RTL-SDR or USRPB210), GPS dongle

    AIS messages types of interest for collisions:
          1: Position Report Class A
          2: Position Report Class A (Assigned schedule)
          3: Position Report Class A (Response to interrogation)
          5: Static and Voyage Related Data 
          18: Standard Class B CS Position Report
          19: Extended Class B Equipment Position Report
          24: Static Data Report 
          
    This script supports message type 1,2,3,18, and 19.
    Static and voyage related data of other vessels is not supported, since data has to be configured by vessel owners and often isin't available. 

    STDMA (Self Organized Time Division Multiple Access) technique ensures that report from one AIS station fits into one of 
    2250 time slots of 26.6 milliseconds established every 60 seconds on each frequency. 
    Therefore, this script listens to socket for 60 seconds before checking for collisions. 

Instructions: 
1. SDRangle
    1.1 Download SDRAngel from https://www.sdrangel.org/ 
    1.2 Configure SDRAngle settings for RTLSDR-USB to receive AIS messages

2. GPS set up
    2.1 Find out GPS port and baud rate 
    2.2 Adjust values in collision_detection.py

3. Collision warning
    Adjust minimum distance (min_distance) in nautical miles to other vessels according to your own preference in collision_detection.py

3. Start SDRAngle 
4. Run collision_detection.py


