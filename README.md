# ais_cd

# Project description:
    This project implements a simple vessel collision warning system based on AIS data. 
    The script connects to SDRAngel through a UDP socket and saves receiving AIVDM/AIVDO messages in a dataframe. 
    Decoding messages with the pyais library (https://pypi.org/project/pyais/) to collect position(lat,lon), speed and heading of other vessels.
    Receiving the own ship data from a gps dongle and decode with pynmea2 (https://pypi.org/project/pynmea2/).
    Calculates the closest time of approach (cpa) and time to closest time of approach (tcpa) of own ship to other targets with 
    the ARPAoCALC Python library (https://github.com/nawre/arpaocalc) 
    Sends a collision warning if there are possible collisions. 

    Hardware requirements: SDR dongle (e.g, RTL-SDR or USRPB210), GPS serial device 

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

## Instructions: 
1. SDRangle
    1.1 Download SDRAngel from https://www.sdrangel.org/ 
    1.2 Configure SDRAngle settings for RTLSDR-USB to receive AIS messages

2. GPS set up
    2.1 Find out GPS port and baud rate 
    2.2 Adjust values in collision_detection.py
    
3. Start SDRAngle 

4. Run collision_detection.py


## Raspberry Pi set up
1. Install OpenPlotter OS on Raspberry Pi 4 https://openplotter.readthedocs.io/en/latest/getting_started/downloading.html. You can follow this [tutorial on YouTube] (https://www.youtube.com/watch?v=WIW1iKOsoGk). 
1.1 Download OpenPlotter Starting version from: https://cloud.openmarine.net/s/mxrBi5K7zRj2gDq -> unzip the folder
1.2 Download Raspberry Pi Imager: https://www.raspberrypi.com/software/ and install it. Run it to write the imager that you just unzipped (in 1.1) on the SD card.
1.3 Put SD card into Raspberry Pi, power it and follow set up wizard (set country, change password (default: "raspberry"), connect to wireless network or plugin network cable, update software).
1.4 Reboot
2. Set up gps. you can follow this [tutorial on YouTube](https://www.youtube.com/watch?v=umfw8uLDkc0).
2.1 Go to "Pi" -> "OpenPlotter" -> "Serial" -> "Devices"
2.2 Connect gps dongle to one of the Raspberry Pi ports and click "Refresh"
2.3 Click on the device, enter an alias in lower case letters at least 4 characters (e.g., "gnss"), select "NMEA 0183" for data and press "Apply"
2.4 Go to the "Connections" tab, click on the device and "Add to Signal K", select "AUTO"
2.5 Go to OpenCPN -> „Options“ -> „Connections“ and apply the Signal K Protocol {Type: Network, Protocol: TCP, Address: localhost, DataPort: 3000, Receive Input on this Port)
2.6 To test the hardware open "OpenCPN", if everthing is correct you see three green bars in the upper right corner and a red boat icon on the map which is your location. Note: place the gps device close to a window. 
3. Set up LED and find out resistor. Raspberry Pi see [General Purpose Input/Output (GPIO) pins](https://pinout.xyz/#). You need: breadboard, jumper wires, LED, and resistor. 
3.1 Calculate the difference between the voltage of the Pi (3,3V) and the LED (e.g., 2V): 3.3V - 2V = 1.3V. The higher the voltage, the brighter the LED. 
3.2 The amperage is specified in the [datasheet](https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-datasheet.pdf) with up to 500mA. Calculate resistor: R = U/I. Take the next higher available resistor. The larger the resistance, the more it limits the current.
3.3 Connect LED cathode (shorter LED leg) to a ground pin. 
3.4 Connect LED anode (longer LED leg) to the positive supply of the circuit. And adjust GPIO pin (led_pin) in collision_detection.py

### Some useful terminal commands:
To check your operationg system version and Raspberry model run: 
```
uname -a
cat /proc/device-tree/model
```
Raspberry Pi GPIO pins: 
```
pinout
gpio readall
```
Devices: 
```
lsusb
dmesg -Hw
```
Raspberry Pi software configurations:
```
sudo raspi-config
```

### Useful tutorials:
To get started with Raspberry see for example "Raspberry on a boat - Playlist" (https://www.youtube.com/playlist?list=PLgYS2FpH2f4rLgdJ05F4KAOMvAgsLH1da)
