#name:			pygsf
#created:		July 2017
#by:			p.kennedy@fugro.com
#description:	python module to read and write a Generic Sensor Formaty (GSF) file natively
#notes:			See main at end of script for example how to use this
#based on GSF Version 3.05

# See readme.md for more details

import sys
from glob import glob
import argparse
import os.path
import struct
import pprint
import time
import datetime
import math
import random
from datetime import datetime
from datetime import timedelta
from statistics import mean
import mmap

# for testing only...
# import matplotlib.pyplot as plt
import numpy as np

#/* The high order 4 bits are used to define the field size for this array */
GSF_FIELD_SIZE_DEFAULT  = 0x00  #/* Default values for field size are used used for all beam arrays */
GSF_FIELD_SIZE_ONE	  = 0x10  #/* value saved as a one byte value after applying scale and offset */
GSF_FIELD_SIZE_TWO	  = 0x20  #/* value saved as a two byte value after applying scale and offset */
GSF_FIELD_SIZE_FOUR	 = 0x40  #/* value saved as a four byte value after applying scale and offset */
GSF_MAX_PING_ARRAY_SUBRECORDS = 26

# Record Decriptions (See page 82)
HEADER 									= 1
SWATH_BATHYMETRY						= 2
SOUND_VELOCITY_PROFILE					= 3
PROCESSING_PARAMETERS					= 4
SENSOR_PARAMETERS						= 5
COMMENT									= 6
HISTORY									= 7
NAVIGATION_ERROR						= 8
SWATH_BATHY_SUMMARY						= 9
SINGLE_BEAM_SOUNDING					= 10
HV_NAVIGATION_ERROR						= 11
ATTITUDE								= 12

SNIPPET_NONE 							= 0  # extract the mean value from the snippet array
SNIPPET_MEAN 							= 1  # extract the mean value from the snippet array
SNIPPET_MAX 							= 2  # extract the maximum value from the snippet array
SNIPPET_DETECT 							= 3	 # extract the bottom detect snippet value from the snippet array
SNIPPET_MEAN5DB 						= 4  # extract the mean of all snippets within 5dB of the mean

# the various frequencies we support in the R2Sonic multispectral files
ARCIdx = {100000: 0, 200000: 1, 400000: 2}

# the rejection flags used by this software
REJECT_CLIP = -1
REJECT_RANGE= -2
REJECT_INTENSITY= -4
###############################################################################
def main():

	parser = argparse.ArgumentParser(description='Read GSF file and create a reflectivity image.')
	parser.add_argument('-i', dest='inputFile', action='store', help='Input ALL filename to image. It can also be a wildcard, e.g. *.gsf')

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

	# testR2SonicAdjustment()
	testreader(filename)
	# conditioner()

###############################################################################
def testreader(filename):
	'''
	sample read script so we can see how to use the code
	'''
	start_time = time.time() # time the process so we can keep it quick

	# filename = "C:/projects/multispectral/PatriciaBasin/20161130-1907 - 0001-2026_1.gsf"

	# filename = "C:/development/python/sample_subset.gsf"
	# filename = "F:/Projects/multispectral/_BedfordBasin2016/20160331 - 125110 - 0001-2026_1.gsf"
	# filename = "F:/Projects/multispectral/_Newbex/20170524-134208 - 0001-2026_1.gsf"
	# filename = "F:/Projects/multispectral/_BedfordBasin2017/20170502 - 131750 - 0001-2026_1.gsf"
	# filename = "C:/projects/multispectral/_BedfordBasin2017/20170502 - 150058 - 0001-2026_1.gsf"


	print (filename)
	pingcount = 0
	# create a GSFREADER class and pass the filename
	r = GSFREADER(filename)
	# r.loadnavigation()


	# f1 = plt.figure()
	# # f2 = plt.figure()
	# # f3 = plt.figure()

	# ax1 = f1.add_subplot(111)
	# # ax2 = f2.add_subplot(111)
	# # ax3 = f3.add_subplot(111)

	print ("pingcount, pingnumber, 100kHz, 200kHz, 400kHz")
	while r.moreData():
		# read a datagram.  If we support it, return the datagram type and aclass for that datagram
		# The user then needs to call the read() method for the class to undertake a fileread and binary decode.  This keeps the read super quick.
		numberofbytes, recordidentifier, datagram = r.readDatagram()
		# print(datagram)
		if recordidentifier == SWATH_BATHYMETRY:
			print(recordidentifier, end=',')
			datagram.read()
			datagram.snippettype = SNIPPET_NONE
			# print ("%s Lat:%.3f Lon:%.3f Ping:%d Freq:%d Serial %s" % (datagram.currentRecordDateTime(), datagram.latitude, datagram.longitude, datagram.pingnumber, datagram.frequency, datagram.serialnumber))

			# for cross profile plotting
			# bs = []
			# for s in datagram.MEAN_REL_AMPLITUDE_ARRAY:
			# 	if s != 0:
			# 		bs.append(20 * math.log10(s) - 100)
			# 	else:
			# 		bs.append(0)

			# bs = [20 * math.log10(s) - 100 for s in datagram.MEAN_REL_AMPLITUDE_ARRAY]
			samplearray = datagram.R2Soniccorrection()
			if datagram.frequency == 100000:
				freq100 = mean(samplearray)
			if datagram.frequency == 200000:
				freq200 = mean(samplearray)
			if datagram.frequency == 400000:
				freq400 = mean(samplearray)
				# print ("%d,%d,%.3f,%.3f,%.3f" %(pingcount, datagram.pingnumber, freq100, freq200, freq400))
				# print ("%d" %(pingcount))
				pingcount += 1
				# if len(bs) > 0:
				# 	plt.plot(datagram.BEAM_ANGLE_ARRAY, bs, linewidth=0.25, color='blue')
				# 	plt.ylim([-60,-5])
				# 	plt.xlim([-60,60])
				# 	# ax3.plot(datagram.BEAM_ANGLE_ARRAY, datagram.ALONG_TRACK_ARRAY)
				# 	plt.pause(0.001)

			# datagram.clippolar(-60, 60)
	# print("Duration %.3fs" % (time.time() - start_time )) # time the process
	# print ("PingCount:", pingcount)
	return

