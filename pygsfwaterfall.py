import sys
# sys.path.append("C:/development/Python/pyall")

import argparse
import bisect
import csv
from datetime import datetime
import geodetic
from glob import glob
import math
# from matplotlib import pyplot as plt
from matplotlib import cm
import numpy as np
from PIL import Image,ImageDraw,ImageFont, ImageOps, ImageChops
import pygsf
import time
import os.path
import warnings

# ignore numpy NaN warnings when applying a mask to the images.
warnings.filterwarnings('ignore')

def main():
	parser = argparse.ArgumentParser(description='Read GSF file and create a reflectivity image.')
	parser.add_argument('-i', dest='inputFile', action='store', help='-i <ALLfilename> : input ALL filename to image. It can also be a wildcard, e.g. *.gsf')
	parser.add_argument('-z', dest='zoom', default = 0, action='store', help='-z <value> : Zoom scale factor. A larger number makes a larger image, and a smaller number (0.5) provides a smaller image, e.g -z 2 makes an image twice the native resolution. [Default: 0]')
	parser.add_argument('-a', action='store_true', default=False, dest='annotate', help='-a : Annotate the image with timestamps.  [Default: True]')
	parser.add_argument('-r', action='store_true', default=False, dest='rotate', help='-r : Rotate the resulting waterfall so the image reads from left to right instead of bottom to top.  [Default is bottom to top]')
	parser.add_argument('-clip', dest='clip', default = 5, action='store', help='-clip <value> : Clip the minimum and maximum edges of the data by this percentage so the color stretch better represents the data.  [Default - 5.  A good value is -clip 5.]')
	parser.add_argument('-invert', dest='invert', default = False, action='store_true', help='-invert : Inverts the color palette')
	parser.add_argument('-color', dest='color', default = 'graylog', action='store', help='-color <paletteName> : Specify the color palette.  Options are : -color yellow_brown_log, -color gray, -color yellow_brown or any of the palette filenames in the script folder. [Default = graylog for a grayscale logarithmic palette.]' )

	if len(sys.argv)==1:
		parser.print_help()
		sys.exit(1)
	
	args = parser.parse_args()

	print ("processing with settings: ", args)
	for filename in glob(args.inputFile):
		if not filename.endswith('.gsf'):
			print ("File %s is not a .all file, skipping..." % (filename))
			continue
		if not os.path.isfile(filename):
			print ("file not found:", filename)
			exit()

		xResolution, yResolution, beamCount, leftExtent, rightExtent, distanceTravelled, navigation = computeXYResolution(filename)
		print("xRes %.2f yRes %.2f  leftExtent %.2f, rightExtent %.2f, distanceTravelled %.2f" % (xResolution, yResolution, leftExtent, rightExtent, distanceTravelled)) 

		if beamCount == 0:
			print ("No data to process, skipping empty file")
			continue
		zoom = float(args.zoom)
		if (zoom ==0):
			zoom = 1
			# swathWidth = abs(leftExtent)+abs(rightExtent)
			bc = beamCount
			while (bc < 300):
				zoom *= 2
				bc *= zoom 
		createWaterfall(filename, args.color, beamCount, zoom, float(args.clip), args.invert, args.annotate, xResolution, yResolution, args.rotate, leftExtent, rightExtent, distanceTravelled, navigation)

