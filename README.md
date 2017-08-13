# pygsf
python module for access of GSF Files (Generic Sensor Format)

This is going to use the standard libraries from python, ie NOT use numpy, gsglib, or external any dependencies.

# 2DO
* implement apply conditioning of backscatter
* make a las file for each frequency where intensity is the amplitude data
* make a las file of RGB where each color is an intensity

# DONE
* implemented options for snippet processing mean, max, dected and mean5db
* fixed bug in backscatter algorithm if range was 0m.  this is an invalid beam so return 0 for backscatter
* make conditioning ARC code work on all frequncies simultaneously
* snippets is now available in 2 forms: detect value or mean of all samples in beam.
* fixed bug in conditioner where extraction routine was using intensity array instead of mean_rel_array
* iterate and see how often settings change.  We can do this by writing settings changes to shp or csv file.
* need to make Angular Response Curves for each frequency
* implemented R2Sonic backscatter adjustment as provided in F77 from Norm Campbell at CSIRO.
* added option to specify output.  very useful when extracting backscatter ARC's
* conditioner now has dedicated function per functionality
* write out to a shape file so we can see where each file exists
* waterfall image creation done for each frequency
* sample read code in place
* conditioner in place which strips attitude records.  We can easily use this to strip by frequency
* can read a bathy record of type r2sonic 2024.  this what we need for multispectral challenge
* implement exclude, so we can strip out the attitide records.  This will speed up development
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


Processing C:\development\python\sample.gsf
Summary report:
GSF_RECORD_HEADER: GSF Version = GSF-v03.07

Total of 3969723 records:
GSF_RECORD_HEADER: 1
GSF_RECORD_SWATH_BATHYMETRY_PING: 2721
GSF_RECORD_SOUND_VELOCITY_PROFILE: 1
GSF_RECORD_PROCESSING_PARAMETERS: 1
GSF_RECORD_SENSOR_PARAMETERS: 0
GSF_RECORD_COMMENT: 0
GSF_RECORD_HISTORY: 0
GSF_RECORD_NAVIGATION_ERROR: 0
GSF_RECORD_SWATH_BATHY_SUMMARY: 0
GSF_RECORD_SINGLE_BEAM_PING: 0
GSF_RECORD_HV_NAVIGATION_ERROR: 0
GSF_RECORD_ATTITUDE: 3966999 (3966999 measurements)

Finished - 1 files processed.

3967003 MB Ping: Flag: 0x0000 
                   2016/334 21:48:14.677
          lat:   48.6526712  long: -123.4764805
          heading: 042.04 course: 000.00 speed: 00.00
          sensor: 152 beams: 256 center: 127 r: -00.40 p: +00.33 h: +00.00
          tide: -3.030  gps_tide: +0.000  depth corrector: -3.030  GPS Height: +9999.99
          ping is: Port

	Imagery data specifics: 
	  bits_per_sample:     16
	  applied_corrections: 0x00000000
	This record contains:
		depth
		across_track
		along_track
		travel_time
		beam_angle
		mr_amplitude
		quality_factor
		beam_flags
		beam_angle_forward
		vertical_error
		horizontal_error
		brb_inten

   Beam   Depth   XTrack  ATrack   TTime  Angle  FAngle Rel Amp  V_Err  H_Err Flag I/S Q_Factors
    001   65.98  -116.95   +0.03  0.1817  60.12    0.00   339.0  0.100  0.070 0x09 Y N       0.0
    002   65.87  -115.77   +0.05  0.1803  59.92    0.00   355.0  0.100  0.070 0x09 Y N       0.0
    003   65.88  -114.78   +0.06  0.1791  59.71    0.00   363.0  0.100  0.070 0x09 Y N       0.0
    004   65.88  -113.80   +0.07  0.1780  59.50    0.00   372.0  0.100  0.070 0x09 Y N       0.0
    005   65.86  -112.78   +0.08  0.1768  59.28    0.00   380.0  0.100  0.070 0x09 Y N       0.0
    006   65.86  -111.79   +0.09  0.1756  59.06    0.00   388.0  0.100  0.070 0x09 Y N       0.0