###############################################################################
class UNKNOWN_RECORD:
	'''used as a convenience tool for datagrams we have no bespoke classes.  Better to make a bespoke class'''
	def __init__(self, fileptr, numbytes, recordidentifier, hdrlen):
		self.recordidentifier = recordidentifier
		self.offset = fileptr.tell()
		self.hdrlen = hdrlen
		self.numbytes = numbytes
		self.fileptr = fileptr
		self.fileptr.seek(numbytes, 1) # set the file ptr to the end of the record
		self.data = ""
		self.name = "unknown"

	def read(self):
		self.data = self.fileptr.read(self.numberofbytes)

	def __str__(self):
		'''
		pretty print this class
		'''
		return pprint.pformat(vars(self))

class SCALEFACTOR:
	def __init__(self):
		self.subrecordID = 0	
		self.compressionFlag = 0	#/* Specifies bytes of storage in high order nibble and type of compression in low order nibble */
		self.multiplier = 0.0
		self.offset = 0
		self.name = "scaleFactor"
	def __str__(self):
		'''
		pretty print this class
		'''
		return pprint.pformat(vars(self))
	
class SWATH_BATHYMETRY_PING :
	def __init__(self, fileptr, numbytes, recordidentifier, hdrlen):
		self.recordidentifier = recordidentifier	# assign the GSF code for this datagram type
		self.offset = fileptr.tell()				# remember where this packet resides in the file so we can return if needed
		self.hdrlen = hdrlen						# remember the header length.  it should be 8 bytes, bout if checksum then it is 12
		self.numbytes = numbytes					# remember how many bytes this packet contains
		self.fileptr = fileptr						# remember the file pointer so we do not need to pass from the host process
		self.fileptr.seek(numbytes, 1)				# move the file pointer to the end of the record so we can skip as the default actions
		self.scalefactors = []
		self.DEPTH_ARRAY = []
		self.ACROSS_TRACK_ARRAY = []
		self.ALONG_TRACK_ARRAY = []
		self.TRAVEL_TIME_ARRAY = []
		self.BEAM_ANGLE_ARRAY = []
		self.MEAN_CAL_AMPLITUDE_ARRAY = []
		self.MEAN_REL_AMPLITUDE_ARRAY = []
		self.QUALITY_FACTOR_ARRAY = []
		self.BEAM_FLAGS_ARRAY = []
		self.BEAM_ANGLE_FORWARD_ARRAY = []
		self.VERTICAL_ERROR_ARRAY = []
		self.HORIZONTAL_ERROR_ARRAY = []
		self.SECTOR_NUMBER_ARRAY = []
		# self.INTENSITY_SERIES_ARRAY = []
		self.SNIPPET_SERIES_ARRAY = []
		self.perbeam = True
		self.snippettype = SNIPPET_MAX
		self.numbeams = 0
		self.time = 0
		self.pingnanotime = 0
		self.name = "swath bathy ping"

###############################################################################
	def __str__(self):
		'''
		pretty print this class
		'''
		return pprint.pformat(vars(self))
###############################################################################
	def clippolar(self, leftclipdegrees, rightclipdegrees):
		'''sets the processing flags to rejected if the beam angle is beyond the clip parameters'''
		if self.numbeams == 0:
			return
		if len(self.QUALITY_FACTOR_ARRAY) != len(self.TRAVEL_TIME_ARRAY):
			return
		for i, s in enumerate(self.BEAM_ANGLE_ARRAY):
			if (s <= leftclipdegrees) or (s >= rightclipdegrees):
				self.QUALITY_FACTOR_ARRAY[i] += REJECT_CLIP
				# self.MEAN_REL_AMPLITUDE_ARRAY[i] = 0
				# self.ACROSS_TRACK_ARRAY[i] = 0
		return
###############################################################################
	def cliptwtt(self, minimumtraveltime=0.0):
		'''sets the processing flags to rejected if the two way travel time is less than the clip parameters'''
		if self.numbeams == 0:
			return
		if len(self.QUALITY_FACTOR_ARRAY) != len(self.TRAVEL_TIME_ARRAY):
			return
		for i, s in enumerate(self.TRAVEL_TIME_ARRAY):
			if (s <= minimumtraveltime):
				self.QUALITY_FACTOR_ARRAY[i] += REJECT_RANGE
		return

###############################################################################
	def clipintensity(self, minimumintenisty=0.0):
		'''sets the processing flags to rejected if the two way travel time is less than the clip parameters'''
		if self.numbeams == 0:
			return
		if len(self.QUALITY_FACTOR_ARRAY) != len(self.TRAVEL_TIME_ARRAY):
			return
		for i, s in enumerate(self.MEAN_REL_AMPLITUDE_ARRAY):
			if (s <= minimumintenisty):
				self.QUALITY_FACTOR_ARRAY[i] += REJECT_INTENSITY
		return

