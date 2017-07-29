# pygsf
python module for access of GSF Files (Generic Sensor Format)

This is going to use the standard libraries from python, ie NOT use numpy, gsglib, or external any dependencies.

# 2DO
* everything

# DONE
* nothing

## Public Header Block
```
FileSignature (“LASF”) char[4] 4 bytes                          4s
FileSourceID unsigned short 2 bytes                             H
GlobalEncoding unsigned short 2 bytes                           H
ProjectIDGUIDdata1 unsigned long 4 bytes                        L
ProjectIDGUIDdata2 unsigned short 2 byte                        H
ProjectIDGUIDdata3 unsigned short 2 byte                        H
ProjectIDGUIDdata4 unsigned char[8] 8 bytes                     8B
VersionMajor unsigned char 1 byte *                             B
VersionMinor unsigned char 1 byte *                             B
SystemIdentifier char[32] 32 bytes *                            32c
GeneratingSoftware char[32] 32 bytes *                          32c
FileCreationDayofYear unsigned short 2 bytes *                  32c
FileCreationYear unsigned short 2 bytes *                       H
HeaderSize unsigned short 2 bytes *                             H
Offsettopointdata unsigned long 4 bytes *                       L
NumberofVariableLengthRecords unsigned long 4 bytes *           L
PointDataRecordFormat unsigned char 1 byte *                    B
PointDataRecordLength unsigned short 2 bytes *                  H
LegacyNumberofpointrecords unsigned long 4 bytes *              L
LegacyNumberofpoints by return unsigned long [5] 20 bytes *     5L
Xscalefactor double 8 bytes *                                   d 
Yscalefactor double 8 bytes *                                   d 
Zscalefactor double 8 bytes *                                   d  
Xoffset double 8 bytes *                                        d
Yoffset double 8 bytes *                                        d
Zoffset double 8 bytes *                                        d
MaxX double 8 bytes *                                           d
MinX double 8 bytes *                                           d
MaxY double 8 bytes *                                           d
MinY double 8 bytes *                                           d
MaxZ double 8 bytes *                                           d
MinZ double 8 bytes *                                           d
StartofWaveformDataPacketRecord Unsigned long long 8 bytes *    Q
StartoffirstExtendedVariableLengthRecord unsigned long long 8 bytes *   Q
NumberofExtendedVariableLengthRecords unsigned long 4 bytes *           L
Numberofpointrecords unsigned long long 8 bytes *                       Q
Numberofpointsbyreturn unsigned long long [15] 120 bytes                15Q
```
  
## Python Struct format characters
```
Format	C Type	            Python type	            Standard size	    
x	    pad byte	        no value	 	 
c	    char	            string of length 1	    1	 
b	    signed char	        integer	                1	
B	    unsigned char	    integer	                1	
?	    _Bool	            bool	                1	
h	    short	            integer	                2
H	    unsigned short	    integer	                2	
i	    int	                integer	                4	
I	    unsigned int	    integer	                4	
l	    long	            integer	                4	
L	    unsigned long	    integer	                4	
q	    long long	        integer 	            8
Q	    unsigned long long	integer	                8
f	    float	            float               	4
d	    double	            float               	8
s	    char[]	            string	 	 
p	    char[]	            string	 	 
P	    void *	            integer	 	