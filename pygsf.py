#name:		  pygsf
#created:	   July 2017
#by:			p.kennedy@fugro.com
#description:   python module to read and write a Generic Sensor Formaty (GSF) file natively
#notes:		 See main at end of script for example how to use this
#based on GSF Version 3.04

# See readme.md for more details

# GSF FORMAT DEFINITION:
# TransmiTRAVEL_TIME_ARRAYal Header (optional)
# Metadata files (optional)
# Data Files[s]
# 
# All data are in big-endian format.
# The public header block contains generic data such as point numbers and point data bounds.

import os.path
import struct
import pprint
import time
import datetime
import math
import random

#/* The high order 4 bits are used to define the field size for this array */
GSF_FIELD_SIZE_DEFAULT  = 0x00  #/* Default values for field size are used used for all beam arrays */
GSF_FIELD_SIZE_ONE      = 0x10  #/* value saved as a one byte value after applying scale and offset */
GSF_FIELD_SIZE_TWO      = 0x20  #/* value saved as a two byte value after applying scale and offset */
GSF_FIELD_SIZE_FOUR     = 0x40  #/* value saved as a four byte value after applying scale and offset */
GSF_MAX_PING_ARRAY_SUBRECORDS = 26

def main():

	testreader()

###############################################################################

###############################################################################
class UNKNOWN_RECORD:
	'''used as a convenience tool for datagrams we have no bespoke classes.  BeTRAVEL_TIME_ARRAYer to make a bespoke class'''
	def __init__(self, fileptr, numbytes, recordidentifier, hdrlen):
		self.recordidentifier = recordidentifier
		self.offset = fileptr.tell()
		self.hdrlen = hdrlen
		self.numbytes = numbytes
		self.fileptr = fileptr
		self.fileptr.seek(numbytes, 1)
		self.data = ""
	def read(self):
		self.data = self.fileptr.read(self.numberofbytes)

# class SCALEINFO:
# 	def __init__(self):
# 		self.compressionFlag = 0    /* Specifies bytes of storage in high order nibble and type of compression in low order nibble */
# 		self.multiplier = 0.0
# 		self.offset = 0
# 		# unsigned char   compressionFlag;    /* Specifies bytes of storage in high order nibble and type of compression in low order nibble */
# 		# double          multiplier;         /* the scale factor (millionths)for the array */
# 		# double          offset;             /* dc offset to scale data by */
# } gsfScaleInfo;

class SCALEFACTOR:
	def __init__(self):
		self.subrecordID = 0    
		self.compressionFlag = 0    #/* Specifies bytes of storage in high order nibble and type of compression in low order nibble */
		self.multiplier = 0.0
		self.offset = 0