###############################################################################
	def read(self, headeronly=False):
		self.fileptr.seek(self.offset + self.hdrlen, 0)   # move the file pointer to the start of the record so we can read from disc			  

		# read ping header
		hdrfmt = '>llll5hlH3h2Hlllh'
		hdrlen = struct.calcsize(hdrfmt)
		rec_unpack = struct.Struct(hdrfmt).unpack

		self.fileptr.seek(self.offset + self.hdrlen , 0)   # move the file pointer to the start of the record so we can read from disc			  
		data = self.fileptr.read(hdrlen)
		s = rec_unpack(data)
		self.time 			= s[0] 
		self.longitude 		= s[2] / 10000000
		self.latitude		= s[3] / 10000000
		self.numbeams 		= s[4]
		self.centrebeam 	= s[5]
		self.pingflags 		= s[6]
		self.reserved 		= s[7]
		self.tidecorrector	= s[8] / 100
		self.depthcorrector	= s[9] / 100
		self.heading		= s[10] / 100
		self.pitch			= s[11] / 100
		self.roll			= s[12] / 100
		self.heave			= s[13] / 100
		self.course			= s[14] / 100
		self.speed			= s[15] / 100
		self.height			= s[16] / 100
		self.separation		= s[17] / 100
		self.gpstidecorrector	= s[18] / 100
		self.spare			= s[19]

		while (self.fileptr.tell() < self.offset + self.numbytes): #dont read past the end of the packet length.  This should never happen!
			fmt = '>l'
			fmtlen = struct.calcsize(fmt)
			rec_unpack = struct.Struct(fmt).unpack
			data = self.fileptr.read(fmtlen)   # read the record from disc
			s = rec_unpack(data)

			subrecord_id = (s[0] & 0xFF000000) >> 24
			subrecord_size = s[0] & 0x00FFFFFF

			# skip the record for performance reasons.  Very handy in some circumstances
			if headeronly:
				if subrecord_id == 21: 
					self.fileptr.seek(self.offset + self.numbytes, 0) #move forwards to the end of the record as we cannot trust the record length from the 2024
				else:
					self.fileptr.seek(subrecord_size, 1) #move forwards to the end of teh record
				continue

			# now decode the subrecord
			# curr = self.fileptr.tell()
			scale, offset, compressionFlag, datatype = self.getscalefactor(subrecord_id, subrecord_size / int(self.numbeams))
			
			if subrecord_id == 100: 
				self.readscalefactors()
			elif subrecord_id == 1: 
				self.readarray(self.DEPTH_ARRAY, scale, offset, datatype)
			elif subrecord_id == 2: 
				self.readarray(self.ACROSS_TRACK_ARRAY, scale, offset, datatype)
			elif subrecord_id == 3: 
				self.readarray(self.ALONG_TRACK_ARRAY, scale, offset, datatype)
			elif subrecord_id == 4: 
				self.readarray(self.TRAVEL_TIME_ARRAY, scale, offset, datatype)
			elif subrecord_id == 5: 
				self.readarray(self.BEAM_ANGLE_ARRAY, scale, offset, datatype)
			elif subrecord_id == 6: 
				self.readarray(self.MEAN_CAL_AMPLITUDE_ARRAY, scale, offset, datatype)
			elif subrecord_id == 7: 
				self.readarray(self.MEAN_REL_AMPLITUDE_ARRAY, scale, offset, datatype)
			elif subrecord_id == 9: 
				self.readarray(self.QUALITY_FACTOR_ARRAY, scale, offset, datatype)
			elif subrecord_id == 16: 
				self.readarray(self.BEAM_FLAGS_ARRAY, scale, offset, datatype)
			elif subrecord_id == 18: 
				self.readarray(self.BEAM_ANGLE_FORWARD_ARRAY, scale, offset, datatype)
			elif subrecord_id == 19: 
				self.readarray(self.VERTICAL_ERROR_ARRAY, scale, offset, datatype)
			elif subrecord_id == 20: 
				self.readarray(self.VERTICAL_ERROR_ARRAY, scale, offset, datatype)
			elif subrecord_id == 21: 
				before = self.fileptr.tell()
				self.readintensityarray(self.SNIPPET_SERIES_ARRAY, scale, offset, datatype, self.snippettype)
				if subrecord_size % 4 > 0:
					self.fileptr.seek(4 - (subrecord_size % 4), 1) #pkpk we should not need this!!!
			elif subrecord_id == 22: 
				self.readarray(self.SECTOR_NUMBER_ARRAY, scale, offset, datatype)
			else:
				# read to the end of the record to keep in alignment.  This permits us to not have all the decodes in place
				self.fileptr.seek(subrecord_size, 1) #move forwards to the end of teh record
		return

	def getscalefactor(self, ID, bytes_per_value):
		for s in self.scalefactors:
			if s.subrecordID == ID:			# DEPTH_ARRAY array
				if bytes_per_value == 1:
					datatype = 'B' 			#unsigned values
				elif bytes_per_value == 2:
					datatype = 'H'			#unsigned values
					if ID == 2:				#ACROSS_TRACK_ARRAY array
						datatype = 'h'		#unsigned values
					if ID == 3:				#ACROSS_TRACK_ARRAY array
						datatype = 'h'		#unsigned values
					if ID == 5:				#beam angle array
						datatype = 'h'		#unsigned values
				elif bytes_per_value == 4:
					datatype = 'L'			#unsigned values
					if ID == 2:				#ACROSS_TRACK_ARRAY array
						datatype = 'l'		#unsigned values
					if ID == 5:				#beam angle array
						datatype = 'l'		#unsigned values
				else:
					datatype = 'L'			#unsigned values not sure about this one.  needs test data
				return s.multiplier, s.offset, s.compressionFlag, datatype
		return 1,0,0, 'h'

	def readscalefactors(self):
		# /* First four byte integer contains the number of scale factors */
		# now read all scale factors
		scalefmt = '>l'
		scalelen = struct.calcsize(scalefmt)
		rec_unpack = struct.Struct(scalefmt).unpack

		data = self.fileptr.read(scalelen)
		s = rec_unpack(data)
		self.numscalefactors = s[0]

		scalefmt = '>lll'
		scalelen = struct.calcsize(scalefmt)
		rec_unpack = struct.Struct(scalefmt).unpack

		for i in range(self.numscalefactors):
			data = self.fileptr.read(scalelen)
			s = rec_unpack(data)
			sf = SCALEFACTOR()
			sf.subrecordID = (s[0] & 0xFF000000) >> 24;
			sf.compressionFlag = (s[0] & 0x00FF0000) >> 16;
			sf.multiplier = s[1]
			sf.offset = s[2]
			self.scalefactors.append(sf)
		# print (self.scalefactors)
		return

	def readintensityarray(self, snippets, scale, offset, datatype, snippettype):
		''' 
		read the time series intensity array type 21 subrecord
		'''
		hdrfmt = '>bl16s'
		hdrlen = struct.calcsize(hdrfmt)
		rec_unpack = struct.Struct(hdrfmt).unpack
		hdr = self.fileptr.read(hdrlen)
		s = rec_unpack(hdr)
		bitspersample = s[0]
		appliedcorrections = s[1]

		# before we decode the intentisty data, read the sensor specific header
		#for now just read the r2sonic as that is what we need.  For other sensors we need to implement decodes
		self.decodeR2SonicImagerySpecific()
		
		for b in range(self.numbeams):
			hdrfmt = '>hh8s'
			hdrlen = struct.calcsize(hdrfmt)
			rec_unpack = struct.Struct(hdrfmt).unpack
			hdr = self.fileptr.read(hdrlen)
			s = rec_unpack(hdr)
			
			numsamples = s[0]
			bottomdetectsamplenumber = s[1]
			spare = s[2]

			fmt = '>' + str(numsamples) + 'H'
			l = struct.calcsize(fmt)
			rec_unpack = struct.Struct(fmt).unpack
			
			data = self.fileptr.read(l)  
			raw = rec_unpack(data)
			# strip out zero values
			raw = [s for s in raw if s != 0]

			if snippettype == SNIPPET_NONE:
				snippets.append(0)
				continue
			elif snippettype == SNIPPET_MEAN5DB:
				# populate the array with the mean of all samples withing a 5dB range of the mean.  As per QPS
				if len(raw) > 0:
					raw2 = [20.0 * math.log10(s / scale + offset) for s in raw]
					mean = (sum(raw2) / float(len(raw2) ))
					highcut = [s for s in raw2 if s < mean + 5] #high cut +5dB
					highlowcut = [s for s in highcut if s > mean - 5] #low cut -5dB
				else:
					snippets.append(0)
					continue
				if len(highlowcut) > 0:
					snippets.append((sum(highlowcut) / float(len(highlowcut) / scale) + offset))
				else:
					snippets.append((mean / scale) + offset)
			elif snippettype == SNIPPET_MEAN:
				# populate the array with the mean of all samples	 
				if len(raw) > 0:
					snippets.append((sum(raw) / float(len(raw) / scale) + offset))
				else:
					snippets.append(0)
			elif snippettype == SNIPPET_MAX:
				# populate the array with the MAX of all samples	 
				if len(raw) > 0:
					snippets.append(max(raw) / scale + offset)
				else:
					snippets.append(0)
			elif snippettype == SNIPPET_MEAN:
				# populate with a single value as identified by the bottom detect
				if bottomdetectsamplenumber > 0:
					snippets.append ((raw[bottomdetectsamplenumber] / scale) + offset)
				else:
					snippets.append (0)
		return

