#name:          pygsf
#created:       July 2017
#by:            p.kennedy@fugro.com
#description:   python module to read and write a Generic Sensor Formaty (GSF) file natively
#notes:         See main at end of script for example how to use this
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
class lashdr:
    def __init__(self):
        # version 1.4 header format
        self.hdrfmt = "<4sHHL HH8sBB 32s32sHHH LLBHL 5Ldddd ddddd dddQQ LQ15Q"
        self.hdrlen = struct.calcsize(self.hdrfmt)

        # create a default template for a V1.4 header.  We use this for writing purposes
        self.FileSignature =                       b'LASF'
        self.FileSourceID  =                       0
        self.GlobalEncoding =                      17
        self.ProjectIDGUIDdata1 =                  0
        self.ProjectIDGUIDdata2 =                  0
        self.ProjectIDGUIDdata3 =                  0
        self.ProjectIDGUIDdata4 =                  b"12345678"
        self.VersionMajor =                        1
        self.VersionMinor =                        4

        self.SystemIdentifier =                    b'pylasfile writer'
        self.GeneratingSoftware =                  b'pylasfile writer'
        self.FileCreationDayofYear =               datetime.datetime.now().timetuple().tm_yday
        self.FileCreationYear =                    datetime.datetime.now().year
        self.HeaderSize =                          375
        self.Offsettopointdata =                   375
        self.NumberofVariableLengthRecords =       0
        self.PointDataRecordFormat =               1
        self.PointDataRecordLength =               28

        self.LegacyNumberofpointrecords =          0
        self.LegacyNumberofpointsbyreturn1 =       0
        self.LegacyNumberofpointsbyreturn2 =       0
        self.LegacyNumberofpointsbyreturn3 =       0
        self.LegacyNumberofpointsbyreturn4 =       0
        self.LegacyNumberofpointsbyreturn5 =       0
        self.Xscalefactor =                        1
        self.Yscalefactor =                        1
        self.Zscalefactor =                        1

        self.Xoffset =                             0
        self.Yoffset =                             0
        self.Zoffset =                             0
        self.MaxX =                                0
        self.MinX =                                0
        self.MaxY =                                0
        self.MinY =                                0
        self.MaxZ =                                0
        self.MinZ =                                0

        self.StartofWaveformDataPacketRecord =     0
        self.StartoffirstExtendedVariableLengthRecord =    0
        self.NumberofExtendedVariableLengthRecords   = 0
        self.Numberofpointrecords =                0
        self.Numberofpointsbyreturn1 =             0  
        self.Numberofpointsbyreturn2 =             0  
        self.Numberofpointsbyreturn3 =             0  
        self.Numberofpointsbyreturn4 =             0  
        self.Numberofpointsbyreturn5 =             0  

        self.Numberofpointsbyreturn6 =             0  
        self.Numberofpointsbyreturn7 =             0  
        self.Numberofpointsbyreturn8 =             0  
        self.Numberofpointsbyreturn9 =             0  
        self.Numberofpointsbyreturn10 =             0  
        self.Numberofpointsbyreturn11 =             0  
        self.Numberofpointsbyreturn12 =             0  
        self.Numberofpointsbyreturn13 =             0  
        self.Numberofpointsbyreturn14 =             0  
        self.Numberofpointsbyreturn15 =             0  

    def __str__(self):
        '''
        pretty print this class
        '''
        return pprint.pformat(vars(self))

    def getsupportedformats(self):
        s = []
        # format 0
        fmt = "<lllHBBbBH"
        fmtlen = struct.calcsize(fmt)
        s.append([fmt,fmtlen])

        # format 1
        fmt = "<lllH BB B BH d"
        fmtlen = struct.calcsize(fmt)
        s.append([fmt,fmtlen])

        # format 2
        fmt = "<lllH BBBBH HHH"
        fmtlen = struct.calcsize(fmt)
        s.append([fmt,fmtlen])

        # format 3
        fmt = "<lllHBBBBH d HHH"
        fmtlen = struct.calcsize(fmt)
        s.append([fmt,fmtlen])

        # format 4
        fmt = "<lllH BBBBH d BQLffff"
        fmtlen = struct.calcsize(fmt)
        s.append([fmt,fmtlen])
    
        # format 5
        fmt = "<lllH BBBB HdHH H BQLffff"
        fmtlen = struct.calcsize(fmt)
        s.append([fmt,fmtlen])

        # format 6
        fmt = "<lllH BBBB hHd"
        fmtlen = struct.calcsize(fmt)
        s.append([fmt,fmtlen])
    
        # format 7
        fmt = "<lllHBBBBhHdHHH"
        fmtlen = struct.calcsize(fmt)
        s.append([fmt,fmtlen])

        # format 8
        fmt = "<lllHBBBBhHdHHHH"
        fmtlen = struct.calcsize(fmt)
        s.append([fmt,fmtlen])

        # format 9
        fmt = "<lllH BBBB hH d BQLffff"
        fmtlen = struct.calcsize(fmt)
        s.append([fmt,fmtlen])

        # format 10
        fmt = "<lllH BBBB hHdH HHHB BBffff"
        fmtlen = struct.calcsize(fmt)
        s.append([fmt,fmtlen])

        return s

    def hdr2tuple(self):
        '''
        convert the header properties into a tuple so we can easily write it to disc using struct
        '''    
        return (
                self.FileSignature, 
                self.FileSourceID,
                self.GlobalEncoding,
                self.ProjectIDGUIDdata1,
                self.ProjectIDGUIDdata2, 
                self.ProjectIDGUIDdata3, 
                self.ProjectIDGUIDdata4,
                self.VersionMajor,
                self.VersionMinor,

                self.SystemIdentifier,
                self.GeneratingSoftware,
                self.FileCreationDayofYear,
                self.FileCreationYear,
                self.HeaderSize,
                self.Offsettopointdata,
                self.NumberofVariableLengthRecords,
                self.PointDataRecordFormat,
                self.PointDataRecordLength,

                self.LegacyNumberofpointrecords,
                self.LegacyNumberofpointsbyreturn1,
                self.LegacyNumberofpointsbyreturn2,
                self.LegacyNumberofpointsbyreturn3,
                self.LegacyNumberofpointsbyreturn4,
                self.LegacyNumberofpointsbyreturn5,
                self.Xscalefactor,
                self.Yscalefactor,
                self.Zscalefactor,

                self.Xoffset,
                self.Yoffset,
                self.Zoffset,
                self.MaxX,
                self.MinX,
                self.MaxY,
                self.MinY,
                self.MaxZ,
                self.MinZ,

                self.StartofWaveformDataPacketRecord,
                self.StartoffirstExtendedVariableLengthRecord,
                self.NumberofExtendedVariableLengthRecords,
                self.Numberofpointrecords,
                self.Numberofpointsbyreturn1,  
                self.Numberofpointsbyreturn2,  
                self.Numberofpointsbyreturn3,  
                self.Numberofpointsbyreturn4,  
                self.Numberofpointsbyreturn5,  

                self.Numberofpointsbyreturn6,  
                self.Numberofpointsbyreturn7,  
                self.Numberofpointsbyreturn8,  
                self.Numberofpointsbyreturn9,  
                self.Numberofpointsbyreturn10,  
                self.Numberofpointsbyreturn11,  
                self.Numberofpointsbyreturn12,  
                self.Numberofpointsbyreturn13,  
                self.Numberofpointsbyreturn14,  
                self.Numberofpointsbyreturn15,  
                )

    def decodehdr(self, data):
        '''
        decode a header from a bytearray
        '''
        s = struct.unpack(self.hdrfmt, data)

        self.FileSignature =                        s[0]
        self.FileSourceID =                         s[1]
        self.GlobalEncoding =                      s[2]
        self.ProjectIDGUIDdata1 =                  s[3]
        self.ProjectIDGUIDdata2 =                  s[4]
        self.ProjectIDGUIDdata3 =                  s[5]
        self.ProjectIDGUIDdata4 =                  s[6]
        self.VersionMajor =                        s[7]
        self.VersionMinor =                        s[8]

        self.SystemIdentifier =                    s[9]
        self.GeneratingSoftware =                  s[10]
        self.FileCreationDayofYear =               s[11]
        self.FileCreationYear =                    s[12]
        self.HeaderSize =                          s[13]
        self.Offsettopointdata =                   s[14]
        self.NumberofVariableLengthRecords =       s[15]
        self.PointDataRecordFormat =               s[16]
        self.PointDataRecordLength =               s[17]

        self.LegacyNumberofpointrecords =          s[18]
        self.LegacyNumberofpointsbyreturn1 =       s[19]
        self.LegacyNumberofpointsbyreturn2 =       s[20]
        self.LegacyNumberofpointsbyreturn3 =       s[21]
        self.LegacyNumberofpointsbyreturn4 =       s[22]
        self.LegacyNumberofpointsbyreturn5 =       s[23]
        self.Xscalefactor =                        s[24]
        self.Yscalefactor =                        s[25]
        self.Zscalefactor =                        s[26]
        self.Xoffset =                             s[27]

        self.Yoffset =                             s[28]
        self.Zoffset =                             s[29]
        self.MaxX =                                s[30]
        self.MinX =                                s[31]
        self.MaxY =                                s[32]
        self.MinY =                                s[33]
        self.MaxZ =                                s[34]
        self.MinZ =                                s[35]

        self.StartofWaveformDataPacketRecord =     s[36]
        self.StartoffirstExtendedVariableLengthRecord =    s[37]
        self.NumberofExtendedVariableLengthRecords =       s[38]
        self.Numberofpointrecords =                        s[39]
        self.Numberofpointsbyreturn1 =                     s[40]
        self.Numberofpointsbyreturn2 =                     s[41]
        self.Numberofpointsbyreturn3 =                     s[42]
        self.Numberofpointsbyreturn4 =                     s[43]
        self.Numberofpointsbyreturn5 =                     s[44]

        self.Numberofpointsbyreturn6 =                     s[45]
        self.Numberofpointsbyreturn7 =                     s[46]
        self.Numberofpointsbyreturn8 =                     s[47]
        self.Numberofpointsbyreturn9 =                     s[48]
        self.Numberofpointsbyreturn10 =                    s[49]
        self.Numberofpointsbyreturn11 =                    s[50]
        self.Numberofpointsbyreturn12 =                    s[51]
        self.Numberofpointsbyreturn13 =                    s[52]
        self.Numberofpointsbyreturn14 =                    s[53]
        self.Numberofpointsbyreturn15 =                    s[54]

    def get_PointDataRecordFormat(self):
        return self._PointDataRecordFormat

    def set_PointDataRecordFormat(self, value):
        self._PointDataRecordFormat = value
        formats = self.getsupportedformats()
        self.PointDataRecordLength = formats[value][1]

    PointDataRecordFormat = property(get_PointDataRecordFormat,set_PointDataRecordFormat)