def createWaterfall(filename, colorScale, beamCount, zoom=1.0, clip=0, invert=True, annotate=True, xResolution=1, yResolution=1, rotate=False, leftExtent=-100, rightExtent=100, distanceTravelled=0, navigation=[]):
	print ("Processing file: ", filename)

	start_time = time.time() # time the process
	recCount = 0
	waterfall = []
	minBS = 9999.0
	maxBS = -minBS
	outputResolution = beamCount * zoom
	isoStretchFactor = (yResolution/xResolution) * zoom
	print ("xRes %.2f yRes %.2f isoStretchFactor %.2f" % (xResolution, yResolution, isoStretchFactor))

	r = pygsf.GSFREADER(filename)
	scalefactors = r.loadscalefactors()
	totalrecords = r.getrecordcount()

	while r.moreData():
		numberofbytes, recordidentifier, datagram = r.readDatagram()
		if recordidentifier == 2: #SWATH_BATHYMETRY_PING
			datagram.scalefactors = scalefactors	
			datagram.read()

			if datagram.frequency != 100000:
			# 	print ("skipping freq: %d" % datagram.frequency)
				continue
			# we need to remember the actual data extents so we can set the color palette mappings to the same limits. 
			minBS = min(minBS, min(datagram.MEAN_REL_AMPLITUDE_ARRAY))
			maxBS = max(maxBS, max(datagram.MEAN_REL_AMPLITUDE_ARRAY))

			# print ("MinBS %.3f MaxBS %.3f" % (minBS, maxBS))
			# waterfall.insert(0, np.abs( np.asarray(datagram.Reflectivity)))			

			# we need to stretch the data to make it isometric, so lets use numpy interp routing to do that for Us
			# datagram.AcrossTrackDistance = datagram.AcrossTrackDistance.reverse()
			xp = np.array(datagram.ACROSS_TRACK_ARRAY) #the x distance for the beams of a ping.  we could possibly use the real values here instead todo
			# datagram.Reflectivity.reverse()
			fp = np.abs(np.array(datagram.MEAN_REL_AMPLITUDE_ARRAY)) #the Backscatter list as a numpy array
			# fp = geodetic.medfilt(fp,31)
			x = np.linspace(leftExtent, rightExtent, outputResolution) #the required samples needs to be about the same as the original number of samples, spread across the across track range
			newBackscatters = np.interp(x, xp, fp, left=0.0, right=0.0)

			# run a median filter to remove crazy noise
			# newBackscatters = geodetic.medfilt(newBackscatters,3)
			waterfall.append(np.asarray(newBackscatters))			

			recCount += 1
			if datagram.currentRecordDateTime().timestamp() % 30 == 0:
				percentageRead = (recCount / totalrecords) 
				update_progress("Decoding .gsf file", percentageRead)
	update_progress("Decoding .gsf file", 1)
	r.close()	

	# we have all data loaded, so now lets make a waterfall image...
	#---------------------------------------------------------------	
	print ("Correcting for vessel speed...")
	# we now need to interpolate in the along track direction so we have apprximate isometry
	npGrid = np.array(waterfall)

	stretchedGrid = np.empty((0, int(len(npGrid) * isoStretchFactor)))	
	for column in npGrid.T:
		y = np.linspace(0, len(column), len(column) * isoStretchFactor) #the required samples
		yp = np.arange(len(column)) 
		w2 = np.interp(y, yp, column, left=0.0, right=0.0)
		# w2 = geodetic.medfilt(w2,7)
		
		stretchedGrid = np.append(stretchedGrid, [w2],axis=0)
	npGrid = stretchedGrid
	# npGrid = np.ma.masked_values(npGrid, 0.0)
	
	if colorScale.lower() == "graylog": 
		print ("Converting to Image with graylog scale...")
		img = samplesToGrayImageLogarithmic(npGrid, invert, clip)
	elif colorScale.lower() == "gray":
		print ("Converting to Image with gray scale...")
		img = samplesToGrayImage(npGrid, invert, clip)

	if annotate:
		#rotate the image if the user requests this.  It is a little better for viewing in a browser
		annotateWaterfall(img, navigation, isoStretchFactor)
		meanBackscatter = np.average(waterfall)
		waterfallPixelSize = (abs(rightExtent) + abs(rightExtent)) /  img.width
		# print ("Mean Backscatter %.2f" % meanBackscatter)
		imgLegend = createLegend(filename, img.width, (abs(leftExtent)+abs(rightExtent)), distanceTravelled, waterfallPixelSize, minBS, maxBS, meanBackscatter, colorMap)
		img = spliceImages(img, imgLegend)

	if rotate:
		img = img.rotate(-90, expand=True)
	img.save(os.path.splitext(filename)[0]+'.png')
	print ("Saved to: ", os.path.splitext(filename)[0]+'.png')