###############################################################################
	def R2Soniccorrection(self):
		'''entry point for r2sonic backscatter TVG, Gain and footprint correction algorithm'''
		if self.perbeam:
			samplearray = self.MEAN_REL_AMPLITUDE_ARRAY
			return samplearray
		else:
			samplearray = self.SNIPPET_SERIES_ARRAY
			return samplearray
		# an implementation of the backscatter correction algorithm from Norm Campbell at CSIRO
		H0_TxPower = self.transmitsourcelevel
		H0_SoundSpeed = self.soundspeed
		H0_RxAbsorption = self.absorptioncoefficient
		H0_TxBeamWidthVert = self.beamwidthvertical
		H0_TxBeamWidthHoriz = self.beamwidthhorizontal
		H0_TxPulseWidth = self.pulsewidth
		H0_RxSpreading = self.receiverspreadingloss
		H0_RxGain = self.receivergain
		H0_VTX_Offset = self.vtxoffset

		for i in range(self.numbeams):
			if self.BEAM_FLAGS_ARRAY[i] < 0:
				continue
			S1_angle = self.BEAM_ANGLE_ARRAY[i] #angle in degrees
			S1_twtt = self.TRAVEL_TIME_ARRAY[i]
			S1_range = math.sqrt((self.ACROSS_TRACK_ARRAY[i] ** 2) + (self.ALONG_TRACK_ARRAY[i] ** 2))
			if samplearray[i] != 0:
				S1_uPa = samplearray[i]
				# adjusted = 0				
				# a test on request from Norm....
				# adjusted = 20 * math.log10(S1_uPa) - 100
				# the formal adjustment from Norm Campbell...
				# if i == 127:
				adjusted = self.backscatteradjustment( S1_angle, S1_twtt, S1_range, S1_uPa, H0_TxPower, H0_SoundSpeed, H0_RxAbsorption, H0_TxBeamWidthVert, H0_TxBeamWidthHoriz, H0_TxPulseWidth, H0_RxSpreading, H0_RxGain, H0_VTX_Offset)
				
				samplearray[i] = adjusted
		return samplearray

