#name:		  pygsf
#created:	   July 2017
#by:			p.kennedy@fugro.com
#description:   python module to read and write a Generic Sensor Formaty (GSF) file natively
#notes:		 See main at end of script for example how to use this
#based on GSF Version 3.04

# See readme.md for more details

# GSF FORMAT DEFINITION:
# Transmittal Header (optional)
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

def main():

	testreader()

###############################################################################

###############################################################################
class UNKNOWN_RECORD:
	'''used as a convenience tool for datagrams we have no bespoke classes.  Better to make a bespoke class'''
	def __init__(self, fileptr, numberofbytes, recordidentifier):
		self.typeOfDatagram = recordidentifier
		self.offset = fileptr.tell()
		self.numberofbytes = numberofbytes
		self.fileptr = fileptr
		self.fileptr.seek(numberofbytes, 1)
		self.data = ""
	def read(self):
		self.data = self.fileptr.read(self.numberofbytes)

class PROCESSING_PARAMETERS :
	def __init__(self, fileptr, bytes, recordidentifier):
		self.recordidentifier = recordidentifier       # assign the GSF code for this datagram type
		self.offset = fileptr.tell()    # remember where this packet resides in the file so we can return if needed
		self.bytes = bytes              # remember how many bytes this packet contains
		self.fileptr = fileptr          # remember the file pointer so we do not need to pass from the host process
		self.fileptr.seek(bytes, 1)     # move the file pointer to the end of the record so we can skip as the default actions

	def read(self):        
		self.fileptr.seek(self.offset, 0)   # move the file pointer to the start of the record so we can read from disc              
		rec_fmt = '=12s'
		rec_len = struct.calcsize(rec_fmt)
		rec_unpack = struct.Struct(rec_fmt).unpack
		data = self.fileptr.read(rec_len)   # read the record from disc
		bytesRead = rec_len
		s = rec_unpack(data)
		
		self.version   = s[0].decode('utf-8').rstrip('\x00')

class GSFHEADER:
	def __init__(self, fileptr, bytes, recordidentifier):
		self.recordidentifier = recordidentifier       # assign the GSF code for this datagram type
		self.offset = fileptr.tell()    # remember where this packet resides in the file so we can return if needed
		self.bytes = bytes              # remember how many bytes this packet contains
		self.fileptr = fileptr          # remember the file pointer so we do not need to pass from the host process
		self.fileptr.seek(bytes, 1)     # move the file pointer to the end of the record so we can skip as the default actions

	def read(self):        
		rec_fmt = '=12s'
		rec_len = struct.calcsize(rec_fmt)
		self.fileptr.seek(self.offset + (self.bytes - rec_len), 0)   # move the file pointer to the start of the record so we can read from disc              
		rec_unpack = struct.Struct(rec_fmt).unpack
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

	def readDatagram(self):
		# read the datagram header.  This permits us to skip datagrams we do not support
		numberofbytes, recordidentifier, haschecksumnumberofbytes = self.readDatagramHeader()
		# print ("%d %d %d " % (numberofbytes, recordidentifier, self.fileptr.tell()))
		if recordidentifier == 1: # Header, the GSF Version
			# create a class for this datagram, but only decode if the resulting class is called by the user.  This makes it much faster
			dg = GSFHEADER(self.fileptr, numberofbytes, recordidentifier)
			dg.read()
			return numberofbytes, dg.recordidentifier, dg

		# elif recordidentifier == 2: #SWATH_BATHYMETRY_PING
		# 	return dg.recordidentifier, dg 

		# elif recordidentifier == 3: # SOUND_VELOCITY_PROFILE
			# dg = SOUND_VELOCITY_PROFILE(self.fileptr, numberofbytes)
			# return dg.recordidentifier, dg 

		# elif recordidentifier == 4: # PROCESSING_PARAMETERS
		# 	return dg.recordidentifier, dg 

		# 	return dg.recordidentifier, dg 
		# elif recordidentifier == 88: # X Depth
		# 	dg = X_DEPTH(self.fileptr, numberofbytes)
		# 	return dg.recordidentifier, dg 
		# elif recordidentifier == 68: # D DEPTH
		# 	dg = D_DEPTH(self.fileptr, numberofbytes)
		# 	return dg.recordidentifier, dg
		else:
			dg = UNKNOWN_RECORD(self.fileptr, numberofbytes, recordidentifier)
			return numberofbytes, recordidentifier, dg

			# self.fileptr.seek(numberofbytes, 1)
			# return numberofbytes, recordidentifier, 0

	def readDatagramHeader(self):
		'''
		read the las file header from disc
		'''
		curr = self.fileptr.tell()

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
			return (sizeofdata + self.hdrlen + 4, recordidentifier, haschecksum)
		else:
			return (sizeofdata + self.hdrlen, recordidentifier, haschecksum)

def testreader():
	'''
	sample read script so we can see how to use the code
	'''
	start_time = time.time() # time the process so we can keep it quick
	writeConditionedFile = True
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

		# read the bytes into a buffer 
		rawBytes = r.readDatagramBytes(datagram.offset, numberofbytes)

		if recordidentifier in exclude:
			continue

		if writeConditionedFile:
			outFilePtr.write(rawBytes)

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

