##################################################################################################################
def findMinMaxClipValues(channel, clip):
	print ("Clipping data with an upper and lower percentage of:", clip)
	# compute a histogram of teh data so we can auto clip the outliers
	bins = np.arange(np.floor(channel.min()),np.ceil(channel.max()))
	hist, base = np.histogram(channel, bins=bins, density=1)	

	# instead of spreading across the entire data range, we can clip the outer n percent by using the cumsum.
	# from the cumsum of histogram density, we can figure out what cut off sample amplitude removes n % of data
	cumsum = np.cumsum(hist)   
	
	minimumBinIndex = bisect.bisect(cumsum,clip/100)
	maximumBinIndex = bisect.bisect(cumsum,(1-clip/100))

	# if DEBUG:
	#	 min = np.floor(channel.min())
	#	 max = np.ceil (channel.max())
	#	 # bins = np.arange(min, max, (max-min)/10)
	#	 # XBins = np.arange(10)
	#	 hist, bins = np.histogram(channel.flat, bins = 100)
	#	 width = 0.7 * (bins[1] - bins[0])
	#	 center = (bins[:-1] + bins[1:]) / 2
	#	 plt.bar(center, hist, align='center', width=width)
	#	 # plt.xlim(int(bin_edges.min()), int(bin_edges.max()))
	#	 plt.show()

		# mu, sigma = 100, 15
		# x = mu + sigma * np.random.randn(10000)
		# hist, bins = np.histogram(x, bins=50)
		# width = 0.7 * (bins[1] - bins[0])
		# center = (bins[:-1] + bins[1:]) / 2
		# plt.bar(center, hist, align='center', width=width)
		# plt.show()

		# width = 0.7 * (bins[1] - bins[0])
		# center = (bins[:-1] + bins[1:]) / 2
		# plt.bar(center, hist, align='center', width=width)
		# plt.show()

	return minimumBinIndex, maximumBinIndex

###################################
# zg_LL = lower limit of grey scale
# zg_UL = upper limit of grey scale
# zs_LL = lower limit of samples range
# zs_UL = upper limit of sample range

###################################
# zg_LL = lower limit of grey scale
# zg_UL = upper limit of grey scale
# zs_LL = lower limit of samples range
# zs_UL = upper limit of sample range
def samplesToGrayImage(samples, invert, clip):
	zg_LL = 5 # min and max grey scales
	zg_UL = 250
	zs_LL = 0 
	zs_UL = 0
	conv_01_99 = 1
	
	#create numpy arrays so we can compute stats
	channel = np.array(samples)   

	# compute the clips
	if clip > 0:
		zs_LL, zs_UL = findMinMaxClipValues(channel, clip)
	else:
		zs_LL = channel.min()
		zs_UL = channel.max()
	
	# this scales from the range of image values to the range of output grey levels
	if (zs_UL - zs_LL) is not 0:
		conv_01_99 = ( zg_UL - zg_LL ) / ( zs_UL - zs_LL )
   
	#we can expect some divide by zero errors, so suppress 
	np.seterr(divide='ignore')
	# channel = np.log(samples)
	channel = np.subtract(channel, zs_LL)
	channel = np.multiply(channel, conv_01_99)
	if invert:
		channel = np.subtract(zg_UL, channel)
	else:
		channel = np.add(zg_LL, channel)
	image = Image.fromarray(channel).convert('L')
	return image

###################################
# zg_LL = lower limit of grey scale
# zg_UL = upper limit of grey scale
# zs_LL = lower limit of samples range
# zs_UL = upper limit of sample range
def samplesToGrayImageLogarithmic(samples, invert, clip):
	zg_LL = 0 # min and max grey scales
	zg_UL = 255
	zs_LL = 0 
	zs_UL = 0
	conv_01_99 = 1
	# channelMin = 0
	# channelMax = 0
	#create numpy arrays so we can compute stats
	channel = np.array(samples)   

	# compute the clips
	if clip > 0:
		channelMin, channelMax = findMinMaxClipValues(channel, clip)
	else:
		channelMin = channel.min()
		channelMax = channel.max()
	
	if channelMin > 0:
		zs_LL = math.log(channelMin)
	else:
		zs_LL = 0
	if channelMax > 0:
		zs_UL = math.log(channelMax)
	else:
		zs_UL = 0
	
	# this scales from the range of image values to the range of output grey levels
	if (zs_UL - zs_LL) is not 0:
		conv_01_99 = ( zg_UL - zg_LL ) / ( zs_UL - zs_LL )
   
	#we can expect some divide by zero errors, so suppress 
	np.seterr(divide='ignore')
	channel = np.log(samples)
	channel = np.subtract(channel, zs_LL)
	channel = np.multiply(channel, conv_01_99)
	if invert:
		channel = np.subtract(zg_UL, channel)
	else:
		channel = np.add(zg_LL, channel)
	# ch = channel.astype('uint8')
	image = Image.fromarray(channel).convert('L')
	
	return image