# 		    self.numArraySubrecords = 0 #/* the number of scaling factors we actually have */
#     		self.gsfScaleInfo    scaleTable[GSF_MAX_PING_ARRAY_SUBRECORDS];
	
	
class SWATH_BATHYMETRY_PING :
	def __init__(self, fileptr, numbytes, recordidentifier, hdrlen):
		self.recordidentifier = recordidentifier	# assign the GSF code for this datagram type
		self.offset = fileptr.tell()	# remember where this packet resides in the file so we can return if needed
		self.hdrlen = hdrlen			# remember the header length.  it should be 8 bytes, bout if checksum then it is 12
		self.numbytes = numbytes			# remember how many bytes this packet contains
		self.fileptr = fileptr			# remember the file pointer so we do not need to pass from the host process
		self.fileptr.seek(numbytes, 1)		# move the file pointer to the end of the record so we can skip as the default actions
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

	def read(self):        
		self.fileptr.seek(self.offset + self.hdrlen, 0)   # move the file pointer to the start of the record so we can read from disc              

		# read ping header
		hdrfmt = '>ll ll 5h l H 3h 2H lll h'
		hdrlen = struct.calcsize(hdrfmt)
		rec_unpack = struct.Struct(hdrfmt).unpack

		self.fileptr.seek(self.offset + self.hdrlen , 0)   # move the file pointer to the start of the record so we can read from disc              
		data = self.fileptr.read(hdrlen)   # read the record from disc
		s = rec_unpack(data)
		self.time 			= s[0] #ll
		self.longitude 		= s[2] / 10000000 # l
		self.latitude		= s[3] / 10000000 # l
		self.numbeams 		= s[4] # h
		self.centrebeam 	= s[5] # h
		self.pingflags 		= s[6] # h
		self.reserved 		= s[7] # h
		self.tidecorrector	= s[8] / 100 # h
		self.depthcorrector	= s[9] / 100 # l
		self.heading		= s[10] / 100 # H
		self.pitch			= s[11] / 100 #h
		self.roll			= s[12] / 100 #h
		self.heave			= s[13] / 100 #h
		self.course			= s[14] / 100 # H
		self.speed			= s[15] / 100 # H
		self.height			= s[16] / 100 # l
		self.separation		= s[17] / 100 # l
		self.gpstidecorrector	= s[18] / 100 # l
		self.spare			= s[19] # h

		while (self.fileptr.tell() < self.offset + self.numbytes):
			fmt = '>l'
			fmtlen = struct.calcsize(fmt)
			rec_unpack = struct.Struct(fmt).unpack
			data = self.fileptr.read(fmtlen)   # read the record from disc
			s = rec_unpack(data)

			subrecord_id = (s[0] & 0xFF000000) >> 24
			subrecord_size = s[0] & 0x00FFFFFF

			# if bytes_per_value == 1:
			# 	field_size = GSF_FIELD_SIZE_ONE
			# elif bytes_per_value == 2:
			# 	field_size = GSF_FIELD_SIZE_TWO
			# elif bytes_per_value == 4:
			# 	field_size = GSF_FIELD_SIZE_FOUR
			# else:
			# 	# field_size = (ft->rec.mb_ping.scaleFactors.scaleTable[subrecord_id - 1].compressionFlag & 0xF0);
			# 	# field_size = self.scalefactors[subrecord_id-1].compressionFlag & 0xF0
			# 	field_size = GSF_FIELD_SIZE_ONE #temp until we understand how to work with the field size for the scale factors sub record which does not need this parameter

			print ("Subrec: %d %d" % (subrecord_id, subrecord_size))
			# now decode the subrecord
			
			scale, offset, compressionFlag, datatype = self.getscalefactor(subrecord_id, subrecord_size / int(self.numbeams))
			
			if subrecord_id == 100: 
				self.readscalefactors()
			elif subrecord_id == 1: 
				self.readarray(self.DEPTH_ARRAY, scale, offset, datatype)
			# elif subrecord_id == 2: 
			# 	self.readarray(self.ACROSS_TRACK_ARRAY, scale, offset, datatype)
			# elif subrecord_id == 3: 
			# 	self.readarray(self.ALONG_TRACK_ARRAY, scale, offset, datatype)
			# elif subrecord_id == 4: 
			# 	self.readarray(self.TRAVEL_TIME_ARRAY, scale, offset, datatype)
			# elif subrecord_id == 5: 
			# 	self.readarray(self.BEAM_ANGLE_ARRAY, scale, offset, datatype)
			# elif subrecord_id == 7: 
			# 	self.readarray(self.MEAN_REL_AMPLITUDE_ARRAY, scale, offset, datatype)
			# elif subrecord_id == 9: 
			# 	self.readarray(self.QUALITY_FACTOR_ARRAY, scale, offset, datatype)
			# elif subrecord_id == 16: 
			# 	self.readarray(self.BEAM_FLAGS_ARRAY, scale, offset, datatype)
			# elif subrecord_id == 18: 
			# 	self.readarray(self.BEAM_ANGLE_FORWARD_ARRAY, scale, offset, datatype)
			# elif subrecord_id == 19: 
			# 	self.readarray(self.VERTICAL_ERROR_ARRAY, scale, offset, datatype)
			# elif subrecord_id == 20: 
			# 	self.readarray(self.VERTICAL_ERROR_ARRAY, scale, offset, datatype)
			# elif subrecord_id == 21: 
			# 	self.readintensityarray(self.INTENSITY_SERIES_ARRAY, scale, offset, datatype)
			# elif subrecord_id == 22: 
			# 	self.readarray(self.SECTOR_NUMBER_ARRAY, scale, offset, datatype)
			else:
				# read to the end of the record to keep in alignment.  This permits us to not have all the decodes in place
				print ("skipping: %d %d" % (subrecord_id, subrecord_size))
				if subrecord_id == 21: # pk  we should not realy do this, but it is required.  We need to investigate why todo
					subrecord_size -= 1
				self.fileptr.read(subrecord_size)

		return

	def getscalefactor(self, ID, bytes_per_value):
		
		for s in self.scalefactors:
			if s.subrecordID == ID:# DEPTH_ARRAY array

				if bytes_per_value == 1:
					datatype = 'B' #unsigned values
				elif bytes_per_value == 2:
					datatype = 'H'#unsigned values
					if ID == 2:# ACROSS_TRACK_ARRAY array
						datatype = 'h'#unsigned values
					if ID == 5:# beam angle array
						datatype = 'h'#unsigned values
				elif bytes_per_value == 4:
					datatype = 'L'#unsigned values
					if ID == 2:# ACROSS_TRACK_ARRAY array
						datatype = 'l'#unsigned values
					if ID == 5:# beam angle array
						datatype = 'l'#unsigned values
				else:
					datatype = 'L'#unsigned values

				return s.multiplier, s.offset, s.compressionFlag, datatype


		return 0,0,0, 'b'

	def readscalefactors(self):
		# /* First four byte integer contains the number of scale factors */
		# now read all scale factors
		scalefmt = '>l'
		scalelen = struct.calcsize(scalefmt)
		rec_unpack = struct.Struct(scalefmt).unpack

		data = self.fileptr.read(scalelen)   # read the record from disc
		s = rec_unpack(data)
		self.numscalefactors = s[0]

		scalefmt = '>lll'
		scalelen = struct.calcsize(scalefmt)
		rec_unpack = struct.Struct(scalefmt).unpack

		for i in range(self.numscalefactors):
			data = self.fileptr.read(scalelen)   # read the record from disc
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
		read the time series intensity array
		'''

		# need to do this for each beam...
		# fmt = '>' + str(self.numbeams) + datatype

		hdrfmt = '>hh8s'
		hdrlen = struct.calcsize(hdrfmt)
		rec_unpack = struct.Struct(hdrfmt).unpack
		hdr = self.fileptr.read(hdrlen)   # read the record from disc
		s = rec_unpack(hdr)
		
		numsamples = s[0]
		bottomdetectsamplenumber = s[1]
		spare = s[2]

		fmt = '>' + str(numsamples) + 'l'
		l = struct.calcsize(fmt)
		rec_unpack = struct.Struct(fmt).unpack
		
		data = self.fileptr.read(l)  
		raw = rec_unpack(data)
		for d in raw:
			values.append((d / scale) + offset)
		return values

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

class GSFHEADER:
	def __init__(self, fileptr, numbytes, recordidentifier, hdrlen):
		self.recordidentifier = recordidentifier       # assign the GSF code for this datagram type
		self.offset = fileptr.tell()    # remember where this packet resides in the file so we can return if needed
		self.hdrlen = hdrlen    # remember where this packet resides in the file so we can return if needed
		self.numbytes = numbytes              # remember how many bytes this packet contains
		self.fileptr = fileptr          # remember the file pointer so we do not need to pass from the host process
		self.fileptr.seek(numbytes, 1)     # move the file pointer to the end of the record so we can skip as the default actions

	def read(self):        
		rec_fmt = '=12s'
		rec_len = struct.calcsize(rec_fmt)
		rec_unpack = struct.Struct(rec_fmt).unpack

		self.fileptr.seek(self.offset + self.hdrlen, 0)   # move the file pointer to the start of the record so we can read from disc              
		data = self.fileptr.read(rec_len)   # read the record from disc
		bytesRead = rec_len
		s = rec_unpack(data)
		
		self.version   = s[0].decode('utf-8').rstrip('\x00')

class GSFREADER:
	def __init__(self, filename):
		if not os.path.isfile(filename):
			print ("file not found:", filename)
		self.fileName = filename
		self.fileptr = open(filename, 'rb')		
		self.fileSize = os.path.getsize(filename)
		self.hdrfmt = ">LL"
		self.hdrlen = struct.calcsize(self.hdrfmt)

	def moreData(self):
		bytesRemaining = self.fileSize - self.fileptr.tell()
		# print ("current file ptr position:", self.fileptr.tell())
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
		preTRAVEL_TIME_ARRAYy print this class
		'''
		return pprint.pformat(vars(self))

	def readDatagramBytes(self, offset, byteCount):
		'''read the entire raw bytes for the datagram without changing the file pointer.  this is used for file conditioning'''
		curr = self.fileptr.tell()
		self.fileptr.seek(offset, 0)   # move the file pointer to the start of the record so we can read from disc              
		data = self.fileptr.read(byteCount)
		self.fileptr.seek(curr, 0)
		return data

	def readDatagram(self):
		# read the datagram header.  This permits us to skip datagrams we do not support
		numberofbytes, recordidentifier, haschecksumnumberofbytes, hdrlen = self.readDatagramHeader()
		# print ("%d %d %d " % (numberofbytes, recordidentifier, self.fileptr.tell()))
		if recordidentifier == 1: # Header, the GSF Version
			# create a class for this datagram, but only decode if the resulting class is called by the user.  This makes it much faster
			dg = GSFHEADER(self.fileptr, numberofbytes, recordidentifier, hdrlen)
			return numberofbytes, recordidentifier, dg

		elif recordidentifier == 2: #SWATH_BATHYMETRY_PING
		# pkpk need to make a dummy scale factor here and then return it.  This is because it is not in every ping, only the first one.
			dg = SWATH_BATHYMETRY_PING(self.fileptr, numberofbytes, recordidentifier, hdrlen)
			# dg.read()

			return dg.recordidentifier, recordidentifier, dg 

		# elif recordidentifier == 3: # SOUND_VELOCITY_PROFILE
			# dg = SOUND_VELOCITY_PROFILE(self.fileptr, numberofbytes)
			# return dg.recordidentifier, dg 
		else:
			dg = UNKNOWN_RECORD(self.fileptr, numberofbytes, recordidentifier, hdrlen)
			return numberofbytes, recordidentifier, dg

			# self.fileptr.seek(numberofbytes, 1)
			# return numberofbytes, recordidentifier, 0

	def readDatagramHeader(self):
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

		sizeofdata =					s[0]
		recordidentifier =				s[1]
		haschecksum = recordidentifier & 0x80000000

		temp = recordidentifier & 0x7FC00000
		reserved = (temp >> 22)

		recordidentifier = (recordidentifier & 0x003FFFFF)

		if haschecksum:
			# read the checksum of 4 bytes if required
			chksum = self.fileptr.read(4)
			return (sizeofdata + self.hdrlen + 4, recordidentifier, haschecksum)
		
		# now reset file pointer
		self.fileptr.seek(curr, 0)
		
		if haschecksum:
			return (sizeofdata + self.hdrlen + 4, recordidentifier, haschecksum, self.hdrlen + 4)
		else:
			return (sizeofdata + self.hdrlen, recordidentifier, haschecksum, self.hdrlen )

