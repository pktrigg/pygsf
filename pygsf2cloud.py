import sys

import argparse
from datetime import datetime
import geodetic
from glob import glob
import math
import numpy as np
import pygsf
import time
import os.path
import warnings
import geopy
from geopy.distance import VincentyDistance


# ignore numpy NaN warnings when applying a mask to the images.
warnings.filterwarnings('ignore')

def main():
	start_time = time.time() # time the process
	parser = argparse.ArgumentParser(description='Read GSF file and create a point cloud file from DXYZ data.')
	parser.add_argument('-i', dest='inputFile', action='store', help='-i <filename> : input filename to image. It can also be a wildcard, e.g. *.gsf')

	if len(sys.argv)==1:
		parser.print_help()
		sys.exit(1)
	
	args = parser.parse_args()

	# print ("processing with settings: ", args)
	for filename in glob(args.inputFile):
		if not filename.endswith('.gsf'):
			print ("File %s is not a .gsf file, skipping..." % (filename))
			continue

		convert(filename)


def convert(filename):	
	recCount = 0

	# create a GSFREADER class and pass the filename
	r = pygsf.GSFREADER(filename)
	navigation = r.loadnavigation()

	arr = np.array(navigation)
	times = arr[:,0]
	latitudes = arr[:,1]
	longitudes = arr[:,2]

	start_time = time.time() # time the process

	while r.moreData():
		numberofbytes, TypeOfDatagram, datagram = r.readDatagram()
		if TypeOfDatagram ==  pygsf.SWATH_BATHYMETRY:
			datagram.read()
			recDate = datagram.currentRecordDateTime()

			if datagram.numbeams > 1:
				# interpolate so we know where the ping is located
				lat = np.interp(datagram.to_timestamp(recDate), times, latitudes, left=None, right=None)
				lon = np.interp(datagram.to_timestamp(recDate), times, longitudes, left=None, right=None)
				latRad = math.radians(lat)
				lonRad = math.radians(lon)

				# needed for an optimised algorithm
				localradius = calculateradiusFromLatitude(lat)
				
				# for each beam in the ping, compute the real world position
				for i in range(len(datagram.DEPTH_ARRAY)):
					#native python version are faster than numpy
					# given the Dx,Dy soundings, compute a range, bearing so we can correccttly map out the soundings
					brg = ( (180 / math.pi) * math.atan2(datagram.ALONG_TRACK_ARRAY[i], datagram.ACROSS_TRACK_ARRAY[i]) )
					rng = math.sqrt( (datagram.ACROSS_TRACK_ARRAY[i]**2) + (datagram.ALONG_TRACK_ARRAY[i]**2) )

					# x,y = positionFromRngBrg4(lat, lon, rng, brg + datagram.Heading)
					
					x,y = destinationPoint(lat, lon, rng, brg + datagram.heading, localradius)

					# a faster algorithm
					# x, y = positionFromRngBrg2(localradius, latRad, lonRad, rng, brg + datagram.Heading)
					# based on the transducer position, range and bearing to the sounding, compute the sounding position.
					# x,y,h = geodetic.calculateGeographicalPositionFromRangeBearing(lat, lon, brg + datagram.Heading, rng)

					# print ("%.10f, %.10f" % (x1 - x, y1 - y))
					print ("%.10f, %.10f, %.3f" % (x, y, datagram.DEPTH_ARRAY[i]))
			recCount = recCount + 1

	r.close()
	eprint("Duration %.3fs" % (time.time() - start_time )) # time the process

	return navigation

def destinationPoint(lat1, lon1, distance, bearing, radius):
	'''
	http://www.movable-type.co.uk/scripts/latlong.html
	'''
	radius = 6371000

	# // sinφ2 = sinlat1⋅cosangulardist + coslat1⋅sinangulardist⋅cosbearing
	# // tanangulardistλ = sinbearing⋅sinangulardist⋅coslat1 / cosangulardist−sinlat1⋅sinφ2
	# // see http://williams.best.vwh.net/avform.htm#LL

	angulardist = distance / radius #; // angular distance in radians
	bearing = math.radians(bearing)

	lat1 = math.radians(lat1) # this.lat.toRadians();
	lon1 = math.radians(lon1) # this.lon.toRadians();

	sinlat1 = math.sin(lat1)
	coslat1 = math.cos(lat1)
	sinangulardist = math.sin(angulardist)
	cosangulardist = math.cos(angulardist)
	sinbearing = math.sin(bearing)
	cosbearing = math.cos(bearing)

	sinφ2 = sinlat1*cosangulardist + coslat1*sinangulardist*cosbearing
	φ2 = math.asin(sinφ2)
	y = sinbearing * sinangulardist * coslat1
	x = cosangulardist - sinlat1 * sinφ2
	λ2 = lon1 + math.atan2(y, x)

	return ((math.degrees(λ2)+540) % 360-180, (math.degrees(φ2)+540) % 360-180)
	# return new LatLon(φ2.toDegrees(), (λ2.toDegrees()+540)%360-180); // normalise to −180..+180°