DEPTH_ARRAY 1
ACROSS_TRACK_ARRAY 2
ALONG_TRACK_ARRAY 3
TRAVEL_TIME_ARRAY 4
BEAM_ANGLE_ARRAY 5
MEAN_CAL_AMPLITUDE_ARRAY 6
MEAN_REL_AMPLITUDE_ARRAY 7
ECHO_WIDTH_ARRAY 8
QUALITY_FACTOR_ARRAY 9
RECEIVE_HEAVE_ARRAY 10
DEPTH_ERROR_ARRAY (obsolete) 11
ACROSS_TRACK_ERROR_ARRAY (obsolete) 12
ALONG_TRACK_ERROR_ARRAY (obsolete) 13
NOMINAL_DEPTH_ARRAY 14
QUALITY_FLAGS_ARRAY 15
BEAM_FLAGS_ARRAY 16
SIGNAL_TO_NOISE_ARRAY 17
BEAM_ANGLE_FORWARD_ARRAY 18
VERTICAL_ERROR_ARRAY 19
HORIZONTAL_ERROR_ARRAY 20
INTENSITY_SERIES_ARRAY 21
SECTOR_NUMBER_ARRAY 22
DETECTION_INFO_ARRAY 23
INCIDENT_BEAM_ADJ_ARRAY 24
SYSTEM_CLEANING_ARRAY 25
DOPPLER_CORRECTION_ARRAY 26
SONAR_VERT_UNCERTAINTY_ARRAY 27
SCALE_FACTORS 100
SEABEAM_SPECIFIC 102
EM12_SPECIFIC 103
EM100_SPECIFIC 104
EM950_SPECIFIC 105
EM121A_SPECIFIC 106
EM121_SPECIFIC 107
SASS_SPECIFIC (To Be Replaced By CMP_SASS) 108
SEAMAP_SPECIFIC 109
SEABAT_SPECIFIC 110
EM1000_SPECIFIC 111
TYPEIII_SEABEAM_SPECIFIC (To Be Replaced By CMP_SASS ) 112
SB_AMP_SPECIFIC 113
SEABAT_II_SPECIFIC 114
SEABAT_8101_SPECIFIC (obsolete) 115
SEABEAM_2112_SPECIFIC 116
ELAC_MKII_SPECIFIC 117
EM3000_SPECIFIC 118
EM1002_SPECIFIC 119
EM300_SPECIFIC 120
CMP_SASS_SPECIFIC (To replace SASS and TYPEIII_SEABEAM) 121
RESON_8101_SPECIFIC 122
RESON_8111_SPECIFIC 123
RESON_8124_SPECIFIC 124
RESON_8125_SPECIFIC 125
RESON_8150_SPECIFIC 126
RESON_8160_SPECIFIC 127
EM120_SPECIFIC 128
EM3002_SPECIFIC 129
EM3000D_SPECIFIC 130
EM3002D_SPECIFIC 131
EM121A_SIS_SPECIFIC 132
EM710_SPECIFIC 133
EM302_SPECIFIC 134
EM122_SPECIFIC 135
GEOSWATH_PLUS_SPECIFIC 136
KLEIN_5410_BSS_SPECIFIC 137
RESON_7125_SPECIFIC 138
EM2000_SPECIFIC 139
EM300_RAW_SPECIFIC 140
EM1002_RAW_SPECIFIC 141
EM2000_RAW_SPECIFIC 142
EM3000_RAW_SPECIFIC 143
EM120_RAW_SPECIFIC 144
EM3002_RAW_SPECIFIC 145
EM3000D_RAW_SPECIFIC 146
EM3002D_RAW_SPECIFIC 147
EM121A_SIS_RAW_SPECIFIC 148
EM2040_SPECIFIC 149
DELTA_T_SPECIFIC 150
R2SONIC_2022_SPECIFIC 151
R2SONIC_2024_SPECIFIC 152
R2SONIC_2020_SPECIFIC 153
SB_ECHOTRAC_SPECIFIC (obsolete) 206
SB_BATHY2000_SPECIFIC (obsolete) 207
SB_MGD77_SPECIFIC (obsolete) 208
SB_BDB_SPECIFIC (obsolete) 209
SB_NOSHDB_SPECIFIC (obsolete) 210
SB_PDD_SPECIFIC (obsolete) 211
SB_NAVISOUND_SPECIFIC (obsolete) 212