###############################################################################
	def backscatteradjustment(self, S1_angle, S1_twtt, S1_range, S1_Magnitude, H0_TxPower, H0_SoundSpeed, H0_RxAbsorption, H0_TxBeamWidthVert, H0_TxBeamWidthHoriz, H0_TxPulseWidth, H0_RxSpreading, H0_RxGain, H0_VTX_Offset):
		'''R2Sonic backscatter correction algorithm from Norm Camblell at CSIRO.  This is a port from F77 fortran code, and has been tested and confirmed to provide identical results'''
		# the following code uses the names for the various packets as listed in the R2Sonic SONIC 2024 Operation Manual v6.0
		# so names beginning with
		# H0_   denote parameters from the BATHY (BTH) and Snippet (SNI) packets from section H0
		# R0_   denote parameters from the BATHY (BTH) packets from section R0
		# S1_   denote parameters from the Snippet (SNI) packets from section S1
		# names beginning with
		# z_	denote values derived from the packet parameters
		# the range, z_range_m, can be found from the two-way travel time (and scaling factor), and the sound speed, as follows:

		one_rad = 57.29577951308232
		S1_angle_rad = S1_angle / one_rad
		z_one_way_travel_secs = S1_twtt / 2.0
		z_range_m = z_one_way_travel_secs * H0_SoundSpeed

		# there is a range of zero, so this is an invalid beam, so quit
		if z_range_m == 0:
			return 0

		###### TRANSMISSION LOSS CORRECTION ##########################################
		# according to Lurton, Augustin and Le Bouffant (Femme 2011), the basic Sonar equation is
		# received_level = source_level - 2 * transmission_loss + target_strength + receiver_gain
		# note that this last term does not always appear explicitly in the sonar equation
		# more specifically:
		# transmission_loss = H0_RxAbsorption * range_m + 40 log10 ( range_m )
		# target_strength = backscatter_dB_m + 10 log10 ( z_area_of_insonification )
		# receiver_gain = TVG + H0_RxGain
		# the components of the Sonar equation can be calculated as follows:
		# u16 S1_Magnitude[S1_Samples]; // [micropascals] = S1_Magnitude[n]

		z_received_level = 20.0 * math.log10 ( S1_Magnitude )
		z_source_level = H0_TxPower # [dB re 1 uPa at 1 meter]
		z_transmission_loss_t1 = 2.0 * H0_RxAbsorption * z_range_m / 1000.0  # [dB per kilometer]
		z_transmission_loss_t2 = 40.0 * math.log10(z_range_m)
		z_transmission_loss = z_transmission_loss_t1 + z_transmission_loss_t2
	
		###### INSONIFICATION AREA CORRECTION Checked 19 August 2017 p.kennedy@fugr.com ##########################################	
		# for oblique angles
			# area_of_insonification = along_track_beam_width * range * sound_speed * pulse_width / 2 sin ( incidence_angle)
		# for normal incidence
			# area_of_insonification = along_track_beam_width * across_track_beam_width * range ** 2

		sin_S1_angle = math.sin ( abs ( S1_angle_rad ) )

		# from Hammerstad 00 EM Technical Note Backscattering and Seabed Image Reflectivity.pdf
		# A = ψTψr*R^2 around normal incidence
		z_area_of_insonification_nml = H0_TxBeamWidthVert * H0_TxBeamWidthHoriz * z_range_m **2 

		# A = ½cτ ψTR/sinφ elsewhere
		if ( abs ( S1_angle ) >= 0.001 ):
			z_area_of_insonification_obl = 0.5 * H0_SoundSpeed * H0_TxPulseWidth * H0_TxBeamWidthVert * z_range_m / sin_S1_angle

		if ( abs ( S1_angle ) < 25. ):
			z_area_of_insonification = z_area_of_insonification_nml
		else:
			z_area_of_insonification = z_area_of_insonification_obl

		if ( abs ( S1_angle ) < 0.001 ):
			z_area_of_insonification = z_area_of_insonification_nml
		elif ( z_area_of_insonification_nml < z_area_of_insonification_obl ):
			z_area_of_insonification = z_area_of_insonification_nml
		else:
			z_area_of_insonification = z_area_of_insonification_obl

		###### TIME VARIED GAIN CORRECTION  19 August 2017 p.kennedy@fugr.com ##########################################
		# note that the first equation refers to the along-track beam width
		# the R2Sonic Operation Manual refers on p21 to the Beamwidth - Along Track -- moreover, for the 2024, the Beamwidth Along Track is twice
		# the Beamwidth Across Track

		# according to the R2Sonic Operation Manual in Section 5.6.3 on p88, the TVG equation is:
		# TVG = 2*R* α/1000 + Sp*log(R) + G
		# where:
		# α = Absorption Loss db/km			(H0_RxAbsorption)
		# R = Range in metres				(range_m)
		# Sp = Spreading loss coefficient	(H0_RxSpreading)
		# G = Gain from Sonar Control setting (H0_RxGain)

		TVG_1 = 2.0 * z_range_m * H0_RxAbsorption / 1000.
		TVG_2 = H0_RxSpreading * math.log10 ( z_range_m )		
		TVG = TVG_1 + TVG_2 + H0_RxGain

		# as per email from Beaudoin, clip the TVG between 4 and 83 dB
		TVG = min(max(4, TVG ), 83)

		###### NOW COMPUTE THE CORRECTED BACKSCATTER ##########################################
		backscatter_dB_m = z_received_level - z_source_level + z_transmission_loss - (10.0 * math.log10 ( z_area_of_insonification )) - TVG - H0_VTX_Offset + 100.0

		return backscatter_dB_m

