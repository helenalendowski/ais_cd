import socket
import sys
import pynmea2
from pyais import *

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('localhost', 5005)
print(f'starting up on {server_address[0]} port {server_address[1]}')
sock.bind(server_address)

# receives !AIVDM Messages
#message = '!AIVDM,1,1,,,33KKKd0P@S1j>rTRKGadvrAF01u@,0*14'       # sample aivdm message
#decoded = decode(message)
#print(decoded)
#print(decoded.speed)
#data = decoded.asdict()
#print(data)
#print(data['speed'])

while True:
     try:
          data, address = sock.recvfrom(4096)
          print(f'Data: {data}; Address: {address}')
          msg = data.decode(encoding='latin1').replace("\n", "").replace("\r", "")
          decoded = decode(msg)
          print(decoded)
     except:
          print('No valid data received.')
          continue