###############################################################################
class lasreader:
    def __init__(self, filename):
        if not os.path.isfile(filename):
            print ("file not found:", filename)
        self.fileName = filename
        self.fileptr = open(filename, 'rb')        
        self.fileSize = os.path.getsize(filename)
        self.hdr = lashdr()
        self.supportedformats = self.hdr.getsupportedformats()

        # the lists of all the data we will populate, then write into whatever format the user desires.  
        # these could be numpy arrays, but that introduces a dependency, so we will leave them as lists
        self.x = []
        self.y = []
        self.z = []
        self.intensity = []
        self.returnnumber = []
        self.numberreturns = []
        self.scandirectionflag = []
        self.edgeflightline = []
        self.classification = []
        self.scananglerank = []
        self.userdata = []
        self.pointsourceid = []
        self.gpstime = []
        self.red = []
        self.green = []
        self.blue = []
        self.wavepacketdescriptorindex = []
        self.byteoffsettowaveformdata = []
        self.waveformpacketsize = []
        self.returnpointwaveformlocation = []
        self.wavex = []
        self.wavey = []
        self.wavez = []
        self.nir = []

        self.classificationflags = []
        self.scannerchannel = []
        self.userdata = []
        self.scanangle = []

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

    def seekPointRecordStart(self):
        '''
        set the file pointer to the START of the points block so we can write some records
        '''
        self.fileptr.seek(self.hdr.Offsettopointdata, 0)                

    def seekPointRecordEnd(self):
        '''
        set the file pointer to the END of the points block so we can add new records
        '''
        self.fileptr.seek(self.hdr.Offsettopointdata + (self.hdr.Numberofpointrecords*self.hdr.PointDataRecordLength), 0)

    def __str__(self):
        '''
        pretty print this class
        '''
        return pprint.pformat(vars(self))

    def readhdr(self):
        '''
        read the las file header from disc
        '''
        data = self.fileptr.read(self.hdr.hdrlen)
        self.hdr.decodehdr(data)

    def unpackpoints(self, records):
        '''
        the points read into the list need unpacking into the real world useful data
        '''
        for r in records:
            self.x.append((r[0] * self.hdr.Xscalefactor) + self.hdr.Xoffset)
            self.y.append((r[1] * self.hdr.Yscalefactor) + self.hdr.Yoffset)
            self.z.append((r[2] * self.hdr.Zscalefactor) + self.hdr.Zoffset)

    def readpointrecords(self, recordsToRead=1):
        '''
        read the required number of records from the file
        '''
        data = self.fileptr.read(self.supportedformats[self.hdr.PointDataRecordFormat][1] * recordsToRead)
        result = []
        i = 0
        for r in range(recordsToRead):
            j = i + self.supportedformats[self.hdr.PointDataRecordFormat][1]
            result.append(struct.unpack(self.supportedformats[self.hdr.PointDataRecordFormat][0], data[i:j]))
            i = j
        
        return result

    def readvariablelengthrecord(self):
        '''
        read a variable length record from the file
        '''
        vlrhdrfmt = "<H16sHH32s"
        vlrhdrlen = struct.calcsize(vlrhdrfmt)
        data = self.fileptr.read(vlrhdrlen)
        s = struct.unpack(vlrhdrfmt, data)

        self.vlrReserved                   = s[0]
        self.vlrUserid                     = s[1]
        self.vlrrecordid                   = s[2]
        self.vlrRecordLengthAfterHeader    = s[3]
        self.vlrDescription                = s[4]

        # now read the variable data
        self.vlrdata = self.fileptr.read(self.vlrRecordLengthAfterHeader)
        print (self.vlrdata)


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


