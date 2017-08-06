#name:			pygsf
#created:		July 2017
#by:			p.kennedy@fugro.com
#description:	python module to read and write a Generic Sensor Formaty (GSF) file natively
#notes:			See main at end of script for example how to use this
#based on GSF Version 3.05

# See readme.md for more details

import os.path
import struct
import pprint
import time
import datetime
import math
import random
from datetime import datetime
from datetime import timedelta

#/* The high order 4 bits are used to define the field size for this array */
GSF_FIELD_SIZE_DEFAULT  = 0x00  #/* Default values for field size are used used for all beam arrays */
GSF_FIELD_SIZE_ONE      = 0x10  #/* value saved as a one byte value after applying scale and offset */
GSF_FIELD_SIZE_TWO      = 0x20  #/* value saved as a two byte value after applying scale and offset */
GSF_FIELD_SIZE_FOUR     = 0x40  #/* value saved as a four byte value after applying scale and offset */
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

###############################################################################
def main():
	testreader()
	# conditioner()

def testreader():
	'''
	sample read script so we can see how to use the code
	'''
	start_time = time.time() # time the process so we can keep it quick
	filename = "C:/development/python/sample_subset.gsf"
	pingcount = 0
	# create a GSFREADER class and pass the filename
	r = GSFREADER(filename)
	# r.loadnavigation()

	while r.moreData():
		# read a datagram.  If we support it, return the datagram type and aclass for that datagram
		# The user then needs to call the read() method for the class to undertake a fileread and binary decode.  This keeps the read super quick.
		numberofbytes, recordidentifier, datagram = r.readDatagram()
		# print(recordidentifier, end='')

		if recordidentifier == SWATH_BATHYMETRY:
			datagram.read()
			if datagram.pingnumber == 76610:
				print (" %s ping #: %d %d %.2f" % (datagram.currentRecordDateTime(), datagram.pingnumber, datagram.frequency, datagram.DEPTH_ARRAY[2]))
			pingcount += 1
	print("Duration %.3fs" % (time.time() - start_time )) # time the process
	print ("PingCount:", pingcount)
	return

###############################################################################
def conditioner():
	'''
	sample condition script so we can strip out unrequired datagrams such as verbose attitude records
	'''
	start_time = time.time() # time the process so we can keep it quick
	writeConditionedFile = True
	exclude = [ATTITUDE] #exclude records of this type (attitude is type 12)
	filename = "C:/development/python/sample.gsf"

	if writeConditionedFile:
		outFileName = os.path.join(os.path.dirname(os.path.abspath(filename)), os.path.splitext(os.path.basename(filename))[0] + "_subset.gsf")
		outFileName = createOutputFileName(outFileName)
		outFilePtr = open(outFileName, 'wb')
		print ("output file: %s" % outFileName)

	# create a GSFREADER class and pass the filename
	r = GSFREADER(filename, False)

	excluded = 0 
	while r.moreData():
		# read a datagram.  If we support it, return the datagram type and aclass for that datagram
		# The user then needs to call the read() method for the class to undertake a fileread and binary decode.  This keeps the read super quick.
		numberofbytes, recordidentifier, datagram = r.readDatagram()

		# read the bytes into a buffer 
		rawBytes = r.readDatagramBytes(datagram.offset, numberofbytes)

		if recordidentifier in exclude:
			excluded += 1
			continue

		if writeConditionedFile:
			outFilePtr.write(rawBytes)

	print("Duration %.3fs record count excluded: %d" % ((time.time() - start_time ), excluded)) # time the process

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

	def read(self):
		self.data = self.fileptr.read(self.numberofbytes)

