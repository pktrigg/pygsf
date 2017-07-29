# pygsf
python module for access of GSF Files (Generic Sensor Format)

This is going to use the standard libraries from python, ie NOT use numpy, gsglib, or external any dependencies.

# 2DO
* implement the extract, so we can strip out the attitide records.  This will speed up development
* processing record
* attitude record
* sound velocity record

# DONE
* can read the GSF header record with the version string
* basic loop in place

# Record Decriptions (See page 82)
HEADER 									1
SWATH_BATHYMETRY_PING 					2
SOUND_VELOCITY_PROFILE 					3
PROCESSING_PARAMETERS 					4
SENSOR_PARAMETERS 						5
COMMENT 								6
HISTORY 								7
NAVIGATION_ERROR (obsolete) 			8
SWATH_BATHY_SUMMARY 					9
SINGLE_BEAM_SOUNDING (use discouraged)	10
HV_NAVIGATION_ERROR 					11
ATTITUDE 								12
  
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