###############################################################################
	def decodeR2SonicImagerySpecific(self):
		''' 
		read the imagery information for the r2sonic 2024
		'''
		fmt = '>12s12slll lllll llllhh lllll lllhh lllll l32s'
		l = struct.calcsize(fmt)
		rec_unpack = struct.Struct(fmt).unpack
		data = self.fileptr.read(l) 
		raw = rec_unpack(data)
		
		self.modelnumber = raw[0]
		self.serialnumber = raw[1].decode('utf-8').rstrip('\x00')

		self.pingtime = raw[2]
		self.pingnanotime = raw[3]
		self.pingnumber = raw[4]
		self.pingperiod = raw[5] / 1.0e6
		self.soundspeed = raw[6] / 1.0e2

		self.frequency = raw[7] / 1.0e3
		self.transmitsourcelevel = raw[8] / 1.0e2
		self.pulsewidth = raw[9] / 1.0e7

		self.beamwidthvertical = math.radians(raw[10] / 1.0e6)
		self.beamwidthhorizontal = math.radians(raw[11] / 1.0e6)
		
		#apply scaling as per email from Beaudoin https://jira.qps.nl/browse/SFM-2857
		self.beamwidthvertical = math.radians(raw[10] / 1.0e6 * (400000 / self.frequency))
		self.beamwidthhorizontal = math.radians(raw[11] / 1.0e6 * (400000 / self.frequency))
	
		transmitsteeringvertical = raw[12] / 1.0e6
		transmitsteeringhorizontal = raw[13] / 1.0e6
		transmitinfo = raw[14]
		self.vtxoffset = raw[15]  / 100
		receiverbandwidth = raw[16] / 1.0e4
		receiversamplerate = raw[17] / 1.0e3
		
		receiverrange = raw[18] / 1.0e5
		# The GSF file preserves R2Sonic's native scaling of their gain parameter at 0.5 dB resolution, so you need to take the gain and multiply by 2.
		self.receivergain = raw[19] / 1.0e2 * 2.0
		self.receiverspreadingloss = raw[20] / 1.0e3
		self.absorptioncoefficient = raw[21]/ 1.0e3 #dB/kilometre
		mounttiltangle = raw[22] / 1.0e6

		# print ("ping %d Date %s freq %d absorption %.3f" % (self.pingnumber, self.currentRecordDateTime(), self.frequency, self.absorptioncoefficient))

		receiverinfo = raw[23]
		reserved = raw[24]
		numbeams = raw[25]

		moreinfo1 = raw[26] / 1.0e6
		moreinfo2 = raw[27] / 1.0e6
		moreinfo3 = raw[28] / 1.0e6
		moreinfo4 = raw[29] / 1.0e6
		moreinfo5 = raw[30] / 1.0e6
		moreinfo6 = raw[31] / 1.0e6

		spare = raw[32]
		return		

	def readarray(self, values, scale, offset, datatype):
		''' 
		read the ping array data
		'''
		fmt = '>' + str(self.numbeams) + datatype
		l = struct.calcsize(fmt)
		rec_unpack = struct.Struct(fmt).unpack
		
		data = self.fileptr.read(l) 
		raw = rec_unpack(data)
		for d in raw:
			values.append((d / scale) + offset)
		return values

	def currentRecordDateTime(self):
		return self.from_timestamp(self.time)

	def to_timestamp(self, recordDate):
		return (recordDate - datetime(1970, 1, 1)).total_seconds()

	def from_timestamp(self, unixtime):
		return datetime(1970, 1 ,1) + timedelta(seconds=unixtime)

###############################################################################
class GSFHEADER:
	def __init__(self, fileptr, numbytes, recordidentifier, hdrlen):
		self.recordidentifier = recordidentifier	# assign the GSF code for this datagram type
		self.offset = fileptr.tell()				# remember where this packet resides in the file so we can return if needed
		self.hdrlen = hdrlen						# remember where this packet resides in the file so we can return if needed
		self.numbytes = numbytes					# remember how many bytes this packet contains
		self.fileptr = fileptr						# remember the file pointer so we do not need to pass from the host process
		self.fileptr.seek(numbytes, 1)				# move the file pointer to the end of the record so we can skip as the default actions
		self.name = "GSFHeader"

	def __str__(self):
		'''
		pretty print this class
		'''
		return pprint.pformat(vars(self))

	def read(self):
		rec_fmt = '=12s'
		rec_len = struct.calcsize(rec_fmt)
		rec_unpack = struct.Struct(rec_fmt).unpack

		self.fileptr.seek(self.offset + self.hdrlen, 0)	# move the file pointer to the start of the record so we can read from disc			  
		data = self.fileptr.read(rec_len)
		bytesRead = rec_len
		s = rec_unpack(data)
		
		self.version   = s[0].decode('utf-8').rstrip('\x00')
		return


