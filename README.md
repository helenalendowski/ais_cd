# ais_cd

## Description
This project implements a simple vessel collision detection system based on the [Automatic Identification System (AIS)](https://en.wikipedia.org/wiki/Automatic_identification_system). You can receive very high frequency (VHF) signals with software defined radio (SDR), e.g., [SDRangel](https://www.sdrangel.org/) which also processes the signals to the NMEA data format.
The script connects to SDRangel through a UDP socket and saves receiving [AIVDM/AIVDO messages](https://gpsd.gitlab.io/gpsd/AIVDM.html) in a dataframe. 
AIVDM/AIVDO sentences are decoded with the [pyais library](https://pypi.org/project/pyais/) to collect the position (latitude, longitude), speed and heading of other vessels.
The script receives the own ship data from a gps dongle and decodes [NMEA 0183](https://en.wikipedia.org/wiki/NMEA_0183) messages with [pynmea2](https://pypi.org/project/pynmea2/).
The script then calculates the closest time of approach (cpa) in nautical miles and time to closest time of approach (tcpa) in minutes of own ship to other targets with the [ARPAoCALC Python library](https://github.com/nawre/arpaocalc). If one of the cpa is less than the defined minimum distance to other vessels by the user (= possible collision), the script sends a collision warning (audio signal on Windows using [winsound](https://docs.python.org/3/library/winsound.html) or lights up a led on Raspberry Pi using [RPi.GPIO](https://pypi.org/project/RPi.GPIO/)). 

[AIS messages types](https://gpsd.gitlab.io/gpsd/AIVDM.html#_ais_payload_interpretation) of interest for collisions:
- 1: Position Report Class A
- 2: Position Report Class A (Assigned schedule)
- 3: Position Report Class A (Response to interrogation)
- 5: Static and Voyage Related Data 
- 18: Standard Class B CS Position Report
- 19: Extended Class B Equipment Position Report
- 24: Static Data Report 
          
This script supports message type 1,2,3,18, and 19.
Static and voyage related data of other vessels is not supported, since data has to be configured by vessel owners and often is not available. 

STDMA (Self Organized Time Division Multiple Access): 2250 time slots of 26.6 ms established every 60 s on each frequency. Therefore, this script listens to socket for 60 seconds before checking for collisions. 

[test_rtlsdr.py](https://github.com/helenalendowski/ais_cd/blob/d2542e78e07ceb7a54afbe9f3fd62acbd226d63c/test_rtlsdr.py) is a start to implement signal processing in Python with [rtlsdr](https://pypi.org/project/pyrtlsdr/) to get rid of the UDP socket and SDRangle -> under construction.

## Hardware requirements
* OS: Windows or Linux (Note: LED signal warning will only work on Raspberry Pi)
* SDR dongle (e.g, RTL-SDR: [Nooelec NESDR SMArt v4](https://www.nooelec.com/store/sdr/sdr-receivers/nesdr/nesdr-smart.html) or [USRPB210](https://www.ettus.com/all-products/ub210-kit/)) to receive VHF
* VHF antenna
* GPS serial device (e.g., [Navilock NL-8012U USB](https://www.navilock.com/produkt/62524/merkmale.html))

## Python libraries
Copied into this project: 
* [ARPAoCALC](https://github.com/nawre/arpaocalc)

Part of standard library that is distributed with Python 3.11.0: 
* [socket](https://docs.python.org/3/library/socket.html)
* [time](https://docs.python.org/3/library/time.html)
* [sys](https://docs.python.org/3/library/sys.html)
* [signal](https://docs.python.org/3/library/signal.html)
* [winsound](https://docs.python.org/3/library/winsound.html) (Windows only) 

Requires installation: 
* [pandas](https://pandas.pydata.org/)
* [pyserial](https://pyserial.readthedocs.io/en/latest/pyserial.html)
* [pyais](https://pypi.org/project/pyais/) 
* [pynmea2](https://pypi.org/project/pynmea2/)
* [RPi.GPIO](https://pypi.org/project/RPi.GPIO/) (Raspberry Pi only) 

## Getting started with SDR
- [Understand settings and variables ](https://www.rtl-sdr.com/sdrsharp-users-guide/) (explanation for SDR#, but similar to SDRangle) 
- [SDRangel features overview](https://www.rtl-sdr.com/sdrangel-features-overview-ads-b-apt-dvb-s-dab-ais-vor-aprs-and-many-more-built-in-apps/)
- Download SDR dongle driver for Windows, e.g., [Zadig](https://zadig.akeo.ie/) or download [Airspy Software Defined Radio Package](https://airspy.com/download/) which includes SDR software and drivers
- If you face problems with "librtlsdr" on Windows go to the [Osmocom project binary builds](https://osmocom.org/projects/rtl-sdr/wiki/Rtl-sdr#Windows) and download zip "[RelWithDebInfo.zip pre-built Windows version":http://lists.osmocom.org/mailman/listinfo/osmocom-sdr]". See [this YouTube tutorial](https://www.youtube.com/watch?v=XT9pybErVW8) for more instructions.

## Project set up 
1. SDRangle
    * [Download SDRAngel](https://www.sdrangel.org/)
    * Install all prerequisites ([Windows](https://github.com/f4exb/sdrangel/wiki/Compile-in-Windows), [Linux](https://github.com/f4exb/sdrangel/wiki/Compile-from-source-in-Linux))
    * See [Quick-start](https://github.com/f4exb/sdrangel/wiki/Quick-start) to navigate through SDRangel and configure settings for RTLSDR-USB to receive AIS messages. See [YouTube tutorial](https://www.youtube.com/watch?v=rTyzEOBs6oI) to get started. 
        * "Add Rx device" -> "Select from list" and choose your SDR device (e.g., "RTL-SDR[0]")
        * center frequency: 0,162,000 kHz 
        * sample rate (SR) according to your SDR hardware (e.g., 2,048,000 S/s) samples per second
        * gain according to your SDR hardware
        * "Add channel" -> "AIS Demodulator"
            * delta f: -0,025,000 Hz (AIS channel A 161.975 MHz (87B))
            * [x] UDP 127.0.0.1:5005   Format:NMEA
        * "Add channel" -> "AIS Demodulator"
            * delta f: +0,025,000 Hz (AIS channel B 162.025 MHz (88B))
            * [x] UDP 127.0.0.1:5005   Format:NMEA
        * optional: "Add feature" -> "AIS" to see vessels in table
        * "Preferences" -> "Save all"
        ![SDRangel example set up](/repository/assets/SDRangel.png?raw=true "SDRangel example set up")
2. GPS set up, e.g., with [u-blocks on Windows](https://canadagps.ca/blogs/knowledgebase-by-platform-windows/connect-a-gps-gnss-receiver-for-windows-maps-windows-10-os)
    * If you face a permission error "serial.serialutil.SerialException: could not open port 'COM6': PermissionError(13, 'Access denied', None, 5)“ [See Windows location service and privacy](https://support.microsoft.com/en-us/windows/windows-location-service-and-privacy-3a8eee0a-5b0b-dc07-eede-2a5ca1c49088)-> Turn on  "Allow apps to access your location" (Start  -> Settings -> Privacy -> Location) and reboot Computer. Several programs cannot access the COM port at the same time. Make sure that you close all other access points. 
    * Find out GPS port and baud rate. In Windows go to "Device Manager" and see list bellow "Ports (COM & LPT)", check port of "u-blox Virtual COM Port (COMXX)" where XX represents a port number. Then right click on device -> Properties -> go to "Connection settings" tab and select bits per second, e.g., 9600 (baud rate). 
    * Adjust values in [collision_detection.py](https://github.com/helenalendowski/ais_cd/blob/da0b0c05c4142e49f5c9bab87ae573d5bd499329/collision_detection.py) according to your GPS device
    
3. Start SDRangle 

4. Run [collision_detection.py](https://github.com/helenalendowski/ais_cd/blob/da0b0c05c4142e49f5c9bab87ae573d5bd499329/collision_detection.py)


## Raspberry Pi 4 
1. Download and install [OpenPlotter OS](https://openplotter.readthedocs.io/en/3.x.x/getting_started/downloading.html) on Raspberry Pi 4. You can follow this [tutorial on YouTube](https://www.youtube.com/watch?v=WIW1iKOsoGk) or the [OpenPlotter installing instructions](https://openplotter.readthedocs.io/en/latest/getting_started/installing.html). 
    * [Download OpenPlotter Starting version](https://cloud.openmarine.net/s/mxrBi5K7zRj2gDq) and unzip the folder
    * Pi only boots from a micro SD card formatted in the "File system: FAT32". Prepare SD card with a [formatter for Windows/Mac OS](https://www.sdcard.org/downloads/formatter/)
    * [Download Raspberry Pi Imager](https://www.raspberrypi.com/software/) and install it. Run it to write the imager that you just unzipped on the SD card.
    * Put SD card into Raspberry Pi, power it and follow set up wizard (set country, change password (default: "raspberry"), connect to wireless network or plugin network cable, update software).
    * Reboot
2. Set up gps, you can follow [this tutorial on YouTube](https://www.youtube.com/watch?v=umfw8uLDkc0).
    * Go to "Pi" -> "OpenPlotter" -> "Serial" -> "Devices"
    * Connect gps dongle to one of the Raspberry Pi ports and click "Refresh"
    * Click on the device, enter an alias in lower case letters at least 4 characters (e.g., "gnss"), select "NMEA 0183" for data and press "Apply"
    * Go to the "Connections" tab, click on the device and "Add to Signal K", select "AUTO"
    * Go to OpenCPN -> „Options“ -> „Connections“ and apply the Signal K Protocol {Type: Network, Protocol: TCP, Address: localhost, DataPort: 3000, Receive Input on this Port)
    * To test the hardware open "OpenCPN", if everthing is correct you see three green bars in the upper right corner and a red boat icon on the map which is your location. Note: place the gps device close to a window and away from metal objects to avoid interference. 
3. Set up LED and find out resistor. Raspberry Pi see [General Purpose Input/Output (GPIO) pins](https://pinout.xyz/#). You need: breadboard, jumper wires, LED, and resistor. 
    * Calculate the difference between the voltage of the Pi (3,3V) and the LED (e.g., 2V): 3.3V - 2V = 1.3V. The higher the voltage, the brighter the LED. 
    * The amperage is specified in the [datasheet](https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-datasheet.pdf) with up to 500mA. Calculate resistor: R = U/I. Take the next higher available resistor. The larger the resistance, the more it limits the current.
    * Connect LED cathode (shorter LED leg) to a ground pin. 
    * Connect LED anode (longer LED leg) to the positive supply of the circuit. And adjust GPIO pin (led_pin) in collision_detection.py
4. Install SDRangle, follow the instructions from [Compile-from-source-in-Linux](https://github.com/f4exb/sdrangel/wiki/Compile-from-source-in-Linux) or [Installing SDRangel for the SDRplay RSP1A and HackRF on a Raspberry Pi](https://www.radiosrs.net/installing_SDRangel.html)
5. [OpenPlotter SDR VHF](https://github.com/openplotter/openplotter-sdr-vhf)

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

### Further useful links:
[Download OpenSeaMap charts](https://ftp.gwdg.de/pub/misc/openstreetmap/openseamap/charts/kap/) for OpenCPN and follow [installation instructions](http://openseamap.smurf.noris.de/index.php?id=opencpn&L=1)

To get started with Raspberry see for example [Raspberry on a boat - Playlist](https://www.youtube.com/playlist?list=PLgYS2FpH2f4rLgdJ05F4KAOMvAgsLH1da)

## Sources:
* AIVDM/AIVDO protocol decoding (2021). Available on: https://gpsd.gitlab.io/gpsd/AIVDM.html (last accessed: 30.10.2022)
* ARPAoCALC Python library. Available on: https://github.com/nawre/arpaocalc (last accessed: 10.10.2022)


This project was created as part of a university course. I assume no liability and the project can not protect against collisions.