def testreader():
	'''
	sample read script so we can see how to use the code
	'''
	start_time = time.time() # time the process so we can keep it quick
	writeConditionedFile = False
	exclude = [12]
	filename = "C:/development/python/sample_subset.gsf"

	if writeConditionedFile:
		outFileName = os.path.join(os.path.dirname(os.path.abspath(filename)), "subset.gsf")
		outFileName = createOutputFileName(outFileName)
		outFilePtr = open(outFileName, 'wb')
		print ("output file: %s" % outFileName)

	# create a GSFREADER class and pass the filename
	r = GSFREADER(filename)

	while r.moreData():
		# read a datagram.  If we support it, return the datagram type and aclass for that datagram
		# The user then needs to call the read() method for the class to undertake a fileread and binary decode.  This keeps the read super quick.
		numberofbytes, recordidentifier, datagram = r.readDatagram()
		# print(recordidentifier, end='')
		print (r.fileptr.tell())

		# read the bytes into a buffer 
		rawBytes = r.readDatagramBytes(datagram.offset, numberofbytes)

# 20
# 2252
# 4056
# 24832
# 45268
		if recordidentifier == 2: #SWATH_BATHYMETRY_PING
			datagram.read()
			print ("ping at offset:", datagram.time)
			# print ("%.3f, %.3f" % (datagram.longitude, datagram.latitude))

		if recordidentifier in exclude:
			continue

		# if writeConditionedFile:
		# 	outFilePtr.write(rawBytes)

	print("Duration %.3fs" % (time.time() - start_time )) # time the process

	return

def isBitSet(int_type, offset):
	'''testBit() returns a nonzero result, 2**offset, if the bit at 'offset' is one.'''
	mask = 1 << offset
	return (int_type & (1 << offset)) != 0

###############################################################################
def createOutputFileName(path):
	'''Create a valid output filename. if the name of the file already exists the file name is auto-incremented.'''
	path      = os.path.expanduser(path)

	if not os.path.exists(os.path.dirname(path)):
		os.makedirs(os.path.dirname(path))

	if not os.path.exists(path):
		return path

	root, ext = os.path.splitext(os.path.expanduser(path))
	dir       = os.path.dirname(root)
	fname     = os.path.basename(root)
	candidate = fname+ext
	index     = 1
	ls        = set(os.listdir(dir))
	while candidate in ls:
			candidate = "{}_{}{}".format(fname,index,ext)
			index    += 1

	return os.path.join(dir, candidate)


###############################################################################
if __name__ == "__main__":
	main()

