###############################################################################
class GSFREADER:
	def __init__(self, filename, loadscalefactors=False):
		'''
		class to read generic sensor format files.
		'''
		if not os.path.isfile(filename):
			print ("file not found:", filename)
		self.fileName = filename
		self.fileSize = os.path.getsize(filename)
		f = open(filename, 'r+b')		
		self.fileptr = mmap.mmap(f.fileno(), 0)
		self.hdrfmt = ">LL"
		self.hdrlen = struct.calcsize(self.hdrfmt)
		self.scalefactors = []
		if loadscalefactors:
			self.scalefactors = self.loadscalefactors()

	def moreData(self):
		bytesRemaining = self.fileSize - self.fileptr.tell()
		# print ("current file ptr position: %d size %d" % ( self.fileptr.tell(), self.fileSize))
		return bytesRemaining

	def currentPtr(self):
		return self.fileptr.tell()

	def close(self):
		'''
		close the file
		'''
		self.fileptr.close()
		
	def rewind(self):
		'''
		go back to start of file
		'''
		self.fileptr.seek(0, 0)				

	def __str__(self):
		'''
		pretty print this class
		'''
		return pprint.pformat(vars(self))

	def readDatagramBytes(self, offset, byteCount):
		'''read the entire raw bytes for the datagram without changing the file pointer.  this is used for file conditioning'''
		curr = self.fileptr.tell()
		self.fileptr.seek(offset, 0)   # move the file pointer to the start of the record so we can read from disc			  
		data = self.fileptr.read(byteCount)
		self.fileptr.seek(curr, 0)
		return data

	def loadscalefactors(self):
		'''
		rewind, load the scale factors array and rewind to the original position.  We can then use these scalefactors for every ping
		'''
		curr = self.fileptr.tell()
		self.rewind()

		while self.moreData():
			numberofbytes, recordidentifier, datagram = self.readDatagram()
			if recordidentifier == SWATH_BATHYMETRY:
				datagram.read()
				self.fileptr.seek(curr, 0)
				return datagram.scalefactors
		self.fileptr.seek(curr, 0)
		return None
	
	def loadnavigation(self):
		'''
		rewind, load the navigation from the bathy records and rewind
		'''
		navigation = []
		curr = self.fileptr.tell()
		self.rewind()

		while self.moreData():
			numberofbytes, recordidentifier, datagram = self.readDatagram()
			if recordidentifier == SWATH_BATHYMETRY:
				datagram.read(True)
				navigation.append([datagram.time + datagram.pingnanotime/1000000000.0, datagram.longitude, datagram.latitude])
		self.fileptr.seek(curr, 0)
		print ("Navigation records loaded:", len(navigation))
		return navigation
		
	def getrecordcount(self):
		'''
		rewind, count the number of ping records as fast as possible.  useful for progress bars
		'''
		numpings = 0
		curr = self.fileptr.tell()
		self.rewind()

		while self.moreData():
			numberofbytes, recordidentifier, datagram = self.readDatagram()
			if recordidentifier == SWATH_BATHYMETRY:
				numpings += 1

		self.fileptr.seek(curr, 0)
		return numpings
		
	def readDatagram(self):
		# read the datagram header.  This permits us to skip datagrams we do not support
		numberofbytes, recordidentifier, haschecksumnumberofbytes, hdrlen = self.sniffDatagramHeader()
		
		if recordidentifier == HEADER:
			# create a class for this datagram, but only decode if the resulting class if called by the user.  This makes it much faster
			dg = GSFHEADER(self.fileptr, numberofbytes, recordidentifier, hdrlen)
			return numberofbytes, recordidentifier, dg
		
		elif recordidentifier == SWATH_BATHYMETRY:
			dg = SWATH_BATHYMETRY_PING(self.fileptr, numberofbytes, recordidentifier, hdrlen)
			dg.scalefactors = self.scalefactors
			return numberofbytes, recordidentifier, dg 
		
		# elif recordidentifier == 3: # SOUND_VELOCITY_PROFILE
			# dg = SOUND_VELOCITY_PROFILE(self.fileptr, numberofbytes)
			# return dg.recordidentifier, dg 
		
		else:
			dg = UNKNOWN_RECORD(self.fileptr, numberofbytes, recordidentifier, hdrlen)
			# self.fileptr.seek(numberofbytes, 1) # set the file ptr to the end of the record			
			return numberofbytes, recordidentifier, dg

	def sniffDatagramHeader(self):
		'''
		read the las file header from disc
		'''
		curr = self.fileptr.tell()

		if (self.fileSize - curr) < self.hdrlen:
			# we have reached the end of the fle, so quit
			self.fileptr.seek(self.fileSize,0)
			return (0, 0, False, 0)

		# version header format
		data = self.fileptr.read(self.hdrlen)
		s = struct.unpack(self.hdrfmt, data)
		sizeofdata = s[0]
		recordidentifier = s[1]
		haschecksum = recordidentifier & 0x80000000

		temp = recordidentifier & 0x7FC00000
		reserved = (temp >> 22)

		recordidentifier = (recordidentifier & 0x003FFFFF)

		if haschecksum:
			# read the checksum of 4 bytes if required
			chksum = self.fileptr.read(4)
			return (sizeofdata + self.hdrlen + 4, recordidentifier, haschecksum)
		
		# now reset file pointer to the start of the record
		self.fileptr.seek(curr, 0)
		
		if haschecksum:
			return (sizeofdata + self.hdrlen + 4, recordidentifier, haschecksum, self.hdrlen + 4)
		else:
			return (sizeofdata + self.hdrlen, recordidentifier, haschecksum, self.hdrlen )


def isBitSet(int_type, offset):
	'''testBit() returns a nonzero result, 2**offset, if the bit at 'offset' is one.'''
	mask = 1 << offset
	return (int_type & (1 << offset)) != 0

###############################################################################
def createOutputFileName(path):
	'''Create a valid output filename. if the name of the file already exists the file name is auto-incremented.'''
	path = os.path.expanduser(path)

	if not os.path.exists(os.path.dirname(path)):
		os.makedirs(os.path.dirname(path))

	if not os.path.exists(path):
		return path

	root, ext = os.path.splitext(os.path.expanduser(path))
	dir = os.path.dirname(root)
	fname = os.path.basename(root)
	candidate = fname+ext
	index = 1
	ls = set(os.listdir(dir))
	while candidate in ls:
			candidate = "{}_{}{}".format(fname,index,ext)
			index += 1

	return os.path.join(dir, candidate)

###############################################################################
class cBeam:
	def __init__(self, beamDetail, angle):
		self.sortingDirection	   = beamDetail[0]
		self.detectionInfo		  = beamDetail[1]
		self.numberOfSamplesPerBeam = beamDetail[2]
		self.centreSampleNumber	 = beamDetail[3]
		self.sector				 = 0
		self.takeOffAngle		   = angle	 # used for ARC computation
		self.sampleSum			  = 0		 # used for backscatter ARC computation process
		self.sampleMin			  = 999		 
		self.sampleMax			  = -999		 
		self.samples				= []
		self.name = "beam"
		
	def __str__(self):
		'''
		pretty print this class
		'''
		return pprint.pformat(vars(self))

###############################################################################
if __name__ == "__main__":
	main()

	# def testR2SonicAdjustment():
# 	'''
# 	This test code confirms the results are in alignment with those from Norm Campbell at CSIRO who kindly provided the code in F77
# 	'''
# 	# adjusted backscatter		  -38.6
# 	# adjusted backscatter		  -47.6
# 	# adjusted backscatter		  -27.5
# 	# adjusted backscatter		  -36.6
# 	# adjusted backscatter		  -35.5

