import sys
import argparse
from datetime import datetime
import geodetic
from glob import glob
import math
# import numpy as np
import pygsf
import time
import os.path
import warnings
import pylasfile
# import geopy
from geopy.distance import VincentyDistance

# ignore numpy NaN warnings when applying a mask to the images.
warnings.filterwarnings('ignore')

def main():
	# start_time = time.time() # time the process
	parser = argparse.ArgumentParser(description='Read GSF file and create a point cloud file from DXYZ data.')
	parser.add_argument('-i', dest='inputFile', action='store', help='-i <filename> : input filename to image. It can also be a wildcard, e.g. *.gsf')
	parser.add_argument('-odir', dest='odir', action='store', default="", help='Specify a relative output folder e.g. -odir conditioned')
	parser.add_argument('-r', action='store_true', default=False, dest='recursive', help='Search recursively from the current folder.  [Default: False]')

	if len(sys.argv)==1:
		parser.print_help()
		sys.exit(1)
	
	args = parser.parse_args()
	matches = []
	
	if args.recursive:
		for root, dirnames, filenames in os.walk(os.path.dirname(args.inputFile)):
			for f in fnmatch.filter(filenames, '*.gsf'):
				matches.append(os.path.join(root, f))
				# print (matches[-1])
	else:
		if os.path.exists(args.inputFile):
			matches.append (os.path.abspath(args.inputFile))
		else:
			for filename in glob(args.inputFile):
				matches.append(filename)
	
	print (matches)

	# # print ("processing with settings: ", args)

	for filename in matches:
		if not filename.endswith('.gsf'):
			print ("File %s is not a .gsf file, skipping..." % (filename))
			continue
		convert(filename, args.odir)

def convert(filename, odir):	
	recCount = 0
	outFileName = os.path.join(os.path.dirname(os.path.abspath(filename)), odir, os.path.splitext(os.path.basename(filename))[0] + ".las")
	outFileName = createOutputFileName(outFileName)
	print("outputfile %s" % outFileName)
	writer = pylasfile.laswriter(outFileName, 1.4)

	# write out a WGS variable length record so users know the coordinate reference system
	writer.writeVLR_WGS84()
	writer.hdr.PointDataRecordFormat = 2

	r = pygsf.GSFREADER(filename)
	scalefactors = r.loadscalefactors()
	start_time = time.time() # time the process

	red = 0
	green = 0
	blue = 0
	gray_LL = 0 # min and max grey scales
	gray_UL = 255
	sample_LL = -60 
	sample_UL = 0
	conv_01_99 = ( gray_UL - gray_LL ) / ( sample_UL - sample_LL )

	while r.moreData():
		numberofbytes, TypeOfDatagram, datagram = r.readDatagram()
		if TypeOfDatagram !=  pygsf.SWATH_BATHYMETRY:
			continue
		# compute the local point scale factor for the computation of the point locations

		datagram.read()
		# recDate = datagram.currentRecordDateTime()
		localradius = calculateradiusFromLatitude(datagram.latitude)

		datagram.scalefactors = scalefactors
		datagram.perbeam = True
		datagram.snippettype = pygsf.SNIPPET_NONE
		datagram.read()
		datagram.cliptwtt(0)
		datagram.clipintensity(0)
		datagram.clippolar(-60,60)
		
		samplearray = datagram.R2Soniccorrection()

		# for each beam in the ping, compute the real world position
		for i in range(len(datagram.DEPTH_ARRAY)):
			if datagram.BEAM_FLAGS_ARRAY[i] < 0:
				continue #skip rejected records
			if datagram.frequency == 100000:
				red = int((samplearray[i] - sample_LL) * conv_01_99)
				red = min(max(0, red), 255)
			if datagram.frequency == 200000:
				green = int((samplearray[i] - sample_LL) * conv_01_99)
				green = min(max(0, green), 255)
			if datagram.frequency == 400000:
				blue = int((samplearray[i] - sample_LL) * conv_01_99)
				blue = min(max(0, blue), 255)
				writer.red.append(red)
				writer.green.append(green)
				writer.blue.append(blue)
				writer.intensity.append(blue)
				# given the Dx,Dy soundings, compute a range, bearing so we can correccttly map out the soundings
				brg = (90 - (180 / math.pi) * math.atan2(datagram.ALONG_TRACK_ARRAY[i], datagram.ACROSS_TRACK_ARRAY[i]) )
				rng = math.sqrt( (datagram.ACROSS_TRACK_ARRAY[i]**2) + (datagram.ALONG_TRACK_ARRAY[i]**2) )
				x,y = destinationPoint(datagram.latitude, datagram.longitude, rng, brg + datagram.heading, localradius)
				writer.x.append(x)
				writer.y.append(y)
				writer.z.append(blue)
				# writer.z.append(datagram.DEPTH_ARRAY[i])
				recCount = recCount + 1
			# print (red, green, blue)
	# before we write any points, we need to compute the bounding box, scale and offsets
	writer.computebbox_offsets()
	writer.writepoints()

	# we need to write the header after writing records so we can update the bounding box, point format etc 
	writer.writeHeader()
	writer.close()
	r.close()
	eprint("Duration %.3fs" % (time.time() - start_time )) # time the process

###############################################################################
# def positionFromRngBrg2(localradius, latitude1, longitude1, d, angle):
# 	'''
# 	compute geographical position efficiently
# 	https://stackoverflow.com/questions/7222382/get-lat-long-given-current-point-distance-and-bearing
# 	'''
# 	R = localradius
# 	# Earth Radious in KM
# 	R = 6378.137 #6378.14;
# 	d = d / 1000

# 	brng = math.radians(angle)

# 	latitude2 = math.degrees( math.asin(math.sin(latitude1) * math.cos(d / R) + math.cos(latitude1) * math.sin(d / R) * math.cos(brng)) )
# 	longitude2 = math.degrees( longitude1 + math.atan2(math.sin(brng) * math.sin(d / R) * math.cos(latitude1), math.cos(d / R) - math.sin(latitude1) * math.sin(latitude2)) )

# 	return longitude2, latitude2;

###############################################################################
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

def update_progress(job_title, progress):
	length = 20 # modify this to change the length
	block = int(round(length*progress))
	msg = "\r{0}: [{1}] {2}%".format(job_title, "#"*block + "-"*(length-block), round(progress*100, 2))
	if progress >= 1: msg += " DONE\r\n"
	sys.stdout.write(msg)
	sys.stdout.flush()

###############################################################################
def createOutputFileName(path):
	'''Create a valid output filename. if the name of the file already exists the file name is auto-incremented.'''
	path	  = os.path.expanduser(path)

	if not os.path.exists(os.path.dirname(path)):
		os.makedirs(os.path.dirname(path))

	if not os.path.exists(path):
		return path

	root, ext = os.path.splitext(os.path.expanduser(path))
	dir	   = os.path.dirname(root)
	fname	 = os.path.basename(root)
	candidate = fname+ext
	index	 = 1
	ls		= set(os.listdir(dir))
	while candidate in ls:
			candidate = "{}_{}{}".format(fname,index,ext)
			index	+= 1

	return os.path.join(dir, candidate)

def eprint(*args, **kwargs):
	print(*args, file=sys.stderr, **kwargs)

if __name__ == "__main__":
	main()