class SCALEFACTOR:
	def __init__(self):
		self.subrecordID = 0    
		self.compressionFlag = 0    #/* Specifies bytes of storage in high order nibble and type of compression in low order nibble */
		self.multiplier = 0.0
		self.offset = 0
	
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
		self.MEAN_REL_AMPLITUDE_ARRAY = []
		self.QUALITY_FACTOR_ARRAY = []
		self.BEAM_FLAGS_ARRAY = []
		self.BEAM_ANGLE_FORWARD_ARRAY = []
		self.VERTICAL_ERROR_ARRAY = []
		self.HORIZONTAL_ERROR_ARRAY = []
		self.SECTOR_NUMBER_ARRAY = []
		self.INTENSITY_SERIES_ARRAY = []

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
			# if headeronly:
			# 	self.fileptr.seek(subrecord_size, 1) #move forwards to the end of teh record
			# 	if subrecord_id == 21: 
			# 		if subrecord_size % 4 > 0:
			# 			self.fileptr.seek(4 - (subrecord_size % 4), 1) #pkpk we should not need this!!!
			# 	continue

			# now decode the subrecord
			curr = self.fileptr.tell()
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
				self.readintensityarray(self.INTENSITY_SERIES_ARRAY, scale, offset, datatype)
				if subrecord_size % 4 > 0:
					self.fileptr.seek(4 - (subrecord_size % 4), 1) #pkpk we should not need this!!!
					
				# self.fileptr.seek(self.offset + self.numbytes, 0) #pkpk we should not need this!!!
				# self.fileptr.seek(curr+subrecord_size-1,0) 
			elif subrecord_id == 22: 
				self.readarray(self.SECTOR_NUMBER_ARRAY, scale, offset, datatype)
			else:
				# read to the end of the record to keep in alignment.  This permits us to not have all the decodes in place
				# print ("skipping rec: %d size: %d offset: %d" % (subrecord_id, subrecord_size, self.fileptr.tell()))
				# if subrecord_id == 21: # pk  we should not realy do this, but it is required.  We need to investigate why todo
				# 	subrecord_size -= 1
				self.fileptr.seek(subrecord_size, 1) #move forwards to the end of teh record
				# self.fileptr.read(subrecord_size)
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

	def readintensityarray(self, values, scale, offset, datatype):
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
			for d in raw:
				values.append((d / scale) + offset)
		return values

	def decodeR2SonicImagerySpecific(self):
		''' 
		read the imagery information for the r2sonic 2024
		'''
		fmt = '>12s12slll lllll lllll lllll lllhh lllll l32s'
		l = struct.calcsize(fmt)
		rec_unpack = struct.Struct(fmt).unpack
		data = self.fileptr.read(l) 
		raw = rec_unpack(data)
		
		self.modelnumber = raw[0]
		self.serialnumber = raw[1]

		self.pingtime = raw[2]
		self.pingnanotime = raw[3]
		self.pingnumber = raw[4]
		self.pingperiod = raw[5] / 1.0e6
		self.soundspeed = raw[6] / 1.0e2

		self.frequency = raw[7] / 1.0e3
		transmitsourcelevel = raw[8] / 1.0e2
		pulsewidth = raw[9] / 1.0e7
		beamwidthvertical = raw[10] / 1.0e6
		beamwidthhorizontal = raw[11] / 1.0e6

		transmitsteeringvertical = raw[12] / 1.0e6
		transmitsteeringhorizontal = raw[13] / 1.0e6
		transmitinfo = raw[14]
		receiverbandwidth = raw[15] / 1.0e4
		receiversamplerate = raw[16] / 1.0e3
		
		receiverrange = raw[17] / 1.0e5
		receivergain = raw[18] / 1.0e2
		receiverspreadingloss = raw[19] / 1.0e3
		absorptioncoefficient = raw[20]/ 1.0e3
		mounttiltangle = raw[21] / 1.0e6

		receiverinfo = raw[22]
		reserved = raw[23]
		numbeams = raw[24]

		moreinfo1 = raw[25] / 1.0e6
		moreinfo2 = raw[26] / 1.0e6
		moreinfo3 = raw[27] / 1.0e6
		moreinfo4 = raw[28] / 1.0e6
		moreinfo5 = raw[29] / 1.0e6
		moreinfo6 = raw[30] / 1.0e6

		spare = raw[31]
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
		Class to read generic sensor format files.
		'''
		if not os.path.isfile(filename):
			print ("file not found:", filename)
		self.fileName = filename
		self.fileptr = open(filename, 'rb')		
		self.fileSize = os.path.getsize(filename)
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
				navigation.append([datagram.time, datagram.longitude, datagram.latitude])
		
		self.fileptr.seek(curr, 0)
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
if __name__ == "__main__":
	main()