def computeXYResolution(fileName):	
	'''compute the approximate across and alongtrack resolution so we can make a nearly isometric Image'''
	'''we compute the across track by taking the average Dx value between beams'''
	'''we compute the alongtracks by computing the linear length between all nav updates and dividing this by the number of pings'''
	xResolution = 1
	YResolution = 1
	prevLong = 0 
	prevLat = 0
	recCount = 0
	acrossMeans = np.array([])
	alongIntervals = np.array([])
	leftExtents = np.array([])
	rightExtents = np.array([])
	beamCount = 0
	distanceTravelled = 0.0
	navigation = []
	selectedPositioningSystem = None

	# open the gsf file and read the scale factors
	r = pygsf.GSFREADER(fileName)
	scalefactors = r.loadscalefactors()

	while r.moreData():
		numberofbytes, recordidentifier, datagram = r.readDatagram()
		if recordidentifier == 2: #SWATH_BATHYMETRY_PING
			datagram.scalefactors = scalefactors	
			datagram.read()
			if prevLat == 0:
				prevLat =  datagram.latitude
				prevLong =  datagram.longitude
			range,bearing1, bearing2  = geodetic.calculateRangeBearingFromGeographicals(prevLong, prevLat, datagram.longitude, datagram.latitude)
			# print (range,bearing1)
			distanceTravelled += range
			navigation.append([recCount, datagram.currentRecordDateTime(), datagram.latitude, datagram.longitude])
			prevLat =  datagram.latitude
			prevLong =  datagram.longitude
			if datagram.numbeams > 1:
				datagram.ACROSS_TRACK_ARRAY = [x for x in datagram.ACROSS_TRACK_ARRAY if x != 0.0]
				if (len(datagram.ACROSS_TRACK_ARRAY) > 0):
					acrossMeans = np.append(acrossMeans, np.average(abs(np.diff(np.asarray(datagram.ACROSS_TRACK_ARRAY)))))
					leftExtents = np.append(leftExtents, min(datagram.ACROSS_TRACK_ARRAY))
					rightExtents = np.append(rightExtents, max(datagram.ACROSS_TRACK_ARRAY))
					recCount = recCount + 1
					beamCount = max(beamCount, len(datagram.MEAN_REL_AMPLITUDE_ARRAY)) 
			
	r.close()
	if recCount == 0:
		return 0,0,0,0,0,[] 
	xResolution = np.average(acrossMeans)
	# distanceTravelled = 235
	yResolution = distanceTravelled / recCount
	return xResolution, yResolution, beamCount, np.min(leftExtents), np.max(rightExtents), distanceTravelled, navigation

def annotateWaterfall(img, navigation, scaleFactor):
	'''loop through the navigation and annotate'''
	lastTime = 0.0 
	lastRecord = 0
	for record, date, lat, long in navigation:
		# if (record % 100 == 0) and (record != lastRecord):
		if (record - lastRecord >= 100):
			writeLabel(img, int(record * scaleFactor), str(date.strftime("%H:%M:%S")))
			lastRecord = record
	return img

def writeLabel(img, y, label):
	x = 0
	f = ImageFont.truetype("arial.ttf",size=16)
	txt=Image.new('RGBA', (500,16))
	d = ImageDraw.Draw(txt)
	d.text( (0, 0), label,  font=f, fill=(0,0,0))
	# d.text( (0, 0), label,  font=f, fill=(255,255,255))
	d.line((0, 0, 20, 0), fill=(0,0,255))
	# w=txt.rotate(-90,  expand=1)
	offset = (x, y)
	img.paste(txt, offset, txt)
	# img.paste( ImageOps.colorize(txt, (0,0,0), (0,0,255)), (x, y),  txt)
	return img

