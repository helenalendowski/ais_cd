import pynmea2
from pyais import *
from math import radians, cos, sin, asin, sqrt


def haversine(lat1, lon1, lat2, lon2):
    """
        Calculate the great circle distance between two points on the earth (specified in decimal degrees)
        If both points are in the same hemisphere (N or S), the latitudes must be subtracted to obtain the difference in latitude.
        If both points are in different hemispheres (N or S), the latitudes must be added to obtain the difference in latitude.
        Same counts for longitudes in the same/different hemisphere/s (W or E)
        Note: different hemispheres can be neglected, since boats in AIS range are probably in the same hemisphere.
        (especially since this script is for German waters).
        Function returns the distance between two points in meters.
    """
    r = 6371  # Earth radius in kilometers km; it ranges from nearly 6378 km to nearly 6357 km

    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)

    a = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lon / 2) ** 2
    c = 2 * asin(sqrt(a))

    return c * r * 1000


#gps_msg = '$GNGGA,075226.00,6012.57453,N,02458.65314,E,1,07,2.08,59.3,M,17.7,M,,*7E'
gps_msg = '$GNRMC,075226.00,A,6012.57453,N,02458.65314,E,0.624,,220922,,,A*68'
gga = pynmea2.parse(gps_msg)
print(gga.latitude)
print(gga.longitude)
#print(gga.timestamp)
print(repr(gga))

# receives !AIVDM Messages
ship_msg = '!AIVDM,1,1,,,33KKKd0P@S1j>rTRKGadvrAF01u@,0*14'       # sample aivdm message
decoded = decode(ship_msg)
print(decoded)
#print(decoded.speed)
#data = decoded.asdict()
#print(data)
#print(data['speed'])

distance = haversine(decoded.lat, decoded.lon, gga.latitude, gga.longitude)
print(f'The distance between the coordinates is {distance} m.')