# 	S1_angle = -58.0
# 	S1_twtt = 0.20588
# 	S1_range = 164.8
# 	H0_TxPower = 197.0
# 	H0_SoundSpeed = 1468.59
# 	H0_RxAbsorption = 80.0
# 	H0_TxBeamWidthVert = 0.0174533
# 	H0_TxBeamWidthHoriz = 0.0087266
# 	H0_TxPulseWidth = 0.000275
# 	H0_RxSpreading = 35.0
# 	H0_RxGain = 8.0
# 	H0_VTX_Offset = -21.0 / 100.

# 	n_snpt_val = 470
# 	S1_uPa = n_snpt_val
# 	z_snpt_BS_dB = 20. * math.log10(S1_uPa)

# 	adjusted = backscatteradjustment( S1_angle, S1_twtt, S1_range, S1_uPa, H0_TxPower, H0_SoundSpeed, H0_RxAbsorption, H0_TxBeamWidthVert, H0_TxBeamWidthHoriz, H0_TxPulseWidth, H0_RxSpreading, H0_RxGain, H0_VTX_Offset, z_snpt_BS_dB)
# 	print (adjusted)

# 	S1_angle = -58.0
# 	S1_twtt = 0.20588
# 	S1_range = 164.8
# 	H0_TxPower = 206.0
# 	H0_SoundSpeed = 1468.59
# 	H0_RxAbsorption = 80.0
# 	H0_TxBeamWidthVert = 0.0174533
# 	H0_TxBeamWidthHoriz = 0.0087266
# 	H0_TxPulseWidth = 0.000275
# 	H0_RxSpreading = 35.0
# 	H0_RxGain = 8.0
# 	H0_VTX_Offset = -21.0 / 100.

# 	n_snpt_val = 470
# 	S1_uPa = n_snpt_val
# 	z_snpt_BS_dB = 20. * math.log10 ( S1_uPa )
# 	adjusted = backscatteradjustment( S1_angle, S1_twtt, S1_range, S1_uPa, H0_TxPower, H0_SoundSpeed, H0_RxAbsorption, H0_TxBeamWidthVert, H0_TxBeamWidthHoriz, H0_TxPulseWidth, H0_RxSpreading, H0_RxGain, H0_VTX_Offset, z_snpt_BS_dB)
# 	print (adjusted)

# 	S1_angle = - 58.0
# 	S1_twtt = 0.20588
# 	S1_range = 164.8
# 	H0_TxPower = 197.0
# 	H0_SoundSpeed = 1468.59
# 	H0_RxAbsorption = 80.0
# 	H0_TxBeamWidthVert = 0.0174533
# 	H0_TxBeamWidthHoriz = 0.0087266
# 	H0_TxPulseWidth = 0.000275
# 	H0_RxSpreading = 30.0
# 	H0_RxGain = 8.0
# 	H0_VTX_Offset = -21.0 / 100.

# 	n_snpt_val = 470
# 	S1_uPa = n_snpt_val
# 	z_snpt_BS_dB = 20. * math.log10 ( S1_uPa )
# 	adjusted = backscatteradjustment( S1_angle, S1_twtt, S1_range, S1_uPa, H0_TxPower, H0_SoundSpeed, H0_RxAbsorption, H0_TxBeamWidthVert, H0_TxBeamWidthHoriz, H0_TxPulseWidth, H0_RxSpreading, H0_RxGain, H0_VTX_Offset, z_snpt_BS_dB)
# 	print (adjusted)

# 	S1_angle = - 58.0
# 	S1_twtt = 0.20588
# 	S1_range = 164.8
# 	H0_TxPower = 197.0
# 	H0_SoundSpeed = 1468.59
# 	H0_RxAbsorption = 80.0
# 	H0_TxBeamWidthVert = 0.0174533
# 	H0_TxBeamWidthHoriz = 0.0087266
# 	H0_TxPulseWidth = 0.000275
# 	H0_RxSpreading = 35.0
# 	H0_RxGain = 6.0
# 	H0_VTX_Offset = -21.0 / 100.

# 	n_snpt_val = 470
# 	S1_uPa = n_snpt_val
# 	z_snpt_BS_dB = 20. * math.log10 ( S1_uPa )
# 	adjusted = backscatteradjustment( S1_angle, S1_twtt, S1_range, S1_uPa, H0_TxPower, H0_SoundSpeed, H0_RxAbsorption, H0_TxBeamWidthVert, H0_TxBeamWidthHoriz, H0_TxPulseWidth, H0_RxSpreading, H0_RxGain, H0_VTX_Offset, z_snpt_BS_dB)
# 	print (adjusted)


# 	S1_angle = - 58.0
# 	S1_twtt = 0.20588
# 	S1_range = 164.8
# 	H0_TxPower = 207.0
# 	H0_SoundSpeed = 1468.59
# 	H0_RxAbsorption = 80.0
# 	H0_TxBeamWidthVert = 0.0174533
# 	H0_TxBeamWidthHoriz = 0.0087266
# 	H0_TxPulseWidth = 0.000275
# 	H0_RxSpreading = 30.0
# 	H0_RxGain = 6.0
# 	H0_VTX_Offset = -21.0 / 100.

# 	n_snpt_val = 470
# 	S1_uPa = n_snpt_val
# 	z_snpt_BS_dB = 20. * math.log10 ( S1_uPa )
# 	adjusted = backscatteradjustment( S1_angle, S1_twtt, S1_range, S1_uPa, H0_TxPower, H0_SoundSpeed, H0_RxAbsorption, H0_TxBeamWidthVert, H0_TxBeamWidthHoriz, H0_TxPulseWidth, H0_RxSpreading, H0_RxGain, H0_VTX_Offset, z_snpt_BS_dB)
# 	print (adjusted)

# 	return



###############################################################################