def update_progress(job_title, progress):
	length = 20 # modify this to change the length
	block = int(round(length*progress))
	msg = "\r{0}: [{1}] {2}%".format(job_title, "#"*block + "-"*(length-block), round(progress*100, 2))
	if progress >= 1: msg += " DONE\r\n"
	sys.stdout.write(msg)
	sys.stdout.flush()

def spliceImages(img1, img2):
	# images = map(Image.open, ['Test1.jpg', 'Test2.jpg', 'Test3.jpg'])
	images = [img1, img2]
	widths, heights = zip(*(i.size for i in images))

	width = max(widths)
	height = sum(heights)

	new_im = Image.new('RGB', (width, height))

	y_offset = 0
	for im in images:
		new_im.paste(im, (0, y_offset))
		y_offset += im.size[1]
	return new_im

def createLegend(fileName, imageWidth=640, waterfallWidth=640, waterfallLength=640, waterfallPixelSize=1, minBackscatter=0, maxBackscatter=999, meanBackscatter=99, colorMap=None):
	'''make a legend specific for this waterfalls image'''
	# this legend will contain:
	# InputFileName: <filename>
	# Waterfall Width: xxx.xxm
	# Waterfall Length: xxx.xxxm
	# Waterfall Pixel Size: xx.xxm
	# Mean Backscatter: xx.xxm
	# Color Palette as a graphical representation

	x = 0
	y=0
	fontHeight = 18
	npGrid = np.array([])

	f = ImageFont.truetype("cour.ttf",size=fontHeight)
	img=Image.new('RGB', (imageWidth,256)) # the new image.  this needs to be the same width as the main waterfall image
	
	d = ImageDraw.Draw(img)

	label = "file:%s" % (fileName)
	white=(255,255,255)
	d.text( (x, y), label,  font=f, fill=white)

	y += fontHeight
	label = "Waterfall Width	: %.2fm" % (waterfallWidth)
	d.text( (x, y), label,  font=f, fill=white)

	y += fontHeight
	label = "Waterfall Length   : %.2fm" % (waterfallLength)
	d.text( (x, y), label,  font=f, fill=white)

	y += fontHeight
	label = "Pixel Size		 : %.2fm" % (waterfallPixelSize)
	d.text( (x, y), label,  font=f, fill=white)

	y += fontHeight
	label = "Minimum Backscatter	  : %.2fm" % (minBackscatter)
	d.text( (x, y), label,  font=f, fill=white)

	y += fontHeight
	label = "Maximum Backscatter	  : %.2fm" % (maxBackscatter)
	d.text( (x, y), label,  font=f, fill=white)

	y += fontHeight
	label = "Mean Backscatter		 : %.2fm" % (meanBackscatter)
	d.text( (x, y), label,  font=f, fill=white)

	if (colorMap==None):
		return img
	# Creates a list containing 5 lists, each of 8 items, all set to 0
	y += fontHeight
	npline = np.linspace(start=minBackscatter, stop=maxBackscatter, num=imageWidth - ( fontHeight)) # length of colorbar is almost same as image
	npGrid = np.hstack((npGrid, npline))
	for i in range(fontHeight*2): # height of colorbar
		npGrid = np.vstack((npGrid, npline))
	colorArray = colorMap.to_rgba(npGrid, alpha=None, bytes=True)	
	colorImage = Image.frombuffer('RGB', (colorArray.shape[1], colorArray.shape[0]), colorArray, 'raw', 'RGBA', 0,1)
	offset = x + int (fontHeight/2), y
	img.paste(colorImage,offset)

	# now make the Backscatter labels alongside the colorbar
	y += 2 + fontHeight * 2
	labels = np.linspace(minBackscatter, maxBackscatter, 10)
	for l in labels:
		label= "%.2f" % (l)
		x = (l-minBackscatter) * ((imageWidth - fontHeight) / (maxBackscatter-minBackscatter))
		offset = int(x), int(y)
		txt=Image.new('RGB', (70,20))
		d = ImageDraw.Draw(txt)
		d.text( (0, 0), label,  font=f, fill=white)
		w=txt.rotate(90,  expand=1)
		img.paste( w, offset)
	return img

if __name__ == "__main__":
	main()

