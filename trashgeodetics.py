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

