import pytest
import pygsf
import os

def test_backscatteradjustment():
	'''
	a simple unit test to validate the backscatter adjustment algorithm works.
	'''
	f = open("tmp.tmp", 'a')
	ping = pygsf.SWATH_BATHYMETRY_PING(f, 0, 0, 0)

	S1_angle 			= -58.0			# degrees
	S1_twtt 			= 0.20588		# seconds
	S1_range 			= 164.8			# metres
	H0_TxPower 			= 197.0			# dB
	H0_SoundSpeed 		= 1468.59		# metres/second
	H0_RxAbsorption		= 80.0			# dB/Km
	H0_TxBeamWidthVert 	= 0.0174533		# radians
	H0_TxBeamWidthHoriz = 0.0087266		# radians
	H0_TxPulseWidth 	= 0.000275		# seconds
	H0_RxSpreading 		= 35.0			# dB
	H0_RxGain 			= 8.0 * 2.0		# dB (multiply by 2 for r2sonic)
	H0_VTX_Offset 		= -21.0 / 100.0 # ask Norm
	S1_uPa 				= 470			# raw backscatter value

	corrected = ping.backscatteradjustment( S1_angle, S1_twtt, S1_range, S1_uPa, H0_TxPower, H0_SoundSpeed, H0_RxAbsorption, H0_TxBeamWidthVert, H0_TxBeamWidthHoriz, H0_TxPulseWidth, H0_RxSpreading, H0_RxGain, H0_VTX_Offset)
	print (corrected)
	requiredresult = -38.6
	assert corrected == requiredresult

if __name__ == "__main__":
	test_backscatteradjustment()


 