def testreader():
    '''
    sample read script so we can see how to use the code
    '''
    start_time = time.time() # time the process so we can keep it quick

    filename = "C:/development/python/sample.las"
    # filename = "C:/development/python/version1.4_format0.las"
    # create a lasreader class and pass the filename
    r = lasreader(filename)
    # r.read the header
    r.readhdr()

    # print some metadata about the reader
    print (r.hdr)

    # read the variable records
    for i in range(r.hdr.NumberofVariableLengthRecords):
        r.readvariablelengthrecord()

    # now find the start point for the point records
    r.seekPointRecordStart()
    # read the point data
    points = r.readpointrecords(64)
    # points = r.readpointrecords(r.hdr.Numberofpointrecords)
    
    # unpack from the native formmat into lists so we can do something with them
    r.unpackpoints(points)

    # for i in range(len(r.x)):
    #     print ("%.3f, %.3f %.3f" % (r.x[i], r.y[i], r.z[i]))
        
    # for p in points:
    #     print ("%.3f, %.3f %.3f" % ((p[0] * r.hdr.Xscalefactor) + r.hdr.Xoffset, (p[1] * r.hdr.Yscalefactor) + r.hdr.Yoffset, (p[2] * r.hdr.Zscalefactor) + r.hdr.Zoffset))

    print("Duration %.3fs" % (time.time() - start_time )) # time the process

    return

def isBitSet(int_type, offset):
    '''testBit() returns a nonzero result, 2**offset, if the bit at 'offset' is one.'''
    mask = 1 << offset
    return (int_type & (1 << offset)) != 0


###############################################################################
if __name__ == "__main__":
        main()

