def calculateradiusFromLatitude(lat):
	'''
	given a latitude compute a localised earth radius in metres using wgs84 ellipsoid 
	https://rechneronline.de/earth-radius/
	'''
	r = 6378.137 # semi major axis for wgs84
	rp = 6356.752 # semi minor axis for wgs 84
	B = math.radians(lat)
	cosB = math.cos(B)
	sinB = math.sin(B) 

	R = (((r**2) * cosB)**2 + ((rp**2) * sinB)**2) / ((r * cosB)**2 + (rp * sinB)**2)
	R = math.sqrt(R)
	return R * 1000

def positionFromRngBrg4(lat1, lon1, d, angle):
	'''
	given: lat1, lon1, angle = bearing in degrees, d = distance in kilometers
	'''
	d = d / 1000

	origin = geopy.Point(lat1, lon1)
	destination = VincentyDistance(kilometers=d).destination(origin, angle)

	return (destination.longitude, destination.latitude)

def positionFromRngBrg3():

	R = 6378.1 #Radius of the Earth
	brng = 1.57 #Bearing is 90 degrees converted to radians.
	d = 15 #Distance in km

	#lat2  52.20444 - the lat result I'm hoping for
	#lon2  0.36056 - the long result I'm hoping for.

	lat1 = math.radians(52.20472) #Current lat point converted to radians
	lon1 = math.radians(0.14056) #Current long point converted to radians

	lat2 = math.asin( math.sin(lat1)*math.cos(d/R) +
		math.cos(lat1)*math.sin(d/R)*math.cos(brng))

	lon2 = lon1 + math.atan2(math.sin(brng)*math.sin(d/R)*math.cos(lat1),
				math.cos(d/R)-math.sin(lat1)*math.sin(lat2))

	lat2 = math.degrees(lat2)
	lon2 = math.degrees(lon2)

	print(lat2)
	print(lon2)

###############################################################################
def positionFromRngBrg2(localradius, latitude1, longitude1, d, angle):
	'''
	compute geographical position efficiently
	https://stackoverflow.com/questions/7222382/get-lat-long-given-current-point-distance-and-bearing
	'''
	R = localradius
	# Earth Radious in KM
	R = 6378.137 #6378.14;
	d = d / 1000

	brng = math.radians(angle)

	latitude2 = math.degrees( math.asin(math.sin(latitude1) * math.cos(d / R) + math.cos(latitude1) * math.sin(d / R) * math.cos(brng)) )
	longitude2 = math.degrees( longitude1 + math.atan2(math.sin(brng) * math.sin(d / R) * math.cos(latitude1), math.cos(d / R) - math.sin(latitude1) * math.sin(latitude2)) )

	return longitude2, latitude2;
###############################################################################
def positionFromRngBrg(lat, lon, rng, brg):

	R = 6378137/1000 #Radius of the Earth based on half WGS84 semi-major 6378137
	brng = math.radians(brg) #Bearing is 90 degrees converted to radians.
	d = rng/1000 #Distance

	lat1 = math.radians(lat) #Current lat point converted to radians
	lon1 = math.radians(lon) #Current long point converted to radians

	lat2 = math.asin( math.sin(lat1)*math.cos(rng/R) +
		math.cos(lat1)*math.sin(rng/R)*math.cos(brg))

	lon2 = lon1 + math.atan2(math.sin(brg)*math.sin(rng/R)*math.cos(lat1),
				math.cos(rng/R)-math.sin(lat1)*math.sin(lat2))

	lat2 = math.degrees(lat2)
	lon2 = math.degrees(lon2)

	return lat2, lon2

def update_progress(job_title, progress):
	length = 20 # modify this to change the length
	block = int(round(length*progress))
	msg = "\r{0}: [{1}] {2}%".format(job_title, "#"*block + "-"*(length-block), round(progress*100, 2))
	if progress >= 1: msg += " DONE\r\n"
	sys.stdout.write(msg)
	sys.stdout.flush()

def eprint(*args, **kwargs):
	print(*args, file=sys.stderr, **kwargs)

if __name__ == "__main__":
	main()

